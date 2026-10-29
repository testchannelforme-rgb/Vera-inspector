# Install Veyra AI V0.4.0

Target branch: `feature/v0.4-code-studio`. Verified baseline: V0.3.3 commit `08b804c71eadd9e324cf04581572e19d609f0f89`.

## Git bundle (preserves the exact feature commit)

The GitHub connection rejected source writes with HTTP 403. The feature branch was committed locally and is supplied in `Veyra_AI_V0.4.bundle`; it was **not pushed to GitHub**. Existing remote branches remain untouched.

Unzip the release outside your repository. Save important local edits before switching branches. In the existing repository, fetch the bundled branch into a new branch name:

```bash
git status --short
git bundle verify /path/to/Veyra_AI_V0.4/Veyra_AI_V0.4.bundle
git fetch /path/to/Veyra_AI_V0.4/Veyra_AI_V0.4.bundle feature/v0.4-code-studio:feature/v0.4-code-studio
git switch feature/v0.4-code-studio
bash scripts/setup.sh
bash start.sh --isolated
```

The bundle requires the verified V0.3.3 baseline commit already in the repository. If the target local branch already exists, choose a fresh destination name; never force-update it. Review the imported branch, then push it using your own GitHub access if wanted. Do not reset/clean a dirty checkout. Retain `.env` and runtime secrets.

## Incremental ZIP

Unzip `Veyra_AI_V0.4.zip` outside the repository. From the existing repository root, run the bundled `update/apply_update.py` with its actual path:

```bash
python3 /path/to/Veyra_AI_V0.4/update/apply_update.py --repo . --check
python3 /path/to/Veyra_AI_V0.4/update/apply_update.py --repo . --apply
```

The installer uses baseline/new content plus three-way merging for local changes. It makes no changes if any conflicts need review. It preserves unrelated files, branches, history, secrets and dependencies. It backs up replaced files under `.v02-backups`; that inherited backup name does not indicate an old application version. Re-running an already-applied update is safe. A `source/` snapshot is also supplied for review, not for blindly replacing a working directory.

If V0.3.3 never fully applied, the ZIP check can fail because required baseline files are absent. Restore the committed V0.3.3 branch in a separate clean checkout, or import the supplied V0.4 Git bundle. Do not force the ZIP over an unknown V0.3.x tree.

Then run setup once. Stop an old Veyra instance intentionally before starting another. For the Compose instance, `docker compose -f compose.inspection.yml stop` preserves volumes. Do not prune images, volumes or backups to chase an arbitrary disk target. Local startup refuses occupied 8001. Compose startup checks browser isolation and health version; the health response includes the baked source revision.

Open private forwarded **8001**, then check `/api/health` for `version: 0.4.0` and the expected commit. `python3 scripts/verify-version.py` additionally checks the current checkout revision. A source ZIP applied as uncommitted edits reports the repository's commit plus `sourceDirty: true`; commit the reviewed changes to obtain a clean revision identity. The ZIP includes its source revision in `RELEASE.json`.

Configure an AI provider only if wanted. Local reconstruction, editor, preview and exports work without one. Read README for preview security limits and tests still required on the actual Codespace.
