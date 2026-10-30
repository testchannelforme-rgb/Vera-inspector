#!/usr/bin/env python3
"""Read-only disk/cache inventory. Safe removals live in clean-disposable.py."""
import json
from pathlib import Path
import shutil
import subprocess
root=Path(__file__).resolve().parents[1]
u=shutil.disk_usage(root)
print(json.dumps({'root':str(root),'totalBytes':u.total,'usedBytes':u.used,'freeBytes':u.free,'freePercent':round(100*u.free/u.total,2),'targetReached':u.free/u.total>=.5}))
subprocess.run(['du','-h','-d','2',str(root)],check=False)
for candidate in [Path.home()/'.cache/pip',Path.home()/'.npm/_cacache',Path.home()/'.cache/ms-playwright']:
 if candidate.exists():subprocess.run(['du','-sh',str(candidate)],check=False)
print('Report only. Do not delete active browser/dependency caches, source, secrets, databases, backups or Git history to chase a disk target.')
