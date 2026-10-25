#!/usr/bin/env python3
"""Opt-in live public website -> current inspection -> prompt API acceptance probe."""
import argparse
import json
from pathlib import Path
import urllib.request

parser=argparse.ArgumentParser()
parser.add_argument('--ai',action='store_true',help='Make ONE real AI request using configured credentials; may consume provider quota')
args=parser.parse_args()
BASE='http://127.0.0.1:8000/api'


def api(path,body=None,method='POST'):
    req=urllib.request.Request(BASE+path,method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type':'application/json','X-Veyra-Client':'inspector-v0.1'})
    with urllib.request.urlopen(req,timeout=45) as response:return json.load(response)


def main():
    health=api('/health',method='GET')
    if health.get('networkMode')!='isolated-public' or health.get('status')!='ready':
        raise SystemExit('A ready isolated-public stack is required; no unrestricted local fallback is allowed.')
    if args.ai and not health.get('prompts',{}).get('aiAvailable'):
        raise SystemExit('AI is not configured/enabled. No live-provider success can be claimed.')
    token=None
    try:
        data=api('/sessions',{'url':'example.com','viewport':{'width':1280,'height':800}})
        token=data['sessionId'];frame=data['frame']
        data=api(f'/sessions/{token}/select',{'frameId':frame['frameId'],'x':640,'y':240})
        inspection=data['inspection'];assert inspection['styles'] and inspection['element']['referenceId']
        frame=data['frame'];folder=Path('artifacts/generated-v03');folder.mkdir(parents=True,exist_ok=True)
        for scope in ['element','section','page']:
            result=api('/prompts/generate',{'sessionId':token,'frameId':frame['frameId'],
                'referenceId':inspection['element']['referenceId'],'scope':scope,'target':'react','detail':'detailed',
                'mode':'auto' if args.ai and scope=='element' else 'local'})
            assert all(f'## {i}.' in result['prompt'] for i in range(1,9))
            assert result['evidenceSummary']['nodeCount']>0
            if args.ai and scope=='element':assert result['mode']=='ai','Provider returned fallback; live AI acceptance failed'
            (folder/f'example-com-{scope}.json').write_text(json.dumps(result,indent=2))
            print(scope+': '+result['mode']+' prompt, '+str(result['evidenceSummary']['nodeCount'])+' observed nodes')
        print('Live prompt API checks passed. Review output and UI before claiming visual/device compatibility.')
    finally:
        if token:api('/sessions/'+token,method='DELETE')


if __name__=='__main__':main()
