# Architecture and interaction contract

React/Vite builds static assets served by FastAPI. REST is sufficient for deliberate screenshots; WebSockets/streaming would add complexity without improving V0.1 selection reliability. The client never embeds an arbitrary website iframe or directly reads a cross-origin DOM.

One Playwright Chromium process owns up to two isolated contexts. A context's network runs through a local authenticated, validating egress proxy. Request routing blocks unsupported resources/methods as a second layer. The exact host allowlist remains mandatory because no host firewall isolation was verified.

## Operations

Every write request uses `X-Veyra-Client: inspector-v0.1` and JSON if there is a body. No cookies or backend URL configuration are required. Session tokens are capabilities; do not share them.

| Method | Path after `/api` | Body / result |
|---|---|---|
| GET | `/health` | Browser readiness, safe startup detail, allowed hosts |
| POST | `/sessions` | `{url, viewport:{width,height}}`; returns `sessionId`, frame and null inspection |
| DELETE | `/sessions/{id}` | Idempotent close |
| POST | `/sessions/{id}/select` | `{frameId,x,y}` → fresh frame and Inspection |
| POST | `/sessions/{id}/scroll` | `{frameId,x,y,deltaY,deltaX}` → fresh frame, clears selection |
| POST | `/sessions/{id}/hover` | `{frameId,durationMs,intervalMs}` → observed Inspection and fresh frame |
| POST | `/sessions/{id}/refresh` | Screenshot only; clears selection |
| POST | `/sessions/{id}/reload` | Navigates current approved URL again; clears selection |
| POST | `/sessions/{id}/clear` | Disposes handle, moves pointer to corner, refreshes screenshot |

A frame contains `frameId`, data-URL `image`, remote `viewport`, `url`, `scroll`, `deviceScaleFactor:1`, `coordinateSystem:"viewport-css-pixels"`, and network warnings. Operations within a session are serialized; overlapping requests are rejected instead of queued. A frame ID rejects requests targeting a previous screenshot. This prevents stale client responses, not movement that occurs autonomously within a webpage.

The backend retains an ElementHandle until selection, navigation, scrolling, expiry or clear. The exported `referenceId` describes that active session reference; it is not a reusable global selector. Detached/replaced elements fail instead of falling back to a possibly different selector.

## Coordinate convention

All hit-tests and rectangles use **remote viewport CSS pixels**, top-left origin. With an image content rectangle `(left,top,displayWidth,displayHeight)` and remote viewport `(W,H)`:

`x = (clientX - left) × W / displayWidth`

`y = (clientY - top) × H / displayHeight`

The frontend measures the image itself, without borders/padding, keeps its intrinsic aspect ratio, and clamps to `[0,W)` / `[0,H)`. Backend screenshot uses `scale="css"`, viewport-only capture, context DPR=1. Client DPR is irrelevant. Do **not** multiply by the tablet's devicePixelRatio.

`document.elementFromPoint(x,y)` and `getBoundingClientRect()` both use viewport coordinates, so do **not** add `scrollX/scrollY` to either. Source scroll offsets are recorded separately. Overlays use `x/W`, `y/H`, `width/W`, `height/H` percentages, clipped to the image. On frontend resize these scale without changing the remote viewport. Changing the remote viewport starts a new context and clears selection.

Open shadow roots are traversed during hit-testing. Closed roots remain opaque. V0.1 returns the iframe element and an explicit content-inspection limitation, for both same- and cross-origin frames. SVG DOM elements are supported where browser hit-testing returns one; canvas/WebGL return their DOM container.

## Hover

Pointer first moves to the viewport corner; the code waits 250 ms and records the baseline. The selected element is brought into view if necessary. The element's center must be unobscured. The mouse moves there and computed style/geometry samples are scheduled with a monotonic clock. Screenshot and browser work can delay samples, so actual elapsed times and requested interval/duration are separate.

