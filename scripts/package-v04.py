#!/usr/bin/env python3
"""Create reviewable source + guarded incremental update from a known Git baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

BASE='08b804c71eadd9e324cf04581572e19d609f0f89'
ROOT=Path(__file__).resolve().parents[1]

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def package(output, worktree=False):
    revision=git('rev-parse','HEAD').decode().strip()
    changed=(git('diff','--name-only',BASE) if worktree else git('diff','--name-only',BASE,'HEAD')).decode().splitlines()
    with tempfile.TemporaryDirectory(prefix='veyra-v04-package-') as td:
        release=Path(td)/'Veyra_AI_V0.4';update=release/'update';source=release/'source'
        entries=[]
        for name in changed:
            path=ROOT/name
            if not path.is_file():raise ValueError('Deletions require a deliberate installer migration: '+name)
            data=path.read_bytes();new=update/'updated'/name;new.parent.mkdir(parents=True,exist_ok=True);new.write_bytes(data)
            before=subprocess.run(['git','show',BASE+':'+name],cwd=ROOT,capture_output=True)
            if before.returncode==0:
                p=update/'baseline'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(before.stdout)
            entries.append({'path':name,'sha256':hashlib.sha256(data).hexdigest(),'mode':path.stat().st_mode&0o777})
        (update/'update-manifest.json').write_text(json.dumps({'version':'0.4.0','baseline':BASE,'revision':revision,'files':entries},indent=2)+'\n')
        shutil.copy2(ROOT/'scripts/apply_update.py',update/'apply_update.py')
        paths=git('ls-files').decode().splitlines()
        for name in paths:
            if name.endswith(('.zip','.png','.jpg','.jpeg')) or name.startswith(('artifacts/','docs/review/')):continue
            p=ROOT/name
            if not p.is_file():continue
            dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        (source/'BUILD_REVISION').write_text(revision+'\n')
        for name in ['README.md','V04_UPDATE.md','TEST_REPORT_V04.md']:
            shutil.copy2(ROOT/name,release/name)
        if not worktree:
            subprocess.run(['git','bundle','create',str(release/'Veyra_AI_V0.4.bundle'),BASE+'..feature/v0.4-code-studio'],cwd=ROOT,check=True,capture_output=True)
            subprocess.run(['git','bundle','verify',str(release/'Veyra_AI_V0.4.bundle')],cwd=ROOT,check=True,capture_output=True)
        (release/'RELEASE.json').write_text(json.dumps({'application':'VEYRA AI','version':'0.4.0','branch':'feature/v0.4-code-studio','commit':revision,'baseline':BASE},indent=2)+'\n')
        hashes={p.relative_to(release).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(release.rglob('*')) if p.is_file()}
        (release/'SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n')
        # Actual application to the exact baseline, idempotence and local edit protection.
        check=Path(td)/'baseline-check';check.mkdir()
        archive=subprocess.Popen(['git','archive',BASE],cwd=ROOT,stdout=subprocess.PIPE)
        import tarfile
        with tarfile.open(fileobj=archive.stdout,mode='r|') as tar:tar.extractall(check,filter='data')
        assert archive.wait()==0
        extra=check/'user-notes.txt';extra.write_text('keep me')
        env=check/'.env';env.write_text('PRIVATE_TEST_SECRET=keep-me\n')
        for action in ['--check','--apply','--check']:
            run=subprocess.run(['python3',str(update/'apply_update.py'),'--repo',str(check),action],capture_output=True,text=True)
            if run.returncode:raise ValueError(run.stdout+run.stderr)
        assert extra.read_text()=='keep me' and env.read_text()=='PRIVATE_TEST_SECRET=keep-me\n'
        for entry in entries:assert hashlib.sha256((check/entry['path']).read_bytes()).hexdigest()==entry['sha256']
        probe=check/'frontend/src/App.jsx';probe.write_text('USER CHANGED THIS FILE\n')
        run=subprocess.run(['python3',str(update/'apply_update.py'),'--repo',str(check),'--check'],capture_output=True,text=True)
        assert run.returncode==2 and probe.read_text()=='USER CHANGED THIS FILE\n'
        output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted(release.rglob('*')):
                if p.is_file():z.write(p,p.relative_to(release.parent))
        print(json.dumps({'path':str(output),'size':output.stat().st_size,'version':'0.4.0','commit':revision,'changedFiles':len(entries),'installer':'baseline application, idempotence, local secret preservation and conflict refusal passed'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--worktree',action='store_true');args=p.parse_args();package(args.output,args.worktree)
