"""Live API acceptance. Refuses universal tests without isolated-public mode.

Run only against your private instance. No access-control bypass or login.
"""
import argparse
import base64
import json
from pathlib import Path
import sys
import time
import urllib.request
import urllib.error


def run(base_url,output):
    def call(path,body=None,method='POST'):
        request=urllib.request.Request(base_url+'/api'+path,data=json.dumps(body).encode() if body is not None else None,
            method=method,headers={'Content-Type':'application/json','X-Veyra-Client':'inspector-v0.1'})
        try:
            with urllib.request.urlopen(request,timeout=50) as r:return json.load(r)
        except urllib.error.HTTPError as exc:
            result=json.load(exc);raise RuntimeError(json.dumps(result)) from None
    health=call('/health',method='GET')
    if health['networkMode']!='isolated-public' or health['status']!='ready':
        raise RuntimeError('Run bash start.sh --isolated first. Public tests are not allowed against an unrestricted local browser.')
    output.mkdir(parents=True,exist_ok=True)
    results=[]
    for label,url in [('static','example.com'),('dynamic','react.dev'),('roblox','www.roblox.com')]:
        token=None
        try:
            normalized=call('/normalize',{'url':url})['url']
            response=call('/sessions',{'url':normalized,'viewport':{'width':1280,'height':800}})
            token=response['sessionId'];frame=response['frame'];diagnostics=frame['diagnostics']
            assert diagnostics['navigationState']=='loaded' and not diagnostics['readiness'].get('empty')
            assert not diagnostics['readiness'].get('accessChecks'),'Website presented an access check; compatibility not established.'
            image=base64.b64decode(frame['image'].split(',')[1]);assert image.startswith(b'\xff\xd8')
            selected=call('/sessions/'+token+'/select',{'frameId':frame['frameId'],'x':64,'y':150})
            inspection=selected['inspection'];assert inspection['schemaVersion']=='0.1' and inspection['styles']['display']
            assert inspection['geometry']['width']>0 and inspection['element']['tagName']
            (output/(label+'-website.jpg')).write_bytes(image)
            (output/(label+'-inspection.json')).write_text(json.dumps(inspection,indent=2))
            (output/(label+'-diagnostics.json')).write_text(json.dumps(diagnostics,indent=2))
            results.append({'site':url,'status':'rendered-and-inspected; review screenshot for completeness','tag':inspection['element']['tagName'],'httpStatus':diagnostics['httpStatus']})
        except Exception as exc:results.append({'site':url,'status':'failed','reason':str(exc)[:2000]})
        finally:
            if token:
                try:call('/sessions/'+token,method='DELETE')
                except Exception:pass
    (output/'public-results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))
    return 1 if any(r['status']=='failed' for r in results) else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',default='http://127.0.0.1:8000');parser.add_argument('--output',default='artifacts/generated-v02')
    args=parser.parse_args()
    try:sys.exit(run(args.base_url.rstrip('/'),Path(args.output)))
    except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(1)
