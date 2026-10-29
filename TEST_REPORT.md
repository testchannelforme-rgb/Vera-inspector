# V0.3.3 candidate verification — 29 October 2026

Baseline commit: `349db3b671fc77c543b5073cdb85cd9a0a115b6e`. Branch: `feature/v0.3.3-ui-prompt-polish`.

## Work runtime (executed)

- Existing + extended Node/React/JavaScript tests: **60 passed, 0 failed**.
- Existing + extended Python/API/security/preset/report tests: **309 passed, 22 skipped, 0 failed**, one inherited Starlette/httpx deprecation warning.
- Vite production build: **passed**.
- `git diff --check`: **passed**.
- The managed cloud browser rendered the actual homepage and inspector. Its frontend preview has no connected inspection backend in this host, so empty/error states are real, not a fabricated successful website inspection.

Sandboxed Chromium could not be installed here: the official Playwright download repeatedly returned an incomplete/invalid archive. Docker is unavailable in this runtime. The existing 20 browser cases and two new candidate browser cases were skipped here; this is not a claim of browser acceptance. No sandbox flag or network restriction was relaxed.

The initial baseline suite started concurrently with the first frontend build, so its frontend-serving test initially returned 404 before dist existed. Building first and rerunning that exact baseline test passed. Candidate validation runs in the correct build-before-test order.

## Existing Codespace acceptance

Pending execution of the new real-browser acceptance suite in the existing sandbox-capable Codespace. Final execution results and any failures must replace this pending statement before delivery.

## Coverage added

- Five strict presets; eight numbered sections, exact captured CSS and unknown responsive/hover data retained.
- Maximum-visual budget and report coverage agreement; bounded assets and sanitization flags; no fabricated accuracy percentage.
- Default local generation does not call an AI provider; optional AI acknowledgement and fallback behavior.
- Real React draft editing, stale-selection detachment, regeneration Undo, explicit history save/restore and per-generation AI acknowledgement.
- Device persistence limits, corrupt/blocked storage, delete/duplicate, no silent eviction and no unrelated data deletion.
- Exact edited TXT/Markdown/section exports, object URL cleanup and missing-evidence checklist.
- Addressable homepage/inspector/draft policy/contact/brand/preference routes.
- New real-browser suite: desktop/tablet/mobile navigation/layout, tutorial, actual fixture selection/hover/prompt/report, exports, history persistence/deletion, reduced motion and screenshots. Execution still requires a capable host.

No live paid-provider call, production deployment, legal compliance certification, trademark clearance or pixel-accuracy score is claimed.
