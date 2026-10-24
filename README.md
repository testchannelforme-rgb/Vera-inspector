# Veyra Inspector V0.1

A React + FastAPI + Playwright prototype for screenshot-based inspection of real public websites. No AI keys, paid APIs, database, or account system are required.

**Delivery status: source implemented, browser acceptance incomplete.** The build and non-browser tests ran here. This execution host prevents sandboxed Chromium startup. Navigation, screenshot selection, hover, exported real inspection examples, and UI screenshots therefore remain unverified. No Codespace or public deployment was created. Read [TEST_REPORT.md](TEST_REPORT.md) for the exact results.

## Start in GitHub Codespaces from an Android tablet

Use a private repository and keep the forwarded port **Private**. Codespaces use is subject to your GitHub account's included quota; stop the Codespace when finished. Do not enable paid usage for this project.

### Option A: upload the extracted project

1. Extract the ZIP using your tablet's file manager.
2. Create a new private GitHub repository. Upload the extracted contents at its root: `README.md`, `backend`, `frontend`, `scripts`, and **`.devcontainer`** should be directly inside the repository. Include files whose names start with a dot.
3. Choose **Code → Codespaces → Create codespace on main** in your tablet browser. Wait for the container and dependency setup to finish.
4. In its terminal, run this single command:

```bash
bash start.sh
```

5. Open **Ports**, find **8000 / Veyra Inspector**, and choose **Open in Browser**. Keep the terminal running.
6. Start with `https://example.com`. Click **Open website**, then tap a visible element. The inspector shows the actual DOM evidence when Chromium is available.

### Option B: upload only the ZIP first

GitHub does **not** extract uploaded ZIPs. In a new repository containing `Veyra_Inspector_V0.1.zip`, create a standard Codespace, then run:

```bash
unzip Veyra_Inspector_V0.1.zip
```

The ZIP has no enclosing folder: it extracts the project files at the current repository root. Then open the command palette (**F1**, or the menu) and choose **Codespaces: Rebuild Container** so `.devcontainer/devcontainer.json` is applied. After setup, run `bash start.sh`.

Do this in a new repository; don't extract over unrelated work. The container configuration is supplied but was **not tested in Codespaces** during this delivery.

## Local Linux/macOS development

Requires Python 3.11+, Node 22.12+ (or Node 24), npm, and a sandbox-capable Chromium host. Linux must support Chromium namespaces; run the app as a normal user. For Debian/Ubuntu system libraries, the first setup command can use sudo:

```bash
bash scripts/setup.sh --system-deps
bash start.sh
```

On macOS use `bash scripts/setup.sh`, without `--system-deps`. Open `http://127.0.0.1:8000`. On subsequent starts only `bash start.sh` is needed. That command also installs missing project dependencies on a suitable existing host. System libraries may still require the explicit first-time setup command above.

`start.sh` uses one Uvicorn worker, one Chromium process, and isolated browser contexts. It serves the Vite production build and `/api` from the same origin. Only port 8000 is needed; browser code contains no hardcoded backend host. The exact Codespaces UI origin is derived from its environment variables if its forwarding proxy rewrites the Host header. Other trusted reverse proxies can set `VEYRA_UI_ORIGIN` to their exact browser-facing origin. No permissive CORS or WebSocket streaming is necessary. REST operations return screenshots only when requested.

For frontend hot reload, run these in separate terminals:

```bash
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --port 8000 --no-proxy-headers
npm --prefix frontend run dev
```

The Vite development proxy handles `/api`. Prefer the single-port build in Codespaces. Rebuild frontend source changes with `npm --prefix frontend run build` before restarting the single-port app.

## Using the inspector

- **Open website** starts a fresh, private remote browser context. Switching viewport takes effect on the next Open.
- **Tap/click the screenshot** selects an element; it does not click a remote link or submit a form. The border is based on the actual element rectangle.
- **Swipe, wheel, or use Scroll** to scroll. A swipe/wheel targets the element under the pointer, so nested scrolling containers work when unobscured. Selection clears after scrolling.
- **Refresh image** takes another screenshot and clears selection. **Reload** reloads the actual page.
- **Styles** groups computed appearance, typography, layout, and animation properties. It includes best-effort accessible name/role, pseudo-elements and up to 100 CSS variables.
- **HTML** displays sanitized text evidence, never executable website HTML. Text and snippets have documented size caps.
- **Motion → Capture hover** moves the remote mouse to the selected element's visible center. It records a baseline, requested 100 ms samples for 1 second, actual timestamps, styles/geometry changes, active animations, and before/during/after screenshots. No destructive remote click is sent.
- **Export JSON / Copy JSON** uses the real response, including hover images if captured. Clipboard requires a secure context; use Export if unavailable.
- **Clear** releases the element handle. **Close** closes the context. Tab-close cleanup is best effort; idle/absolute expiry also runs server-side.

