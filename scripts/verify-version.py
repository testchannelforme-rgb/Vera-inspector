#!/usr/bin/env python3
import json
import subprocess
import sys
import urllib.request
base=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8001'
try:
    with urllib.request.urlopen(base+'/api/health',timeout=5) as r:data=json.load(r)
    if data.get('version')!='0.4.0':raise ValueError('Wrong app version: '+str(data.get('version')))
    expected=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if data.get('commit')!=expected:raise ValueError('Stale server: '+str(data.get('commit'))+'; checked-out commit: '+expected)
    with urllib.request.urlopen(base+'/',timeout=5) as r:page=r.read()
    if b'/assets/' not in page:raise ValueError('Production frontend missing.')
    print('VEYRA AI',data['version'],'commit',data['commit'],'browser',data['status'],'on',base)
except Exception as exc:raise SystemExit('Version verification failed: '+str(exc))
