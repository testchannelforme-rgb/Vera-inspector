"""Cross-language collector -> sanitizer -> local prompt test (synthetic DOM).

This exercises the production JS assembly, not a real browser or pixel comparison.
Protected Chromium integration lives in test_visual_browser.py.
"""
import json
from pathlib import Path
import shutil
import subprocess
import pytest
from app.prompts.evidence import sanitize
from app.prompts.schemas import PromptRequest
from app.prompts.provider import ProviderConfig
from app.prompts.service import PromptService


async def test_real_collector_source_to_local_prompt_without_provider():
    node=shutil.which('node')
    if not node:pytest.skip('Node is required for cross-language synthetic collector check')
    root=Path(__file__).resolve().parents[2]
    script=r'''
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {el,environment} from './backend/tests/js/synthetic-dom.mjs';
const base='./backend/app/prompts/';
const source=readFileSync(base+'collect.js','utf8')
 .replace('__VEYRA_BOUNDARY_FUNCTION__','('+readFileSync(base+'boundary.js','utf8')+')')
 .replace('__VEYRA_VISUAL_FUNCTION__',readFileSync(base+'visual.js','utf8'));
const title=el('h1',{text:'Observed fixture title',styles:{'background-clip':'text','-webkit-text-fill-color':'rgba(0, 0, 0, 0)'}});
const owner=el('section',{styles:{'background-image':'linear-gradient(120deg, red 10%, blue 90%), url("https://example.com/?token=private")'}}).add(title);
owner.pseudos={'::before':{content:'""',position:'absolute','background-image':'conic-gradient(red, blue)',width:'100px',height:'60px'}};
console.log(JSON.stringify(vm.runInNewContext('('+source+')',environment({now:()=>0}))(title,'element')));
'''
    proc=subprocess.run([node,'--input-type=module','-e',script],cwd=root,capture_output=True,text=True,timeout=10)
    assert proc.returncode==0,proc.stderr
    raw=json.loads(proc.stdout)
    evidence=sanitize(raw,'https://example.com/')
    request=PromptRequest(sessionId='s'*32,frameId='f'*16,referenceId='r'*16,mode='local')
    result=await PromptService(ProviderConfig()).generate(evidence,request)
    assert result.mode=='fallback'
    assert 'linear-gradient(120deg, red 10%, blue 90%)' in result.prompt
    assert 'conic-gradient(red, blue)' in result.prompt
    assert 'ancestor:1' in result.prompt and '::before' in result.prompt
    assert 'Observed fixture title' in result.prompt
    assert '?token=private' not in json.dumps(evidence) and '?token=private' not in result.prompt
    assert evidence['nodes'][0]['styles']['-webkit-text-fill-color']=='rgba(0, 0, 0, 0)'
    assert 'no pixel' in result.prompt.lower()
