# VEYRA AI V0.4.2 verification — 30 October 2026

Baseline: V0.4.1 `531b0298dff3873259eb1f9dc3182195d6ea53ff`, verified against the fetched remote V0.4.1 branch. Working source was clean before branching to `feature/v0.4.2-blue-hour`. This report covers the available Work runtime, not the owner's live Codespace.

## Storage and baseline

Phase-zero audit preceded feature development. Total volume: 33,770,192,896 bytes. Available space changed from 29,459,533,824 to 29,461,598,208 bytes, recovering 2,064,384 bytes (~1.97 MiB) of allocated space. More than 87% remained free, exceeding the 50% target. The guarded cleanup removed untracked frontend build output, pytest cache and Python bytecode caches. Source, tracked archives, uncommitted work, secrets, Git, required dependencies/browsers, databases and backups were preserved.

The owner's Codespace is not mounted. No claim is made that its full disk has been cleaned remotely. The packaged read-only storage audit and guarded cleanup command can be run there. See `docs/v042/STORAGE_REPORT.md` and the exact machine-readable before/after report.

V0.4.1 service was rebuilt and started after cleanup, with its exact commit on private localhost port 8001. It correctly reported `browser-unavailable` in this runtime; production Chromium startup was not relabelled as successful. Baseline tests: **336 Python passed, 22 skipped**. Existing JavaScript suite: **63 passed** before the new tests.

## Final automated results

- Full Python run with explicit offline UI runner: **344 passed, 22 skipped, 0 failed; one inherited warning; 76.82s (0:01:16)**.
- JavaScript/React/collector suite: **66 passed, 0 failed**.
- Production frontend build: passed. Vite/Rolldown emits non-fatal third-party `use client` directive warnings for Motion; this app is a client-rendered React application.
- Shell syntax, Python compilation and whitespace checks: passed before packaging.
- Production npm audit: zero reported vulnerabilities at the checked registry response; not a security certification.

The inherited Starlette/httpx deprecation warning remains. Protected production browser/public-site tests remain skipped, as distinguished below.

## New real-browser acceptance

Both HTML/CSS/JavaScript and React paths passed the complete workspace scenario using the built app, real FastAPI, fixture inspection and actual browser rendering:

- Official optimized logo loaded; root background is Blue Hour Midnight. The original blue source button remained `rgb(37,99,235)`, separate from host branding.
- Inspector maximized fallback retained hover outlines, click-to-select and the selection overlay. Escape exited without losing the selection.
- Editor fullscreen retained file explorer, CodeMirror editing and edited code. Preview fullscreen retained the sandboxed interactive frame. A separate test exercised **native Fullscreen API entry/exit for all three modes** without relaxing app CSP.
- Source-ID click-to-edit navigated to unique HTML/JSX markers and selected the actual opening-tag range. Normal preview interaction remains separate; unsupported/duplicate markers do not guess by visible text.
- Compare displayed the real original session beside the generated iframe. Matching to 390×844 resized the remote viewport without navigation; generated viewport width was independently checked as 390 CSS pixels. Comparison fullscreen and Escape passed. Original and generated scrolling remain independent; optional sync is intentionally one-way delta forwarding, not a claim of precise page-section alignment.
- Draft/checkpoint save, full refresh restoration, explicit restore confirmation/cancellation and original-generation checkpoint retention passed. A separate two-tab test verified that a newer saved draft is not overwritten and that the current unsaved editor remains intact.
- Compiler failures reached the console. Preview warnings were bounded/redacted; a forged message with the wrong token was rejected. A separate runtime/asset case verified a thrown JavaScript error and failed data-image load in the console. Instrumentation registers before markup to capture early asset failures.
- Focus shortcut and Escape passed. Native/fallback fullscreen, reduced-motion operation, tablet/mobile layouts and absence of page overflow were checked at 1440, 1024, 768 and 390 widths.

Additional unit/API tests cover stable-ID mapping ambiguity, exact autosave round-trip and storage bounds, corrupt/blocked storage without replacement, actual stage sequences, bounded progress records, request-ID validation, viewport bounds/client headers and unique per-render bridge tokens.

