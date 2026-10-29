"""Single-operator entitlements and durable daily accounting. No billing/auth claims."""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time
from ..browser_manager import SessionError
from ..prompts.provider import ProviderFailure
from .provider import CodeProvider
from .local import reconstruct
from .preview import compile_project,document
from .schemas import Project

def number(name,default):
    try:return max(0,min(10000,int(os.getenv(name,str(default)))))
    except ValueError:return default

class StudioService:
    def __init__(self,db=None,provider=None,refiner=None):
        self.provider=provider or CodeProvider('code');self.refiner=refiner or CodeProvider('refine')
        self.plan='premium' if os.getenv('VEYRA_OPERATOR_PLAN')=='premium' else 'free'
        # Trusted deployment configuration only. A client cannot choose its entitlement.
        self.generation_limit=number('VEYRA_'+self.plan.upper()+'_GENERATIONS_PER_DAY',4 if self.plan=='free' else 50)
        self.refine_limit=number('VEYRA_'+self.plan.upper()+'_REFINEMENTS_PER_DAY',2 if self.plan=='free' else 50)
        self.preview_limit=number('VEYRA_'+self.plan.upper()+'_PREVIEWS_PER_DAY',4 if self.plan=='free' else 100)
        db=db or os.getenv('VEYRA_USAGE_DB','.veyra-runtime/studio.sqlite3')
        if db!=':memory:':Path(db).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(db,check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS usage(day TEXT, task TEXT, count INTEGER, PRIMARY KEY(day,task))');self.db.commit()
        self.lock=asyncio.Lock();self.records={};self.previews={}

    def config(self):
        return {'plan':self.plan,'scope':'single-operator deployment; not multi-user billing','generationLimit':self.generation_limit,'refinementLimit':self.refine_limit,'previewLimit':self.preview_limit,'localRendersMetered':False,
                'codeAIAvailable':self.provider.config.available,'refineAIAvailable':self.refiner.config.available,'multiElement':False,'maxContextNodes':55 if self.plan=='premium' else 24}

    def charge(self,task,limit):
        day=datetime.now(timezone.utc).date().isoformat()
        with self.db:
            self.db.execute('DELETE FROM usage WHERE day < ?', (day,))
            self.db.execute('INSERT OR IGNORE INTO usage VALUES(?,?,0)',(day,task))
            updated=self.db.execute('UPDATE usage SET count=count+1 WHERE day=? AND task=? AND count < ?',(day,task,limit))
            if updated.rowcount!=1:raise SessionError('Daily '+task+' allowance reached. Local editing and rendering remain available.',429,'studio-quota')

    @asynccontextmanager
    async def admission(self):
        if self.lock.locked():raise SessionError('A generation operation is running. Please wait.',429,'studio-busy')
        async with self.lock:yield

    def prune(self):
        now=time.monotonic()
        self.records={k:v for k,v in self.records.items() if now-v['created']<3600}
        self.previews={k:v for k,v in self.previews.items() if now-v[0]<600}
        while len(self.records)>=12:self.records.pop(next(iter(self.records)))
        while len(self.previews)>=16:self.previews.pop(next(iter(self.previews)))

    async def generate(self,evidence,request):
        if request.mode=='auto' and (not request.consent or not self.provider.config.available):
            raise SessionError('AI requires a configured provider and explicit permission to send the selected evidence.',503 if request.consent else 422,'studio-ai-unavailable')
        self.charge('generation',self.generation_limit)
        # Existing collector redaction and ancestor admission stay authoritative.
        from ..prompts.selection import selection_plan
        context=dict(evidence)
        context['nodes'],sample=selection_plan(evidence['nodes'],55 if self.plan=='premium' else 24)
        context['truncated']=evidence.get('truncated',False) or sample['omitted']>0
        project,warnings=reconstruct(context,request.format);usage={};summary='Measured local reconstruction';mode='local'
        if request.mode=='auto':
            try:
                answer,usage=await self.provider.generate({'task':'generation','untrustedEvidence':context,'project':project.model_dump()})
                project=Project(format=project.format,files={**project.files,**answer['files']});summary=answer['summary'][:500];mode='ai'
                warnings=[w for w in warnings if not w.startswith('Local measured')]
                project.files['README.md']=project.files.get('README.md','').replace('- Local measured reconstruction; no AI model was called.','- AI-assisted recreation. Review all generated code before running or publishing.')
            except ProviderFailure as exc:raise SessionError('AI code generation failed ('+exc.reason+'). No retry was made; existing code is preserved.',502,'studio-provider-failed') from None
            except ValueError:raise SessionError('AI returned an invalid project. Existing code is preserved.',422,'code-invalid') from None
        await compile_project(project)
        self.prune();ident=secrets.token_hex(16)
        self.records[ident]={'created':time.monotonic(),'evidence':context,'format':project.format}
        return {'generationId':ident,'project':project.model_dump(),'mode':mode,'summary':summary,'warnings':warnings,'usage':usage,'model':self.provider.config.model if mode=='ai' else None,'modifiedFiles':list(project.files),'diagnostics':{'includedNodes':len(context['nodes']),'omittedNodes':sample['omitted'],'pixelComparison':'not performed','assets':'URLs omitted; placeholders used','expected':[{ 'id':n['id'],'width':n.get('box',{}).get('width'),'height':n.get('box',{}).get('height'),'fontSize':n.get('styles',{}).get('font-size'),'color':n.get('styles',{}).get('color')} for n in context['nodes']]}}

    async def refine(self,request):
        self.prune();record=self.records.get(request.generationId)
        if not record or request.project.format!=record['format']:raise SessionError('Generation context expired or changed format. Generate from the current selection again; your code is kept.',409,'studio-context-expired')
        if not request.consent or not self.refiner.config.available:raise SessionError('Refinement requires a configured AI provider and permission to send current code and selected evidence. No files changed.',503,'studio-ai-unavailable')
        self.charge('refinement',self.refine_limit)
        try:
            answer,usage=await self.refiner.generate({'task':'refinement','instruction':request.instruction,'project':request.project.model_dump(),'untrustedEvidence':record['evidence']})
            if set(answer['files']) & {'package.json','vite.config.js','README.md'}:raise ValueError()
            project=Project(format=request.project.format,files={**request.project.files,**answer['files']})
        except ProviderFailure as exc:raise SessionError('AI refinement failed ('+exc.reason+'). No files changed.',502,'studio-provider-failed') from None
        except ValueError:raise SessionError('AI returned invalid files. No files changed.',422,'code-invalid') from None
        await compile_project(project)
        modified=[k for k,v in project.files.items() if request.project.files.get(k)!=v]
        if not modified:raise SessionError('The AI returned no changes. Your code is preserved.',422,'studio-no-changes')
        return {'project':project.model_dump(),'generationId':request.generationId,'modifiedFiles':modified,'summary':answer['summary'][:500],'mode':'ai','model':self.refiner.config.model,'usage':usage,'warnings':[]}

    async def preview(self,project):
        js=await compile_project(project);doc,csp=document(project,js)
        self.prune();ident=secrets.token_hex(24);self.previews[ident]=(time.monotonic(),doc,csp)
        return {'url':'/api/studio/render/'+ident,'expiresInSeconds':600,'metered':False}
