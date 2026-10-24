# Veyra Inspector V0.1 — delivery verification

Date: 24 October 2026 (IST).

**Milestone 01 is NOT complete.** Source for the prototype is implemented, but essential real-browser acceptance is blocked in this execution host. The report distinguishes code present from behavior verified.

## Actual execution results

| Check | Result |
|---|---|
| Frontend production build | PASS — Vite 8.3.5 built the real React source |
| Frontend coordinate tests | PASS — 6 tests, 0 failures |
| Backend unit/API/security/proxy tests | PASS — 50 tests, 0 failures |
| Browser-dependent pytest tests | BLOCKED/SKIPPED — 7 tests, including the public site and tablet UI flow |
| Strict sandboxed Chromium startup probe | FAIL — root process cannot launch protected Chromium; host also prevents switching UID / creating a usable user namespace |
| Complete `bash scripts/test.sh --public` command | EXIT 1 — intentionally fails acceptance when Chromium cannot launch |
| Backend HTTP startup using `bash start.sh` | PASS with installed dependencies — real server returned health HTTP 200 and `browser-unavailable` |
| Frontend served by that running backend | PASS — real built index returned HTTP 200; static asset serving also passed API tests |
| Python module / browser extraction JS / shell syntax | PASS — compileall, node --check, bash -n |
| Devcontainer and JSON Schema configuration syntax | PASS — JSON parsed; container execution not tested |
| Frontend dependency audit | No known vulnerabilities reported by npm audit, including dev dependencies |
| Python runtime dependency audit | No known vulnerabilities reported by pip-audit for the pinned runtime dependency closure |
| GitHub Codespaces | NOT TESTED — no Codespace created or controlled |
| Public deployment | NOT PERFORMED |

Audits are point-in-time checks, not a security certification. pytest emitted one development-only deprecation warning about Starlette TestClient's httpx integration. TestClient API checks still passed.

Raw evidence is included in `artifacts/tests.log`, `artifacts/browser-probe.log`, `artifacts/server-smoke.json`, `artifacts/server-smoke.log`, and the two dependency-audit JSON files. Browser binaries, virtual environments and node_modules are not in the ZIP.

## Environment and startup blocker

The available environment has Python 3.12.14, Node 24.22.1, npm 11.9.0, Git 2.51.1 and file/execution access. There was no existing repository. Playwright and runtime/test dependencies were installed. Chromium was downloaded; the final pinned Playwright 1.64.1 Chromium binary was obtained from the official Chrome-for-Testing storage after the normal CDN returned empty/truncated downloads in this host.

Launching with `chromium_sandbox=True` fails with Chromium's explicit “Running as root without --no-sandbox is not supported” diagnostic. This host does not allow switching to a normal user or the required user namespace configuration. No `--no-sandbox` retry or web-security bypass was used. A fresh dependency setup also encountered an incomplete local driver file; the HTTP startup smoke check used the already-installed verified development environment. A clean Codespaces installation has not been verified.

The API remains usable for diagnostics and invalid-URL handling. The UI displays the startup error rather than a fake website. This does not satisfy inspection acceptance.

## Acceptance criteria

| Requirement | Status here |
|---|---|
| Frontend starts | Build and HTTP serving verified; interactive browser rendering unverified |
| Backend starts | Verified in graceful browser-unavailable state |
| Playwright launches Chromium | Failed in this host |
| Public test website opens in Chromium | Blocked before navigation; not verified |
| Real screenshot displayed | Implemented; unverified |
| Correct real element selected | Implemented with hit-test and ElementHandle; unverified |
| Real computed CSS returned | Implemented; unverified in Chromium |
| Accurate selection highlight | Conversion tests passed; actual browser overlay unverified |
| Actual hover observations | Implemented; browser test blocked |
| Inspection JSON exported | Implemented; real browser/UI export test blocked |
| Invalid/unsafe URLs rejected | Policy and API tests verified |
| Browser sessions cleaned up | Unit expiry/proxy cleanup verified; real context cleanup test blocked |
| Documented startup command | HTTP startup verified with prepared dependencies; fresh Codespaces setup unverified |

## Implemented source

- Exact-host URL/DNS policy plus a validating, authenticated local egress proxy that pins connections to vetted IPs.
- Browser manager with one Chromium process, isolated contexts, timeouts, concurrency/session/request budgets and expiry cleanup.
- Navigation, viewport screenshots, viewport hit-testing, shadow-root descent, internal element references, computed CSS grouping, geometry, safe HTML evidence, metadata and JSON schema 0.1.
- Baseline and timed hover sampling, style/geometry comparisons, actual timestamps, active animation timing/keyframes and before/midpoint/final screenshot capture.
- Responsive dark React UI, viewport selector, screenshot decoding/scaling, tap/pointer selection, clipped highlight, touch/wheel/basic button scrolling, inspection tabs, clear/close, reload/refresh and JSON copy/download.
- Codespaces devcontainer, pinned dependencies, setup/start/test scripts, deterministic local fixture, public example.com test and full UI acceptance test.

## Partial features and known limits

- Animation comparisons are computed-style/geometry comparisons. Images are captured evidence; numerical pixel-difference scoring is not implemented. Arbitrary JavaScript animation source is not recovered.
- Iframe contents and closed shadow roots are opaque; V0.1 reports the outer element and a limitation. SVG DOM nodes are inspectable where hit-testing returns one. Canvas/WebGL receive outer-element and available visual evidence only.
- Role/name is best effort, not the complete accessibility tree. Pseudo-elements/custom properties are bounded. Computed CSS is not original authored CSS.
- A moving/self-updating page can drift between screenshot and DOM extraction. Frame IDs detect outdated client frames, not independent animation movement.
- Hover baselines can still be hovered at the viewport corner and long earlier transitions can be unsettled. Such cases are flagged. Hover remains active after capture.
- Network filtering and a proxy do not prove host-level isolation. Exact-host allowlisting stays mandatory. No authentication, public-service protection, enforced per-session heap quota, or complete browser-network isolation is provided.
- Browser-backed examples and running-app screenshots are absent because their tests did not pass. The tests generate them only on success; no manufactured substitute is included.

## Not implemented / outside Milestone 01

Streaming remote video, iframe-content traversal, closed-shadow introspection, arbitrary page clicks or login, destructive actions, animation source reconstruction, numerical screenshot pixel comparison, AI prompt/code generation, account/payment systems, project management and native apps.

## Required next action and Milestone 02 priorities

1. On a sandbox-capable host, run `bash scripts/test.sh --public`. Fix any actual browser/UI failures it reveals. Verify the generated evidence and interact manually from the Android tablet. Do not declare Milestone 01 complete before this succeeds.
2. Add enforced egress isolation, credential separation, total transfer accounting and per-session resource controls before widening URL access.
3. Expand tested iframe/shadow support and animation comparison coverage.
4. After inspection acceptance is achieved, build Milestone 02 prompt generation using this versioned evidence. No paid AI service is needed for V0.1.
