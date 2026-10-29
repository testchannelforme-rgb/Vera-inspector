import importlib.util
import json
from pathlib import Path
import subprocess
import pytest

spec=importlib.util.spec_from_file_location('install_v032',Path(__file__).resolve().parents[2]/'scripts/install_v032.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)


def make_bundle(tmp_path):
    repo=tmp_path/'repo';repo.mkdir();(repo/'backend/app').mkdir(parents=True)
    (repo/'backend/app/main.py').write_text('baseline\n');(repo/'notes.txt').write_text('old\n')
    subprocess.run(['git','init','-b',installer.BRANCH],cwd=repo,check=True,capture_output=True)
    subprocess.run(['git','add','.'],cwd=repo,check=True)
    subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.com','commit','-m','baseline'],cwd=repo,check=True,capture_output=True)
    bundle=tmp_path/'bundle';(bundle/'updated').mkdir(parents=True);(bundle/'baseline').mkdir()
    (bundle/'updated/notes.txt').write_text('new\n');(bundle/'baseline/notes.txt').write_text('old\n')
    (bundle/'updated/new.txt').write_text('new file\n')
    entries=[{'path':'notes.txt','sha256':installer.digest(b'new\n'),'baselineSha256':installer.digest(b'old\n')},
             {'path':'new.txt','sha256':installer.digest(b'new file\n'),'baselineSha256':None}]
    (bundle/'manifest.json').write_text(json.dumps({'files':entries}))
    return repo,bundle


def test_check_apply_backup_and_rollback(tmp_path):
    repo,bundle=make_bundle(tmp_path);(repo/'unrelated.txt').write_text('keep')
    installer.install(bundle,repo);assert (repo/'notes.txt').read_text()=='old\n'
    backup=installer.install(bundle,repo,True)
    assert (repo/'notes.txt').read_text()=='new\n' and (backup/'original/notes.txt').read_text()=='old\n'
    installer.rollback(repo,'latest')
    assert (repo/'notes.txt').read_text()=='old\n' and not (repo/'new.txt').exists()
    assert (repo/'unrelated.txt').read_text()=='keep'


def test_dirty_working_tree_and_wrong_branch_are_rejected(tmp_path):
    repo,bundle=make_bundle(tmp_path);(repo/'notes.txt').write_text('uncommitted')
    with pytest.raises(ValueError,match='Uncommitted'):installer.install(bundle,repo,True)
    subprocess.run(['git','switch','-c','main'],cwd=repo,check=True,capture_output=True)
    with pytest.raises(ValueError,match='Main/other branches'):installer.install(bundle,repo,True)
    assert (repo/'notes.txt').read_text()=='uncommitted'


def test_committed_baseline_difference_is_not_overwritten(tmp_path):
    repo,bundle=make_bundle(tmp_path);(repo/'notes.txt').write_text('new committed work')
    subprocess.run(['git','add','.'],cwd=repo,check=True)
    subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.com','commit','-m','local change'],cwd=repo,check=True,capture_output=True)
    with pytest.raises(ValueError,match='differ from'):installer.install(bundle,repo,True)
    assert not (repo/'new.txt').exists()


def test_rollback_rejects_later_edits_and_payload_tampering(tmp_path):
    repo,bundle=make_bundle(tmp_path);installer.install(bundle,repo,True)
    (repo/'notes.txt').write_text('later edit')
    with pytest.raises(ValueError,match='changed since'):installer.rollback(repo,'latest')
    assert (repo/'new.txt').exists()
    (bundle/'updated/notes.txt').write_text('tampered')
    with pytest.raises(ValueError,match='Payload checksum'):installer.plan(bundle,repo)


def test_path_symlink_and_baseline_tampering_rejected(tmp_path):
    repo,bundle=make_bundle(tmp_path)
    with pytest.raises(ValueError,match='Unsafe'):installer.safe_path(repo,'../escape')
    (repo/'link').symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):installer.safe_path(repo,'link/escape')
    (bundle/'baseline/notes.txt').write_text('corrupt')
    with pytest.raises(ValueError,match='Baseline checksum'):installer.plan(bundle,repo)


def test_existing_unmodified_ui_test_fixes_are_preserved(tmp_path):
    repo,bundle=make_bundle(tmp_path)
    (repo/'local-ui-test.py').write_text('# Codespace-specific test fix\n')
    subprocess.run(['git','add','local-ui-test.py'],cwd=repo,check=True)
    subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.com','commit','-m','Codespace test checkpoint'],cwd=repo,check=True,capture_output=True)
    installer.install(bundle,repo,True)
    assert (repo/'local-ui-test.py').read_text()=='# Codespace-specific test fix\n'
    installer.rollback(repo,'latest')
    assert (repo/'local-ui-test.py').read_text()=='# Codespace-specific test fix\n'


def test_protected_git_credentials_and_runtime_paths_rejected(tmp_path):
    repo,bundle=make_bundle(tmp_path)
    for path in ['.git/config','.env','.venv/config','backend/node_modules/token','.veyra-runtime/password']:
        with pytest.raises(ValueError,match='Protected'):installer.safe_path(repo,path)


def test_compatibility_anchor_is_verified_before_any_write(tmp_path):
    repo,bundle=make_bundle(tmp_path)
    manifest=json.loads((bundle/'manifest.json').read_text())
    manifest['compatibilityFiles']=[{'path':'backend/app/main.py','sha256':installer.digest(b'different baseline')} ]
    (bundle/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='compatibility anchor'):installer.install(bundle,repo,True)
    assert (repo/'notes.txt').read_text()=='old\n' and not (repo/'new.txt').exists()


def test_cross_platform_path_separator_is_rejected(tmp_path):
    repo,bundle=make_bundle(tmp_path)
    with pytest.raises(ValueError,match='Unsafe'):installer.safe_path(repo,r'..\escape')
