# Apply V0.3 to the existing V0.2 repository

The remote GitHub repository could not be read (404). This package is an incremental update against the retained V0.2 delivery. Your live source may differ; review conflicts rather than force-copying files.

1. In the existing Codespace, check `git status`. Preserve your current work using your usual commit or backup process. No script resets Git or discards changes.
2. Upload `Veyra_AI_V0.3.zip` beside `backend`, `frontend` and `start.sh` using Explorer.
3. Create a feature branch, then check and apply:

```bash
git switch -c feature/v0.3-prompt-engine
unzip -q Veyra_AI_V0.3.zip
python3 veyra-v03-update/apply_update.py --check
python3 veyra-v03-update/apply_update.py --apply
```

The unchanged V0.2 updater performs checksum/path checks, plans all files, attempts three-way merges and refuses the whole update on conflict. Backups retain the existing folder convention `.v02-backups/update-*`. It does not delete unrelated files or create Git commits. `baseline/` and `updated/` support review. If any conflict is reported, no project file changes; compare those specific files manually. `full-source/` is a reference, not permission to overwrite a customized repository.

4. Start with the existing isolated stack:

```bash
bash start.sh --isolated
```

Docker rebuilds the app/frontend and installs its pinned HTTPX runtime dependency. Browser image, seccomp, firewall rules, private ports and devcontainer remain unchanged. A fresh Codespace still needs **Codespaces: Rebuild Container**. This update was not executed in Codespaces here.

5. Keep forwarded port 8000 Private. Test example.com inspection, selection, hover and JSON export first. Then generate a local prompt, edit/copy/regenerate it, change scope and inspect the warnings. Select a different element to verify stale drafts clear.
6. Install development dependencies with `bash scripts/setup.sh`, then run the tests in README. Review `git diff` before committing or opening a PR. This delivery did not push to GitHub or open a PR.

The bundle also includes `patches/veyra-v0.3.patch`; `git apply --check` is suitable for an unmodified matching baseline, but the guarded updater is safer for local changes. Never use force/reset commands to apply this upgrade.
