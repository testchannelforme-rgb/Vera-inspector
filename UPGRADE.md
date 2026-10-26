# Install V0.3.1 safely from the attached V0.3 baseline

This update was built from `Veyra_V0.3_Clean_For_Sol.zip`, not a GitHub checkout. It cannot include uncommitted Codespaces edits that were absent from your attachment. No remote connectivity is required.

1. Open your existing Codespace on the tablet. In the repository terminal run `git status --short`. Commit or separately back up current work before proceeding. The installer refuses staged/unstaged tracked changes and does not stash them automatically. Protect any untracked personal files too; existing paths are never silently replaced.
2. Use Explorer's upload action to upload `Veyra_AI_V0.3.1_Update.zip` beside `backend`, `frontend` and `start.sh`.
3. Create or select the required branch:

```bash
git switch -c feature/v0.3.1-prompt-accuracy
```

If it already exists, use `git switch feature/v0.3.1-prompt-accuracy` instead. The installer refuses to run on main or any other branch.

4. Extract, check, then apply only if the check succeeds:

```bash
unzip -q Veyra_AI_V0.3.1_Update.zip
python3 veyra-v031-update/apply_update.py --check
python3 veyra-v031-update/apply_update.py --apply
```

The package's `manifest.json` lists every changed/new path, original SHA256 (or null for a new file), updated SHA256, mode and purpose. `updated/` preserves repository-relative paths; `baseline/` contains only replaced source for comparison. These are not extra historical release archives. No complete application replacement is required.

The installer checks all paths and hashes before writing. If a current file differs from the attachment, it reports that path and makes **no changes**. Compare `baseline/`, `updated/` and your current source, reconcile manually and test; do not force-copy or reset to bypass the refusal. Even committed Codespaces changes absent from the attachment require review.

Application uses same-directory atomic writes, original-file backups and rollback on a write failure. Successful backups are under `.v031-backups/update-*`, with a hash-checked journal identifying replaced and newly created files. Keep them until acceptance passes. Only the packaged files change; unrelated work is left alone.

5. Rebuild/start the existing app stack:

```bash
bash start.sh --isolated
```

The app image builds the changed frontend/backend. No dependency version, browser container, firewall, seccomp or devcontainer change is required. For a fresh environment use **Codespaces: Rebuild Container** first. Open port 8000 with visibility **Private**.

6. Follow [manual acceptance](docs/V031_ACCEPTANCE.md), review `git diff` and commit only the intended update files. Do not commit credentials, `.env`, runtime capabilities, backups or the release ZIP. The supplied ignore rules cover the update folder/ZIP/backups.

Rollback before subsequent edits:

```bash
python3 veyra-v031-update/apply_update.py --rollback latest
bash start.sh --isolated
```

Rollback checks every current installed file against its journal hash before restoring any source. If you have edited, deleted or replaced an installed file since applying, rollback refuses the whole operation; preserve/reconcile that work manually first. You may replace `latest` with the exact printed path `.v031-backups/update-...` to choose a particular backup. Newly added update files are removed only after those checks; unrelated files stay in place. Keep using the feature branch for rollback.

A second `--check` while the applied files are still uncommitted will intentionally report a dirty working tree. After reviewing/committing the update, reapplying a matching package is a zero-file operation.

This package was not run in Codespaces. Test logs here cannot establish that your live website/browser stack works after installation. No script pushes to GitHub, force-pushes, deploys publicly or changes main.
