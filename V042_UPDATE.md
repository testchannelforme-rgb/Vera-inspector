# Install VEYRA AI V0.4.2 — Blue Hour

Baseline: V0.4.1 commit `531b0298dff3873259eb1f9dc3182195d6ea53ff`. Target branch: `feature/v0.4.2-blue-hour`. Preserve existing edits and secrets before switching branches.

## Check storage first in the actual Codespace

The build workspace is not your Codespace. Its recorded cleanup results are in `docs/v042/storage-cleanup.json`. Run the existing `python3 scripts/clean-disposable.py` to preview safe candidates; add `--apply` to remove those untracked caches/build outputs. After importing this update, `python3 scripts/storage-audit.py` provides a read-only disk/cache inventory. Neither script deletes dependencies, Git history, secrets, databases, important backups, tracked archives or user exports. Aim for 50% free; stop short if reaching it would damage the environment.

## Import the exact commit

Unzip `Veyra_AI_V0.4.2.zip` outside the repository. Its Git bundle preserves the exact feature commit:

```bash
git status --short
git bundle verify /path/to/Veyra_AI_V0.4.2/Veyra_AI_V0.4.2.bundle
git fetch /path/to/Veyra_AI_V0.4.2/Veyra_AI_V0.4.2.bundle feature/v0.4.2-blue-hour:feature/v0.4.2-blue-hour
git switch feature/v0.4.2-blue-hour
bash scripts/setup.sh
```

If that local branch already exists, fetch into a fresh branch name; do not force-update it. The bundle requires the baseline commit to be present. Alternatively, use the guarded installer from your existing Veyra repository root:

```bash
python3 /path/to/Veyra_AI_V0.4.2/update/apply_update.py --repo . --check
python3 /path/to/Veyra_AI_V0.4.2/update/apply_update.py --repo . --apply
```

It checks exact payload hashes and performs safe three-way merges before writing anything. Conflicts stop the update; replaced files are backed up. It preserves unrelated files, `.env`, runtime data and Git history. The source snapshot is for review, not a reason to overwrite a dirty directory.

Stop the existing Veyra process intentionally. For Compose:

```bash
docker compose -f compose.inspection.yml stop
bash start.sh --isolated
python3 scripts/verify-version.py
```

Keep forwarded **8001 private**. Expect version `0.4.2`, the release's source commit and a ready protected browser. A ZIP installer applied as uncommitted edits has `sourceDirty: true`; bundle import preserves clean commit identity. Existing provider environment settings and quotas remain. No key or paid service is required for local reconstruction.

## Workspace controls

Fullscreen Editor, Fullscreen Inspector and Fullscreen Preview are separate. Native browser fullscreen is used where available; otherwise a fixed maximized workspace preserves the same mounted view. Exit controls and Escape remain available. Compare also has its own fullscreen control. Original inspection keeps click-to-select, hover outlining, screenshot-coordinate mapping, remote scrolling and existing captured-hover analysis. It does not turn original-site clicks into unrestricted navigation or form submission.

Compare shows the real current inspection frame beside the generated sandbox. Choose a device size, then Match original viewport to align logical CSS viewports; this preserves the source page without navigating it. Both sides have independent scroll areas. Optional synchronization sends original-page wheel/swipe deltas to the generated document in one direction; unrelated document structures may scroll differently. Section-only output is not automatically aligned to a full original page. A missing/expired original view is reported; cached frames are labelled on action failure.

Device sizes are 320–1440 × 320–1000 CSS pixels. Oversized values are clamped for the iframe and cannot be applied to the remote browser. Smaller screens may pan horizontally to inspect a full logical viewport. Changing size does not remount the editor.

Click to edit is separate from normal preview interaction. Supported elements retain `data-veyra-node` markers. A unique matching marker opens the corresponding HTML or JSX source and selects its opening-tag range. Missing/duplicate IDs are reported; arbitrary source is never guessed by visible text. Some provider outputs may omit markers. No promise of full source maps for arbitrary components is made.

## Autosave / privacy

`veyra.code-studio.v2` stores the current code, active file, original generation and up to five checkpoints on this browser origin, capped at 2 MiB. Saves are debounced; status distinguishes saved, unsaved and failed/conflicting states. A draft is restored at startup. AI session credentials/context are not persisted with it; restored code can be edited/exported, but refinement needs a fresh live generation context.

Cross-tab updates pause autosave instead of overwriting newer saved code. Restore actions require confirmation and checkpoint current edits. Pause autosave or clear saved data via Data preferences. Shared-device users should review the stored code; it may contain private source text. The app cannot guarantee recovery after browser eviction, storage failure, or closing before a pending save completes. Download portable backups. Clearing local data preserves the open editor and pauses autosave rather than immediately recreating the deleted draft.

## Console / progress / motion

The console retains up to 80 redacted/truncated entries. Preview messages must come from the active opaque iframe; instrumented events additionally use a fresh per-render capability token. These messages navigate source or display diagnostics; they never grant backend operations or host DOM access. Instrumentation sends at most 300 events per document. Compiler failures and console warnings/errors are captured; asset failures are best effort. AI fix preparation fills the existing refinement instruction; review it and grant existing consent before sending anything.

Generation stages come from the server at actual operation boundaries. No timer-driven fake percentages or automatic generation retry exists. Status polling permits one outstanding request. Some short stages may finish between polls; the final response contains the actual recorded stages. Refining appears only if a repair really runs.

Motion 14.8.0 MIT core is the only new animation library. Shared host transition tokens and `prefers-reduced-motion` support are documented in `docs/MOTION_V042.md`. Generated website bundles do not import host motion or Blue Hour CSS. The attached mark is cropped/resized from the supplied image, not replaced or recolored; original raster reference is retained.

Alt+Shift shortcuts: E editor, I inspector, P preview, C compare, S save, R refresh, J next file, X console, F focus. Escape exits fullscreen/focus. Shortcuts are handled in the host; focus inside the sandboxed iframe may be handled by that document/browser instead. Visible controls provide equivalent access on touch devices.

## Limits retained

The existing sandbox is a private development boundary, not a VM or complete CPU/navigation firewall for hostile code. Keep deployments private. Existing URL validation, SSRF/private-address blocking, isolated browser/gateway, generation quotas, payload bounds and provider secrecy remain. External AI and a fresh Docker/protected-browser startup require verification in your Codespace; tests using injected providers are not live cloud inference. Read `TEST_REPORT_V042.md` for exact executed results and remaining limits.
