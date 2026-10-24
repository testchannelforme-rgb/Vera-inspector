import importlib.util
import json
import hashlib
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('apply_update',Path(__file__).resolve().parents[2]/'scripts/apply_update.py')
updater=importlib.util.module_from_spec(spec);spec.loader.exec_module(updater)


def bundle(tmp_path,old,new):
    root=tmp_path/'repo';root.mkdir();(root/'backend/app').mkdir(parents=True);(root/'backend/app/main.py').write_text('baseline')
    (root/'frontend/src').mkdir(parents=True);(root/'frontend/src/App.jsx').write_text('UI')
    package=tmp_path/'bundle';(package/'baseline').mkdir(parents=True);(package/'updated').mkdir()
    name='notes.txt';(root/name).write_text(old);(package/'baseline'/name).write_text(old);(package/'updated'/name).write_text(new)
    (package/'update-manifest.json').write_text(json.dumps({'files':[{'path':name,'sha256':hashlib.sha256(new.encode()).hexdigest(),'mode':0o644}]}))
    return root,package


def test_check_then_apply_preserves_backup_and_unrelated_work(tmp_path):
    root,package=bundle(tmp_path,'old\n','new\n');(root/'my-work.txt').write_text('keep')
    assert updater.apply(package,root)==0 and (root/'notes.txt').read_text()=='old\n'
    assert updater.apply(package,root,True)==0 and (root/'notes.txt').read_text()=='new\n'
    assert (root/'my-work.txt').read_text()=='keep'
    assert next((root/'.v02-backups').rglob('notes.txt')).read_text()=='old\n'


def test_conflict_never_partially_updates(tmp_path):
    root,package=bundle(tmp_path,'old\n','new\n');(root/'notes.txt').write_text('my conflicting work\n')
    assert updater.apply(package,root,True)==2
    assert (root/'notes.txt').read_text()=='my conflicting work\n'
    assert not (root/'.v02-backups').exists()


def test_safe_nonconflicting_three_way_merge(tmp_path):
    base='line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\n'
    root,package=bundle(tmp_path,base,base.replace('line1','updated1'))
    (root/'notes.txt').write_text(base.replace('line8','my8'))
    assert updater.apply(package,root,True)==0
    text=(root/'notes.txt').read_text();assert 'updated1' in text and 'my8' in text


def test_payload_integrity_and_symlink_rejection(tmp_path):
    root,package=bundle(tmp_path,'old','new');(package/'updated/notes.txt').write_text('tampered')
    with pytest.raises(ValueError,match='checksum'):updater.apply(package,root,True)
    with pytest.raises(ValueError,match='Unsafe'):updater.safe_target(root,'../outside')
    (root/'link').symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):updater.safe_target(root,'link/outside.txt')