If the corner still hovers the element, the baseline is explicitly flagged. The implementation does not inject CSS to suppress hover and does not promise to reset arbitrary prior JavaScript state. It compares sampled styles and geometry to the baseline. Before, midpoint and final screenshots provide evidence; a numerical pixel-difference algorithm and animation-source reconstruction are not implemented. Hover remains active after capture so the returned rectangle/styles match the final state as closely as successive observations permit.

## Implementation references

- [Playwright browser contexts and request routing](https://playwright.dev/python/docs/api/class-browsercontext)
- [Playwright network guidance](https://playwright.dev/python/docs/network)
- [Playwright Docker: non-root user and Chromium sandbox profile](https://playwright.dev/python/docs/docker)

These references informed implementation choices. The delivery test report, not documentation, determines what was actually verified in this environment.

## V0.2 changes (supersede V0.1 network/startup descriptions above)

The public path uses a separate Node Playwright launchServer and a dedicated egress gateway. The Python client attaches without `expose_network` so it never bridges its own private network into the browser. Full Chromium is explicitly selected on both paths, sandbox enabled. The browser's kernel OUTPUT firewall enforces the gateway as its only new outbound TCP destination. The server control path is unguessable and never host-published. The app checks trusted readiness metadata before attaching. Container behavior was not verified here.

`POST /api/normalize` accepts `{url}` and returns the canonical URL. The frontend uses this one authoritative normalizer; `POST /sessions` also applies it through the network policy. `POST /api/browser/retry` retries the engine only when live sessions can be preserved; stale disconnected contexts are first disposed. `/health` adds `version`, `networkMode` and structured startup diagnostics.

Frames add a `diagnostics` object. Errors may add `code` and safe `diagnostics`; existing `detail` is preserved. Inspection schemaVersion remains 0.1 and the selection-coordinate convention is unchanged. New diagnostic categories include navigation-timeout, website-blocked-or-inaccessible, loaded-empty, screenshot-failure, response-transfer-failure and browser-engine-failure. No computed values are synthesized.

Readiness waits up to 5 seconds for content and a bounded network-quiet period, with a minimum 2-second early-success window and a bounded font wait. Canvas/SPA readiness remains heuristic. CSS/CSP/access-control enforcement remains enabled. Console CSP errors are categorized without exporting raw console text.

## V0.3 extension

The existing same-origin API adds `/api/prompts/generate`. `prompts/evidence.py` and `collect.js` collect a minimized, bounded server-owned snapshot from the retained selection or visible body. `deterministic.py` renders the measured eight-section prompt; `service.py` enforces generation admission and fallback. `provider.py` optionally sends reduced JSON to a configured compatible HTTPS chat endpoint through the existing validated egress proxy, then appends labelled interpretation. No provider key or raw inspection object is accepted from the frontend.

`PromptPanel.jsx` extends the current screen below the workspace; existing selection/export controls remain. It sends references/preferences, provides a controlled editable textarea, copy fallback, stale-draft clearing and duplicate-request protection. No frontend HTML renderer or code execution is introduced. See [PROMPTS.md](PROMPTS.md).

## V0.3.1 precision pipeline

The attached V0.3 architecture is retained. `boundary.js` supplies scored local-container decisions to the existing collector through evidence.py's source assembly. The collector preserves bounded geometry/DOM semantics, records sibling order and pins the selected ancestry. `selection.py` is shared by sanitized byte admission and detail selection, retaining complete captured paths and reporting omissions. `style_groups.py` factors exact equal sanitized properties with reversible per-node references. The deterministic renderer organizes those measurements and labelled recommendations under the existing eight numbered sections.

Public prompt/inspection schemas stay 0.3/0.1; internal 0.3-evidence gains optional metadata consumed by the same provider serializer and renderer. The provider, browser manager and isolation stack do not change. The frontend changes help/version text only. See [V031_ACCURACY.md](V031_ACCURACY.md) for budgets, compatibility and limitations.
