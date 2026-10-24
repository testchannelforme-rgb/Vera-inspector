# Applying V0.2 to the existing Vera-inspector repository

This is an incremental update based on the delivered V0.1 source. Current GitHub source could not be retrieved through the available connection. Do not delete or replace the repository. The archive contains a guarded updater, a patch and complete source for reference.

## Tablet / Codespaces steps

1. Download `Veyra_Inspector_V0.2.zip`. In your existing Codespaces browser editor, use the Explorer upload action to upload it to the directory containing `backend`, `frontend` and `start.sh`.
2. In that directory's terminal run:

```bash
unzip -q Veyra_Inspector_V0.2.zip
python3 veyra-v02-update/apply_update.py --check
```

3. If it reports no conflicts, apply:

```bash
python3 veyra-v02-update/apply_update.py --apply
```

Existing files are backed up under `.v02-backups/update-...`. Locally changed files are three-way merged using the packaged V0.1 baseline. If any merge conflicts, **no project file is changed**. Do not force-copy the complete source over local work. Review the named conflicts against `veyra-v02-update/baseline` and `veyra-v02-update/updated`, or share only those nonsensitive source files for reconciliation.

4. Choose **Codespaces: Rebuild Container** from the command palette. The new development image installs matching Playwright/Chromium and its system libraries during build; Docker-in-Docker supplies the isolated browser stack. No change to the old Yarn APT signing key is needed because the rebuilt image uses clean distribution sources.
5. Once setup finishes, start public inspection:

```bash
bash start.sh --isolated
```

6. Open forwarded port **8000** with visibility **Private**. Enter `example.com`. Once it works, try `react.dev`, then Roblox and inspect the new Page diagnostics panel. A site restriction is an error to report, not something to bypass.
7. Run actual target-host checks:

```bash
bash scripts/test.sh --public
.venv/bin/python scripts/test_public.py
```

The first command checks the local sandboxed engine/fixture and unit tests; the second exercises the isolated public API against multiple live sites. In an isolated-only host where a direct/local Chromium launch is unsupported, the local probe may fail even when the separate public browser works. Report both results rather than changing the local sandbox settings.

## Stop/start and diagnostics

```bash
docker compose -f compose.inspection.yml stop
bash start.sh --isolated
bash scripts/doctor.sh --environment-only
docker compose -f compose.inspection.yml logs --tail=80 browser gateway app
```

If Docker, IPv6 netfilter, namespace support or firewall capabilities are unavailable, public mode stops with an error. Do not remove firewall rules or disable the Chromium sandbox. Restricted mode remains `bash start.sh` with explicit approved public hosts.

The default private subnet `172.30.88.0/24` must not overlap an existing Docker network. If there is a conflict, stop and adjust the Compose subnet, gateway address, browser firewall, readiness proof and tests together; do not change only the proxy URL.

## Reviewing and committing

Review `git status --short` and `git diff` after applying. Stage only the intended files listed in `docs/MODIFIED_FILES.md`, plus any deliberate conflict resolution. The update excludes `.env`, credentials, virtual environments, node_modules, Git metadata and `.veyra-runtime`. Generated capabilities, backups and the update archive are ignored. No remote commit, branch, PR or public deployment was created during delivery.

`veyra-v02-update/patches/veyra-v0.2.patch` is an alternative unified patch. Use `git apply --check` before applying it. The complete `full-source/` tree is a reference/runnable copy; the updater does not replace your project with it.
