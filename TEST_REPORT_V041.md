# V0.4.1 verification — 30 October 2026

Verified source baseline: `1c885d0a7b1419fd972edec896a08c13b28f90a5` (also fetched as the remote V0.4 branch). This is an incremental quality update, not a rebuild.

## Diagnosis from code

V0.4 selected local deterministic reconstruction by default; AI was optional and not secretly invoked. It did not silently substitute templates after failed AI requests. However, the UI did not explain configured-vs-live provider status clearly. The Free context was reduced to 24 of 55 collected nodes. The seed generator discarded source asset references, suppressed animation names without keyframes, normalized root positioning, used a guessed mobile breakpoint, and left the canvas white when the captured region inherited a dark ancestor background. The vanilla preview sanitizer discarded inline style attributes. AI inherited a 1500-token default / 2500-token maximum, small for complete projects. The V0.4 UI retained violet/blue branding; this was incorrect for the approved Charcoal/Sage identity.

## Corrections

The reconstruction/2 contract now passes structured hierarchy, measured boxes, full collected styles, paint context, hover evidence, coverage and explicit unknowns. Both plans retain the collector's 55-node maximum; existing redaction, ancestor selection and byte limits remain. Top/left/right/bottom, outlines and additional text/layout CSS are collected. Root crop coordinates are normalized; descendants keep measured offsets/flex/grid. Transparent roots get the observed ancestor canvas color. No new breakpoint is presented as observed.

Already-loaded, origin-clean raster images may be embedded within a 64 KB budget, 512px dimension limit, strict base64/PNG validation and the existing 180 KB project cap. CORS-tainted images remain missing. Safe inline styles survive vanilla preview. Font family/type metrics remain measured; external font binaries/SVG/background-URL extraction are not claimed.

Code/refine/repair tasks use independent model settings and 8192-token default output budgets, bounded to 12000. Prompt-task budgets remain unchanged. The UI reports not-configured/configured-not-probed and labels local generation honestly. No key or provider was supplied in this environment; no live AI inference is claimed. AI/repair success is represented with its actual selected model; repaired local seeds are not labelled as having made no AI call.

Comparison captures a local reference crop and renders the generated project at the same viewport using the existing browser. All preview rendering network routes except the synthetic document are blocked. It compares pixels and mapped DOM nodes, dimensions, styles, overflow and runtime errors. Screenshot data is operation-local, never sent to AI, and never written into exports. One optional repair uses one refinement allowance and requires explicit consent. It must compile, lower combined discrepancy, have no runtime errors and introduce no additional missing mapped nodes; otherwise the previous valid project is retained. The editor allows up to 120 seconds for this bounded multi-stage request; individual compiler/model/render bounds remain.

## Executed results

- Complete Python suite with explicit offline test runner: **336 passed, 22 skipped, 0 failed**, 50.23 seconds; one inherited Starlette/httpx deprecation warning.
- JavaScript/React/collector suite: **63 passed, 0 failed**.
- Production frontend build: passed.
- Separate five-fixture/repair/brand suite: passed; included real screenshot/geometry comparison, with an injected model contract (not a cloud inference).
- Existing full UI/export cases: passed for vanilla and React, including screenshot-coordinate selection, prompt generation, CodeMirror edits and undo/redo, preview CSS update, copy, ZIP, independent exported-project build/serve, reset/restore, invalid-code preservation and responsive layouts.
- Exact brand assertions: app root background `rgb(46,49,56)` and primary button `rgb(168,184,154)`. Theme tokens are `#2E3138` and `#A8B89A`. Source-site colors remain unchanged in generated projects. Semantic red error colors and neutral editor colors are intentional; no violet-blue brand hex values are retained in the application stylesheet/logo assets.

## Measured before/after

Same collected evidence, viewport and source fixture for both generators; V0.4 generator loaded from the baseline Git commit. Rendered using the same offline preview renderer. Pixel mean absolute channel error ranges 0–255, lower is better; this is **not an accuracy percentage**. Geometry is root-relative mean absolute box error in CSS pixels. Raw reports are in `docs/v041/`.

| Fixture | V0.4 pixel MAE | V0.4.1 pixel MAE | V0.4 / V0.4.1 geometry MAE |
|---|---:|---:|---:|
| Navigation | 0.000 | 0.000 | 0 / 0 |
| Hero with layered decoration/image | 186.831 | 0.000 | 0.002 / 0.002 |
| Card grid | 118.920 | 0.000 | 0.007 / 0.007 |
| Responsive section at captured viewport | 202.682 | 0.000 | 0 / 0 |
| Gradient/motion/native disclosure | 0.104 | 0.104 | 0 / 0 |

These results were identical for vanilla and React. Improvements here primarily recover inherited canvas backgrounds and bounded asset mapping; they do not demonstrate better geometry on already-correct fixtures or universal website recreation. The responsive fixture includes CSS breakpoints but the test captures one desktop viewport; recovery of the original breakpoint is not claimed. Animation timing/keyframe recovery is not proven by static screenshots.

A separate real-render test deliberately injects incorrect model CSS, compares its screenshot, applies a targeted injected model correction, and asserts lower loss before acceptance. Unit tests also reject higher-loss repair and malicious page-supplied asset strings. No perfect-pixel claim extends beyond these deterministic fixtures.

## Security/deployment limits

The offline acceptance runner is explicitly configured using a separate test Chromium binary without its OS sandbox on this restricted host. Production browser source still requires the original protected Chromium/gateway; no security flag was relaxed in production. The 22 inherited skips concern the unavailable protected engine or opt-in public site. No fresh Docker Compose startup, owner Codespace restart, external font recovery or real provider request was executed here.

The UI preview remains the inherited opaque-origin/CSP development sandbox, not a VM or complete CPU/navigation firewall. The offline server-renderer adds request blocking and time bounds, but public hostile-code hosting still requires stronger deployment isolation. Keep forwarded ports private.

Menus, arbitrary dropdown/tab application logic, offscreen scroll triggers, original navigation targets and unavailable CSS animation keyframes are not guessed. Native disclosure and captured hover CSS remain supported. Missing assets and single-viewport observation limits remain explicit. No new GPU, paid API, provider SDK or duplicate Chromium is required. Pillow is the only new Python dependency, used for bounded image comparison/validation. Disk remains about 29 GB free here; the owner's Codespace disk is not mounted.

The final package includes source, a Git bundle, checksum manifest and guarded incremental installer. The package generator verifies baseline application, idempotence, unrelated/secret preservation and conflict refusal. Remote push status is reported separately; no GitHub upload is inferred from a local commit.

Remote push was attempted and failed: GitHub Git credentials are unavailable in this environment (terminal prompts disabled). The feature commit is local and included in the Git bundle; no remote V0.4.1 branch or deployment is claimed.
