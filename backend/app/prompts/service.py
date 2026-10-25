import asyncio
from collections import deque
from contextlib import asynccontextmanager
import secrets
import time
from ..browser_manager import SessionError
from .deterministic import render_prompt
from .provider import CompatibleProvider, ProviderConfig, ProviderFailure
from .schemas import PromptResponse


class PromptService:
    def __init__(self, config=None, provider=None):
        self.config=config or ProviderConfig.from_env()
        self.provider=provider or CompatibleProvider(self.config)
        self.lock=asyncio.Lock();self.requests=deque(maxlen=12)

    @asynccontextmanager
    async def admission(self, session_id):
        now=time.monotonic()
        while self.requests and now-self.requests[0][0]>=60:self.requests.popleft()
        if self.lock.locked():raise SessionError('A prompt is already being generated. Please wait.',429,'prompt-busy')
        if len(self.requests)>=10 or sum(token==session_id for _,token in self.requests)>=3:
            raise SessionError('Prompt limit reached. Wait one minute before trying again.',429,'prompt-rate-limit')
        async with self.lock:
            self.requests.append((now,session_id));yield

    async def generate(self, evidence, request):
        ai=None;warning=None
        if request.mode=='auto':
            if not self.config.available:warning='AI is not configured or enabled. The local deterministic generator was used.'
            else:
                try:ai=await self.provider.generate(evidence,request)
                except ProviderFailure as exc:
                    messages={'timeout':'timed out','rate-limit':'was rate limited','configuration':'has invalid configuration'}
                    warning=f'AI {messages.get(exc.reason,"was unavailable or returned unusable output")}. The local deterministic generator was used; no automatic retry was made.'
        prompt,warnings=render_prompt(evidence,request,ai)
        if warning:warnings.append(warning)
        if len(prompt)>60000:raise SessionError('The evidence exceeded the prompt output budget. Choose Concise.',422,'prompt-output-limit')
        return PromptResponse(generationId=secrets.token_hex(12),prompt=prompt,mode='ai' if ai else 'fallback',
            provider=self.config.name if ai else None,model=self.config.model if ai else None,warnings=warnings,
            evidenceSummary={'scope':request.scope,'rootTag':evidence['nodes'][0]['tag'],'boundary':evidence['boundary'],
                             'nodeCount':len(evidence['nodes']),'viewport':evidence['viewport'],'truncated':evidence['truncated'],
                             'capturedAt':evidence['source']['capturedAt']})