## Allowed sites and security

The default allowlist is exactly `example.com,www.example.com`. This is intentional: **V0.1 is a private development tool, not an unrestricted public URL-fetching service.** It has no user authentication. Do not publish it publicly or put secrets into its browser contexts.

To inspect another reviewed public host, stop the server and set an explicit allowlist before restarting:

```bash
export VEYRA_ALLOWED_HOSTS='example.com,www.example.com,your-reviewed-public-host.com'
bash start.sh
```

Replace that last hostname with the real approved host. Redirect destinations and CDN/resource hosts need their own explicit entries. No wildcards or switch for accepting all public sites is provided. Blocking required resources can change the appearance; the UI reports blocked requests. Do not use authenticated pages or bypass website access controls.

A local authenticated egress proxy validates destinations and pins each outbound HTTP/TLS connection to a validated numeric IP. The browser also applies request policies. Chromium's sandbox stays enabled. **This is not host-level network isolation.** See [SECURITY.md](SECURITY.md) for residual risks, resource limits, and the test-only local-site exception.

## Tests and real artifacts

From the repository root:

```bash
bash scripts/test.sh --public
```

This builds the frontend, runs Node and pytest checks, and runs a strict browser-startup probe. It exits nonzero if Chromium cannot launch, even when unit tests pass and browser-dependent tests are reported as skipped. `--public` enables actual inspection of `https://example.com` after browser startup; it does not substitute the local fixture for a public site.

Browser tests cover a deterministic local HTTP fixture, navigation, screenshot generation, real DOM hit-testing, CSS extraction, hover, nested scrolling, SVG/open shadow roots, blocked subrequests/redirects, cleanup and a complete tablet UI → API → browser → JSON export flow. The local exception exists only in test code; there is no production environment flag that allows private URLs.

After successful real browser tests, `artifacts/` receives `local-inspection.json`, `hover-inspection.json`, `public-inspection.json`, `public-website.jpg`, `ui-export.json`, `veyra-tablet.png`, and `veyra-mobile.png`. **These evidence files are absent from the delivered ZIP because those tests could not run here.** No fabricated inspection output or screenshot is included.

Other commands:

```bash
.venv/bin/python -m pytest -q -rs                # unit + local browser tests
npm --prefix frontend test                     # coordinate conversion
PYTHONPATH=backend .venv/bin/python scripts/check_browser.py
PYTHONPATH=backend .venv/bin/python scripts/export_schema.py
```

## Troubleshooting

- **Browser unavailable / running as root / no usable sandbox:** run as `vscode` in the supplied devcontainer, rebuild it, and check the namespace/seccomp support of the host. The provided profile permits Chromium's namespace syscalls without disabling its sandbox. Do not add `--no-sandbox`, disable web security, or ignore certificate errors. If the host denies namespace creation regardless of container configuration, use a host that supports it.
- **Chromium executable missing / browser download fails:** rerun `.venv/bin/python -m playwright install --no-shell chromium`. A proxy/firewall may block the download host. The delivered source pins its Playwright version; don't mix a different version's browser binaries.
- **Missing Linux libraries:** run `bash scripts/setup.sh --system-deps`.
- **Frontend unavailable:** run `npm --prefix frontend ci` then `npm --prefix frontend run build`, and restart the backend.
- **Host not allowed / network blocked:** review the exact host and public DNS results; allow only trusted public test sites. Blocking is deliberate, including after a redirect.
- **Old preview / element changed:** refresh and select again. Screenshots are successive observations, so continuously moving content can shift between capture and inspection.
- **Session expired/busy:** close another session or reopen the website. Default maximum: two sessions, 10-minute lifetime, three-minute idle expiry.
- **Canvas, WebGL, iframe content, closed shadow roots:** V0.1 reports the accessible outer DOM element and limitations. It cannot reverse-engineer pixel content or arbitrary JavaScript animation source.

## Repository guide

`backend/app` contains policy, egress proxy, browser lifecycle, extraction, hover, Pydantic schemas and FastAPI routes. `frontend/src` contains the responsive React interface and coordinate mapping. `backend/tests/fixtures` is the local test website. `.devcontainer` contains the reproducible container configuration. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) documents the API and coordinate system; [docs/SCHEMA.md](docs/SCHEMA.md) documents the versioned JSON format and its generated schema.

## Next priorities

1. Finish Milestone 01 browser acceptance on a supported host, including public navigation and tablet interaction; resolve any resulting failures before adding features.
2. Add enforced egress firewall isolation and per-session memory/transfer accounting before considering broader URL access.
3. Add more tested frame/shadow-root handling and animation-timeline comparison.
4. Only then use the versioned evidence as input to Milestone 02 prompt generation. Native apps, payments and generated code are outside V0.1.
