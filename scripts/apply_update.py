#!/usr/bin/env python3
"""Guarded application of a packaged incremental update; never deletes a project.

The distribution places this script beside update-manifest.json, baseline/ and
updated/. Check all merges before writing anything; back up every replaced file.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys


def safe_target(root,name):
    rel=Path(name)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:raise ValueError('Unsafe update path')
    target=root/rel
    for parent in [target,*target.parents]:
        if parent==root.parent:break
        if parent.is_symlink():raise ValueError('Refusing a symlink in update target: '+name)
    return target


def plan_update(bundle,root):
    manifest=json.loads((bundle/'update-manifest.json').read_text())
    planned=[];conflicts=[]
    for entry in manifest['files']:
        name=entry['path'];target=safe_target(root,name)
        newer=safe_target(bundle/'updated',name).read_bytes()
        if hashlib.sha256(newer).hexdigest()!=entry['sha256']:raise ValueError('Payload checksum mismatch: '+name)
        current=target.read_bytes() if target.exists() else None
        basepath=safe_target(bundle/'baseline',name)
        baseline=basepath.read_bytes() if basepath.exists() else None
        if current==newer:continue
        if current is None and baseline is not None:
            conflicts.append(name+' (existing baseline file is missing)');continue
        if current==baseline:merged=newer
        elif baseline is None:
            conflicts.append(name+' (new file already exists with different contents)');continue
        else:
            if not shutil.which('git'):
                conflicts.append(name+' (changed locally; Git is needed for a safe three-way merge)');continue
            with tempfile.TemporaryDirectory(prefix='veyra-merge-') as tmp:
                files=[Path(tmp)/n for n in ['current','baseline','updated']]
                for p,content in zip(files,[current,baseline,newer]):p.write_bytes(content)
                result=subprocess.run(['git','merge-file','--diff3','-p',*[str(p) for p in files]],capture_output=True)
                if result.returncode!=0:
                    conflicts.append(name+' (three-way merge requires review)');continue
                merged=result.stdout
        planned.append((name,target,merged,entry.get('mode',0o644),current))
    return planned,conflicts


def apply(bundle,root,write=False):
    if not (root/'backend/app/main.py').is_file() or not (root/'frontend/src/App.jsx').is_file():
        raise ValueError('Run from the existing Veyra repository root, or pass --repo PATH.')
    planned,conflicts=plan_update(bundle,root)
    if conflicts:
        print('No project files changed. Conflicts:\n'+'\n'.join('  '+name for name in conflicts))
        return 2
    print(f'{len(planned)} files can be updated safely; unrelated files are untouched.')
    if not write:return 0
    for name,target,content,mode,expected in planned:
        if (target.read_bytes() if target.exists() else None)!=expected:
            raise ValueError('File changed during update planning: '+name)
    backup_parent=root/'.v02-backups'
    if backup_parent.is_symlink():raise ValueError('Backup directory must not be a symlink.')
    backup_parent.mkdir(exist_ok=True)
    backup=Path(tempfile.mkdtemp(prefix='update-',dir=backup_parent))
    created=[];replaced=[]
    try:
        for name,target,content,mode,expected in planned:
            if target.exists():
                old=backup/name;old.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,old);replaced.append((target,old))
            else:created.append(target)
            target.parent.mkdir(parents=True,exist_ok=True)
            # Replace atomically in the same directory, preserving write rollback.
            fd,temporary=tempfile.mkstemp(prefix='.veyra-write-',dir=target.parent)
            with os.fdopen(fd,'wb') as stream:stream.write(content)
            os.chmod(temporary,mode & 0o777);os.replace(temporary,target)
    except BaseException:
        for target,old in replaced:shutil.copy2(old,target)
        for target in created:
            if target.exists():target.unlink()
        raise
    print('Update applied. Backups: '+str(backup))
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo',default='.')
    group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--check',action='store_true');group.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try:sys.exit(apply(Path(__file__).resolve().parent,Path(args.repo).resolve(),args.apply))
    except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(1)
