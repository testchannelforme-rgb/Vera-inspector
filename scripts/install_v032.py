#!/usr/bin/env python3
"""Conservative changed-file installer, packaged beside manifest/baseline/updated.

Never switches branches, stashes, resets, merges or discards local edits. Rollback
refuses to overwrite changes made after installation. Run the packaged copy.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BRANCH='feature/v0.3.2-visual-fidelity'
BACKUPS='.v032-backups'


def digest(data):return hashlib.sha256(data).hexdigest()


def safe_path(root,name):
    if not isinstance(name,str) or "\\" in name or "\x00" in name:raise ValueError('Unsafe package path')
    rel=Path(name)
    if any(part in ('.git','.env','.venv','.veyra-runtime','node_modules') for part in rel.parts):raise ValueError('Protected package path')
    if not rel.parts or rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe package path')
    target=root/rel
    for part in [target,*target.parents]:
        if part==root.parent:break
        if part.is_symlink():raise ValueError('Refusing symlink: '+name)
    return target


def git(root,*args):
    result=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True)
    if result.returncode:raise ValueError('Git check failed. Run from your existing repository root.')
    return result.stdout.strip()


def guard(root,require_clean=True):
    if git(root,'branch','--show-current')!=BRANCH:raise ValueError('Switch to '+BRANCH+' first. Main/other branches are protected.')
    if require_clean and (git(root,'diff','--name-only') or git(root,'diff','--cached','--name-only')):
        raise ValueError('Uncommitted tracked changes exist. Commit or back up your work before installing; nothing was changed.')
    if Path(git(root,'rev-parse','--show-toplevel')).resolve()!=root:raise ValueError('Run from the Git repository root.')
    if not (root/'backend/app/main.py').is_file():raise ValueError('Choose the existing Veyra repository root.')


def plan(bundle,root):
    manifest=json.loads((bundle/'manifest.json').read_text());operations=[];conflicts=[];seen=set()
    for item in manifest.get('compatibilityFiles',[]):
        target=safe_path(root,item['path'])
        if not target.is_file() or digest(target.read_bytes())!=item['sha256']:
            raise ValueError('API/evidence compatibility anchor differs: '+item['path']+'. No files changed; reconcile this baseline first.')
    for item in manifest['files']:
        name=item['path']
        if name in seen:raise ValueError('Duplicate package path')
        seen.add(name);target=safe_path(root,name)
        data=safe_path(bundle/'updated',name).read_bytes()
        if digest(data)!=item['sha256']:raise ValueError('Payload checksum mismatch: '+name)
        base_hash=item.get('baselineSha256')
        if base_hash is not None:
            base=safe_path(bundle/'baseline',name).read_bytes()
            if digest(base)!=base_hash:raise ValueError('Baseline checksum mismatch: '+name)
        current=target.read_bytes() if target.exists() else None
        if current==data:continue
        if (digest(current) if current is not None else None)!=base_hash:
            conflicts.append(name);continue
        operations.append((item,target,current,data))
    if conflicts:raise ValueError('Files differ from the supplied reconstructed V0.3.1 baseline. No files changed; review these paths:\n'+'\n'.join(conflicts))
    return operations


def write_atomic(target,data,mode):
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.veyra-v032-',dir=target.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data)
        os.chmod(tmp,mode&0o777);os.replace(tmp,target)
    finally:
        if Path(tmp).exists():Path(tmp).unlink()


def install(bundle,root,write=False):
    guard(root);operations=plan(bundle,root)
    print(str(len(operations))+' changed files are safe to apply.')
    if not write or not operations:return None
    backups=safe_path(root,BACKUPS);backups.mkdir(mode=0o700,exist_ok=True)
    backup=Path(tempfile.mkdtemp(prefix='update-',dir=backups));journal=[]
    for item,target,current,data in operations:
        # Recheck the preimage before making any writes.
        if (target.read_bytes() if target.exists() else None)!=current:raise ValueError('A file changed during planning; rerun --check.')
        mode=target.stat().st_mode&0o777 if current is not None else None
        if current is not None:
            original=safe_path(backup/'original',item['path']);original.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,original)
        journal.append({'path':item['path'],'existed':current is not None,'originalSha256':digest(current) if current is not None else None,
                        'installedSha256':digest(data),'mode':mode})
    (backup/'journal.json').write_text(json.dumps(journal,indent=2))
    written=[]
    try:
        for (item,target,current,data),entry in zip(operations,journal):
            if (target.read_bytes() if target.exists() else None)!=current:raise ValueError('A file changed during installation.')
            write_atomic(target,data,item.get('mode',0o644));written.append((target,entry))
    except BaseException:
        for target,entry in reversed(written):
            if entry['existed']:write_atomic(target,safe_path(backup/'original',entry['path']).read_bytes(),entry['mode'])
            else:target.unlink()
        raise
    print('Installed. Backup: '+str(backup.relative_to(root)))
    return backup


def rollback(root,which):
    guard(root,require_clean=False)
    backups=safe_path(root,BACKUPS)
    if which=='latest':
        entries=sorted([p for p in backups.glob('update-*') if (p/'journal.json').is_file()],key=lambda p:p.stat().st_mtime_ns)
        if not entries:raise ValueError('No update backup found.')
        backup=safe_path(root,str(entries[-1].relative_to(root)))
    else:
        backup=safe_path(root,which)
        if backup.parent!=backups:raise ValueError('Choose a backup directly inside '+BACKUPS)
    journal=json.loads((backup/'journal.json').read_text());operations=[]
    for entry in journal:
        target=safe_path(root,entry['path'])
        if not target.is_file() or digest(target.read_bytes())!=entry['installedSha256']:
            raise ValueError('Rollback refused: file changed since installation: '+entry['path'])
        original=safe_path(backup/'original',entry['path']).read_bytes() if entry['existed'] else None
        if original is not None and digest(original)!=entry['originalSha256']:raise ValueError('Backup checksum mismatch')
        operations.append((target,original,entry))
    for target,original,entry in operations:
        if original is None:target.unlink()
        else:write_atomic(target,original,entry['mode'])
    print('Rollback restored the pre-installation files; unrelated files were preserved.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repo',default='.')
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check',action='store_true');action.add_argument('--apply',action='store_true');action.add_argument('--rollback',metavar='BACKUP_OR_latest')
    args=parser.parse_args();root=Path(args.repo).resolve()
    if args.rollback:rollback(root,args.rollback)
    else:install(Path(__file__).resolve().parent,root,args.apply)


if __name__=='__main__':
    try:main()
    except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(1)