Existing end-to-end export tests still compile and independently serve downloaded vanilla and React projects, verify edited styling, keyboard undo/redo, reset/restore and failure preservation. Existing V0.4.1 measurement/comparison/repair tests remain; host styles and Motion are not imported into those generated projects.

## Progress, security and resource behavior

Progress events are recorded at actual inspection/analyzing/generating/validating/rendering/refining boundaries. Refining appears only if a repair occurs; the final response supplies actual recorded stages. No percentages or timed fake completion stages are used. Polling permits one outstanding status request and ends with the operation. Progress entries expire and are capped at 32.

Draft storage is limited to 2 MiB and five snapshots plus current/original code. Console storage is capped at 80 entries with truncation/redaction; instrumentation limits total emitted events to 300 per document. Host handlers verify the active iframe window and opaque origin; instrumented events also carry a per-render token. These messages can display diagnostics/navigate code, not call privileged backend operations. Because generated code shares its own instrumented realm, a token does not prove that every diagnostic is truthful. No stronger authenticity claim is made.

Existing SSRF/address policy, isolated source browser, sandbox response headers, API-key handling, provider consent, quotas, project payload bounds, compiler timeout and context cleanup remain. The preview is still a private development sandbox, not a VM or complete CPU/navigation firewall. Keep forwarded ports private.

## Branding and dependency review

Central tokens exactly match #081529, #162B4B, #294C85, #4B7FCF and #A7CEFF, with the supplied gradient. The user's JPEG is the authoritative logo: the monogram region was cropped and proportionally resized to a ~2.9 KiB WebP; a PNG favicon was derived without redrawing/recoloring. The reference raster remains a source asset. Its original sage color is intentionally preserved independently from Blue Hour UI colors. No replacement logo was generated.

Motion 14.8.0 core was selected after checking official documentation, installed MIT license and React 18/19 peer support. Shared timings and reduced-motion rules cover host feedback; there is no premium animation asset dependency. See docs/MOTION_V042.md.

## Explicit unverified items and limits

- No live external model request was executed; tests use local reconstruction and injected provider responses. Existing live-provider configuration remains required to verify cloud generation/refinement/repair.
- No fresh Docker Compose firewall/protected-browser startup or owner Codespace restart was executed here. Official protected Chromium is unavailable in this runtime. The offline UI runner uses a separately supplied test binary without OS sandboxing; that is not production isolation evidence. Production source continues to require its protected browser/gateway.
- Representative viewport tests are not tests on a physical Samsung tablet or every mobile browser. Native fullscreen can be refused; the maximized fallback remains available.
- Mapping covers unique retained data-node IDs in HTML/JSX. Arbitrary provider output, dynamically created unmapped nodes and duplicate IDs remain explicitly unsupported. Original-site access restrictions are preserved.
- One-way scroll synchronization can differ when original and generated document structures/heights differ. No automatic section-to-page alignment or pixel identity is claimed.
- Draft recovery depends on the same browser origin and available storage. Pausing autosave is an in-session control; after refresh autosave is enabled again. Browser eviction, blocked storage and closing before debounce can lose unsaved edits; exports remain necessary backups.
- Console redaction is best effort for source text, not a complete PII/secret classifier. No provider credential enters preview source. Fullscreen-local shortcuts cannot override all browser/iframe shortcuts; visible buttons remain available.

## Delivery checks

The release generator supplies complete source (including official raster assets), Git bundle, hashes and an incremental updater for the exact V0.4.1 baseline. It tests baseline application, byte checks, idempotence, preservation of an unrelated note and local test secret, and conflict refusal. No caches, virtual environments, dependencies, browser binaries, runtime databases or secrets belong in the ZIP. Remote push outcome and exact commit are reported separately; no deployment is implied.

Remote push was attempted and rejected because GitHub Git credentials are unavailable in this runtime (terminal prompts disabled). The feature commit is local and included in the verified bundle; no remote V0.4.2 branch or deployment is claimed. Final bundle checks corrected an inherited packaging branch-name reference before release.
