# Safely install V0.3.2 in your existing Codespace

This is a changed-files update, not a replacement project. Use the actual current V0.3.1 checkout, including your later Codespaces UI-test/config fixes. The installer requires Python 3.11+ and Git. Installation itself needs no network.

## 1. Protect your work and create the branch

Open your existing Codespace on your tablet. Open Terminal → New Terminal at the repository root:

```bash
git status --short
git branch --show-current
git log -1 --oneline
```

If there are uncommitted changes, save/commit or independently back them up **before proceeding**. Review files individually before staging; never stage `.env`, credentials, runtime data or caches. The installer refuses tracked changes, including staged changes. It does not stash or discard anything.

From your verified, latest installed V0.3.1 checkout:

```bash
git branch backup/pre-v032-visual-fidelity
git switch -c feature/v0.3.2-visual-fidelity
```

If the backup name already exists, choose a new backup name; do not move/delete the old branch. If the target branch already exists, use `git switch feature/v0.3.2-visual-fidelity` only after verifying its source is the intended baseline. Stable backup branches remain untouched. No checkout of the supplied attachment is needed in your existing repository.

## 2. Upload, extract and check

In Codespaces Explorer, upload `Veyra_AI_V0.3.2_Visual_Fidelity_Update.zip` to the repository root. If a `veyra-v032-update` directory already exists, move it outside the repository or rename it before extraction; do not overwrite a prior package or backup.

```bash
unzip -q Veyra_AI_V0.3.2_Visual_Fidelity_Update.zip
python3 veyra-v032-update/apply_update.py --check
```

The check verifies repository/branch, every overwritten file against an exact expected baseline or already-installed payload, new-file collisions, compatibility anchors, payload/baseline SHA-256 checksums and safe paths/symlinks. No source file is written during `--check`.

**If it stops:** do not use `cp`, overwrite prompts, edit manifest hashes or reset the repository to force installation. Your latest installed source differs. Preserve it, compare the reported paths with the package's `baseline/` and `updated/` copies and `changes.patch`, then request/review a reconciled update against those current files. Unrelated committed changes are preserved. The exact checkpoint `29ef127` and later uncommitted Codespaces changes could not be inspected here, so automatic compatibility cannot be promised.

## 3. Apply and start

Only after the check passes:

```bash
python3 veyra-v032-update/apply_update.py --apply
bash start.sh --isolated
```

Backups are created first in `.v032-backups/update-*` with a hash journal. Each preimage is rechecked before writing; writes use atomic replacement. A mid-install failure restores already-written files. Nothing merges, commits, switches branches, stashes, pushes or deploys automatically.

Open forwarded port **8000** and keep visibility **Private**. The existing Docker startup rebuilds the app/frontend, checks network isolation and browser readiness, and stops public browsing if verification fails. Preserve your existing Docker/devcontainer/CSP fixes. No API key is needed.

On a clean environment only, run `bash scripts/setup.sh` in the maintained devcontainer. Do not run browser tests with sandbox disabled or change CSP to pass tests. A restart should use the same `bash start.sh --isolated` command. Rebuild Container only if your existing environment requires it; this update does not alter system dependency setup.

Run the commands in TEST_REPORT.md and the acceptance checklist before claiming real-site accuracy. Review and commit only the intended changed source/docs/tests once satisfied.

## Rollback

Before making further source edits:

```bash
python3 veyra-v032-update/apply_update.py --rollback latest
bash start.sh --isolated
```

Rollback restores pre-installation bytes/modes and removes files introduced by this update. It preserves unrelated files and refuses if installed files have since changed or backup hashes disagree. If refused, preserve those later edits and review the journal/backups manually; never force overwrite. If you committed the update, rollback intentionally leaves source changes in the worktree for review; it does not rewrite Git history. Keep the package and `.v032-backups` until acceptance is complete.
