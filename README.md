# VEYRA AI V0.4.0 — Code Studio

An incremental upgrade from verified V0.3.3 commit `08b804c71eadd9e324cf04581572e19d609f0f89`. Branch: `feature/v0.4-code-studio`. The existing React/FastAPI/Playwright inspection, URL policy, browser isolation and prompt engine remain.

Open a website, select an element or local section (or visible page), generate a prompt or code, edit files, render the recreation, and download a runnable project. Outputs: HTML/CSS/JavaScript and React/Vite. CodeMirror provides syntax highlighting, line numbers, indentation, bracket matching, completion, and keyboard undo/redo. The studio offers file switching, copy, ZIP download, original reset, ten project snapshots, viewport presets, an adjustable desktop split and tablet/mobile tabs.

## Start / update

Use Node 22.12+ or 24 LTS and Python 3.11+. Keep forwarded ports **private**; this is a single-operator development tool, not a public multi-tenant service.

```bash
bash scripts/setup.sh
bash start.sh --isolated
```

Public-site inspection requires Docker and the existing protected browser + validating egress gateway. The app is on **8001**, mapped to container port 8000. Do not disable the browser sandbox or URL/network policies. For restricted development with configured allowlisted hosts, use `bash start.sh` (also 8001). The Vite dev proxy targets 8001. Both paths rebuild the current frontend. Startup refuses an occupied local port and never kills unknown processes.

```bash
python3 scripts/verify-version.py http://127.0.0.1:8001
python3 scripts/clean-disposable.py
```

The cleanup command reports only disposable project caches/build output. Add `--apply` to remove those untracked artifacts. Dependencies, Chromium installs, archives, source, Git history, backups, secrets and user exports are excluded. Never promise a free-space percentage. The setup script preserves existing environment/dependency handling.

The GitHub integration rejected remote source writes (403); this release includes a locally committed Git bundle plus an incremental ZIP. Follow `V04_UPDATE.md`. The guarded installer checks/merges before writing, preserves unrelated files, backs up replacements, and refuses conflicts.

## Code generation and refinement

**Local measured reconstruction** works without credentials or a GPU. It maps existing redacted evidence into a semantic node tree with measured CSS, flex/grid properties, gradients, borders, safe pseudo-elements and captured hover endpoints. Missing assets become labelled placeholders. It is deterministic and never labelled AI output. It does not infer working backend actions, original navigation targets, unknown breakpoints, animation keyframes or unobserved scroll triggers.

Optional AI generation and targeted refinement use the existing HTTPS-compatible provider transport through the vetted egress gateway. Separate environment prefixes select independent prompt/code/refinement models. No provider SDK, paid account or mandatory API key is added. The operator must choose a provider with a suitable free tier if desired; Veyra cannot guarantee any provider's price or availability.

- Prompt task: existing `VEYRA_AI_*` settings.
- Code task: `VEYRA_CODE_AI_ENABLED`, `VEYRA_CODE_AI_MODEL`, `VEYRA_CODE_AI_API_KEY`, `VEYRA_CODE_AI_ENDPOINT` (plus optional `PROVIDER`).
- Refinement task: corresponding `VEYRA_REFINE_AI_*` settings.
- Existing timeout/token settings remain bounded (1–20 seconds, 128–2500 output tokens). Large generations can hit the limit and fail honestly. There are no automatic retries or spending loops.

Examples and all quota defaults are in `.env.example`. Local startup reads process environment; it does not automatically load `.env`. Export variables in the shell before starting. Docker Compose reads `.env` for the explicit settings forwarded in `compose.inspection.yml`. Never put keys in frontend variables or commit real keys. Selected evidence is sent only after per-generation consent; refinement requires consent for the current code and the original selected evidence. No unavailable-provider refinement is simulated.

AI files are parsed, checked against a fixed project schema, and compiled before replacement. Refinement merges only changed editable files and retains others. Invalid code, stale context, timeout, quota errors and provider failures retain the working project. A generation context lasts up to one hour in memory; browser inspection sessions retain their existing shorter expiry. Editor code remains in the open React session, including navigation away/back; download before closing/reloading. No code auto-save or new device storage is introduced.

## Preview and exports

Node/esbuild parses and bundles source without evaluating generated code, installing generated dependencies or loading generated build configurations. Only local project files, `react` and `react-dom/client` imports are supported. React metadata uses pinned dependencies and fixed Vite scripts; custom build configurations are rejected. The self-contained bundle is served in a separate preview document with both iframe and response sandboxing, no `allow-same-origin`, a nonce script policy, `connect-src 'none'`, no workers, no nested frames, no form submission and no external subresources. HTML source scripts, event attributes, external links, embeds and asset URLs are removed from preview markup. Secrets never enter preview code. Preview errors are returned through a bounded, source-checked message handler.

CSP blocks fetch/subresources; the iframe is **not a VM or a complete outbound-network firewall**. Browser support does not provide a general enforceable navigation prohibition for arbitrary JavaScript. Scripts can attempt self-navigation or consume CPU; the compiler has an eight-second bound and a two-request concurrency cap, but browser execution has no hard CPU kill limit. Use only private development deployments. A separately isolated preview origin/container with network egress filtering is needed before accepting hostile projects in a public service. An authenticated multi-user product is not claimed.

Previews are bounded to 16 in-memory documents with a ten-minute TTL; generation contexts are capped at 12. Projects are capped at 180 KB; API bodies are bounded; temporary compilation uses no generated filesystem tree. Local preview compilation does not consume generation allowances. Debounced preview can be turned off on lower-powered devices.

ZIP exports contain the current edited files, not a screenshot. Vanilla: serve the folder (`python3 -m http.server 8080`) or open `index.html`. React: `npm install`, `npm run dev`; `npm run build` produces a standalone deployment. Preview sanitization can differ from the exported HTML; review all downloaded code before use. External fonts/assets are intentionally absent and can be added manually after review.

Generation diagnostics expose included/omitted nodes and limitations. Preview DOM checks compare mapped nodes for missing elements, dimensions (2px/5% tolerance), font size, text color and page overflow. They are indicative, may change with the viewport, and are not a screenshot similarity or pixel accuracy score. No perfect interaction or animation recovery is claimed.

## Entitlements

Trusted server configuration selects `VEYRA_OPERATOR_PLAN=free|premium`. Clients cannot upgrade themselves. Configurable daily defaults: Free 4 generations/2 refinements; Premium 50/50. SQLite records attempted operations per UTC day and survives restarts; one shared operator allowance applies to the deployment. Preview limits (4/100) reserve a future hosted/server-preview allowance; ordinary local editor rendering is unmetered. Multi-element selection remains disabled until a complete secure selection flow exists. Context budgets differ by plan (24/55 nodes, preserving selected ancestry). There are no payments, fabricated subscriptions or public-user authentication.

## Verification

See `TEST_REPORT_V04.md` for executed checks and unresolved environment-dependent tests. Run:

```bash
.venv/bin/python -m pytest -q
npm --prefix frontend test
npm --prefix frontend run build
```

`STUDIO_TEST_CHROMIUM=/absolute/path/to/test/chromium` enables the separate offline browser acceptance harness. It uses a test-only browser runner without OS sandboxing on this restricted host; application source still requires protected Chromium. It is not evidence that production Docker/browser isolation started here. Do not use this test configuration to browse arbitrary sites.

The provisional V0.3.3 violet/blue brand, inspection studio and prompt policies remain; branding/legal approval is not fabricated. No production deployment or live external-provider call is claimed.
