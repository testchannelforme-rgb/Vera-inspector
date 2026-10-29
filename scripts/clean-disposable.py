#!/usr/bin/env python3
"""Report by default. --apply removes only named project caches and build output."""
import argparse
from pathlib import Path
import shutil
import subprocess
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
root=Path(__file__).resolve().parents[1]
tracked=set(subprocess.check_output(['git','ls-files'],cwd=root,text=True).splitlines())
# Never touch dependencies, browser installs, logs, exports, archives, Git or backups.
candidates=[root/'.pytest_cache',root/'frontend/dist',root/'frontend/node_modules/.vite']
candidates += list((root/'backend').rglob('__pycache__'))
seen=set();total=0
for item in candidates:
 if item in seen or not item.exists() or item.is_symlink():continue
 seen.add(item);rel=item.relative_to(root).as_posix()
 if any(n==rel or n.startswith(rel+'/') for n in tracked):continue
 files=list(item.rglob('*')) if item.is_dir() else [item]
 if any(f.is_symlink() for f in files):continue
 size=sum(f.stat().st_size for f in files if f.is_file());total+=size
 print(('REMOVE ' if args.apply else 'WOULD REMOVE ')+rel+f' ({size:,} bytes)')
 if args.apply:
  if item.is_dir():shutil.rmtree(item)
  else:item.unlink()
print(f'Disposable total: {total:,} bytes. Free disk: {shutil.disk_usage(root).free:,} bytes.')
