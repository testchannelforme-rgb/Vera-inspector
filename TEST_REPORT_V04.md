# VEYRA AI V0.4.0 verification — 30 October 2026

Baseline: V0.3.3 `08b804c71eadd9e324cf04581572e19d609f0f89`. Target: `feature/v0.4-code-studio`. This report describes this runtime, not the owner's live Codespace.

## Baseline recovery

Inspected all six repository branches and V0.3.3's two commits, the saved V0.3.3 review ZIP, startup scripts, source, dependencies and disk. The remote V0.3.3 branch has both implementation (`4b5599b`) and follow-up verification (`08b804c`) commits. Its source is present; this does not establish that an older Codespace applied or served it. A clean checkout was used; no owner uncommitted files or secrets were accessed/deleted.

Baseline rerun: **309 Python passed, 22 skipped; 60 JavaScript passed; production build passed**. The inherited report records broader tests on the prior Codespace; those historical counts are not substituted for current verification.

Found and corrected the mismatch between local startup/origin/devcontainer port 8000 and Compose's host port 8001. Both V0.4 launch paths now identify 8001. Local startup rebuilds checked-out frontend source and refuses an occupied port; no process is killed. Health reports `0.4.0`, source commit, dirty status and separate browser availability.

## Current executed tests

- Complete Python suite with the explicit offline UI runner: **328 passed, 22 skipped, 0 failed**, 31.95 seconds. One inherited Starlette/httpx deprecation warning.
- Same protected-engine/default run without the optional UI runner: **325 passed, 25 skipped, 0 failed**. The extra three skips are the opt-in offline Code Studio browser cases.
- JavaScript/React/collector suite: **63 passed, 0 failed**.
- Production frontend build: **passed**. Main initial bundle approximately 265 KB / 83 KB gzip; Code Studio and CodeMirror/language packages split into deferred chunks. Full output is approximately 0.9 MB. No Monaco, provider SDK, browser WASM compiler or new Chromium installation is shipped.
- Production npm dependency audit: **0 reported vulnerabilities** (current registry response; not a security certification).
- Guarded installer candidate: **passed** exact-baseline application, byte checks, idempotence, secret/unrelated-file preservation and conflict refusal.
- Python syntax compilation, shell syntax checks and `git diff --check`: **passed**.
- Local real `start.sh` smoke on **8001**: **passed** for backend + built frontend, correct V0.4 health, source identity and intentional `browser-unavailable` state. Duplicate local startup refused the occupied port. This does not count as a successful protected browser startup.

Backend coverage includes inspection-reference-only admission, stale frames, missing consent/credentials, independent model configuration, injected provider success/failure/timeout handling, usage propagation, schema/path/size limits, unsafe imports, syntax errors, non-evaluation of top-level generated JS, metadata safeguards, refinement merge/preservation, context expiry, request headers, durable quotas, unmetered renders, bounded preview storage and sandbox response policies. Existing URL/SSRF/egress/prompt tests remain in the suite.

JavaScript and browser coverage includes exact current-file ZIP bytes, copy/download, file switching, format/scope controls, editor loading/editing, panel layout, viewport presets, draft preservation, reset/restore, diagnostics, and request-failure handling. Diagnostic checks report missing mapped nodes, dimensions, font-size, color and overflow without inventing a pixel accuracy score.

## Offline end-to-end acceptance — passed for both outputs

Actual built React UI + FastAPI + existing inspector/collector + bounded local HTTP fixture:

1. Open fixture through the inspection session and real screenshot.
2. Select its button through screenshot coordinates.
3. Generate an existing V0.3.x prompt from that selection.
4. Generate vanilla or React implementation from collected evidence.
5. Load files in actual CodeMirror and render the real sandboxed iframe.
6. Change CSS and observe the changed button color in the preview.
7. Copy current code and download the actual ZIP.
8. Extract it; independently serve vanilla output, or run the exported React `npm run build` and serve its dist. Both rendered the edited color.
9. Introduce invalid JS/JSX; show a compiler error while retaining current code. Reset and restore preserved the previous edits.
10. Check desktop/tablet/mobile widths (1440, 1024, 768, 390), tabs and no horizontal page overflow.

A separate real browser security test confirmed that preview scripts could not access the parent DOM, read localStorage or fetch the host API. The parent page and stored host test value remained intact.

**Runner distinction:** the optional offline test runner uses a separately supplied Chromium binary without an OS sandbox because this host lacks the necessary process capabilities. Its exact local fixture exception is test-only; production `BrowserManager` still requires `chromium_sandbox=True` and the existing policy/gateway. These tests prove workflow/browser CSP behavior, not production browser-process isolation. No public website was inspected through that test-only runner.

## Not executed / limitations

- Protected production Chromium startup here: **unavailable**. The matching official browser download repeatedly returned invalid/truncated archives. Production browser tests skipped; no sandbox protection was weakened to make them pass.
- Fresh Docker Compose build/firewall readiness and actual owner's Codespace restart: **not executed**; Docker is unavailable in this runtime.
- Live external AI-provider request: **not executed**; no credentials were supplied. Provider contracts/failures were tested with injected deterministic responses. Local reconstruction is explicitly identified and is not evidence of a live model response.
- Public-site V0.4 acceptance: **not executed** in this host. Existing opt-in public test remains skipped.
- Screenshot pixel similarity, full animation keyframe recovery, unknown navigation/backend interactions, original asset URLs/fonts and multi-element selection: **not implemented**. Available DOM fidelity diagnostics are indicative.
- Preview has opaque-origin/CSP isolation, not a VM, browser CPU kill switch or complete network-navigation firewall. Resource/fetch access is blocked; arbitrary code can still attempt self-navigation or consume browser CPU. A separate hardened preview origin/container is required before a public hostile-code service.
- Allowances are server-owned but deployment-wide for one private operator; no account system, verified paid subscription or payment flow exists. Hosted-preview limits are reserved configuration; local rendering is unmetered.

## Disk and packaging

Workspace initially: 32 GB volume, about 543 MB used / 30 GB available. After dependencies and QA browser tools: about 1.5 GB used / 29 GB available. The actual owner's Codespace is not mounted; no claim is made about its free-space percentage. Only disposable local caches/build output are eligible for the supplied cleanup command; tracked old ZIPs, source, history, dependencies, secrets and backups are retained.

The release generator excludes dependencies, virtual environments, caches, secrets, old ZIPs and QA screenshots. It carries complete source plus an incremental update with exact-baseline content, checksums, three-way conflict handling and replacement backups. Its built-in checks apply the update to a clean baseline, verify all updated bytes, recheck idempotence, preserve a local test secret/unrelated note, and refuse a conflicting local source edit. These installer checks passed on the review package; the release generator repeats them on the final package. No force overwrite is used.

## Source delivery

The connected GitHub integration returned HTTP 403 (`Resource not accessible by integration`) for source creation. No remote V0.4 commit, branch or deployment is claimed. The release contains the locally committed feature branch in a verified Git bundle, full source, and the tested incremental installer. Import the bundle to retain the exact commit identity.
