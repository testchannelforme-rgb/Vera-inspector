# VEYRA AI V0.3.3 — UI & prompt studio review candidate

An incremental upgrade from verified V0.3.2 commit `349db3b671fc77c543b5073cdb85cd9a0a115b6e`, developed on `feature/v0.3.3-ui-prompt-polish`. **Branding, interface and legal documents are provisional. No production release or deployment is finalized.**

The existing React/Vite + FastAPI + sandboxed Playwright inspection engine remains. V0.3.3 adds a separate dark violet/blue landing page; redesigned inspector; six-step replayable tutorial; five meaningful prompt presets; an evidence coverage report; explicit local prompt version save/restore/duplicate/delete; and copy/section/TXT/Markdown/checklist exports. Deterministic local generation remains free and requires no model key. No coding engine, image generation, subscriptions, payment system, analytics or mandatory application accounts are added.

## Private development preview

Use your existing Codespace and keep its forwarded app port **Private**. Build before starting or testing the app:

```bash
npm --prefix frontend ci
npm --prefix frontend run build
bash start.sh --isolated
```

This repository retains its existing Compose app-port mapping `127.0.0.1:8001:8000`. Use the existing private forwarded app port. Restricted local development with `bash start.sh` uses port 8000 and only configured hosts. Do not disable Chromium sandboxing or remove network controls to work around a startup failure.

Routes: homepage `/#/`, inspector `/#/inspector`, logo alternatives `/#/brand`, device controls `/#/preferences`; draft policies at `/#/privacy`, `/#/cookies`, `/#/terms`; About/Contact at their named hash routes. Hash navigation works with the unchanged static backend without introducing permissive route fallbacks.

The local Vite preview additionally allows the exact managed development host `terminal.local`; production CSP, API-origin checks and browser URL policy are unchanged. The ordinary Vite development proxy still expects the backend on 127.0.0.1:8000.

## Verification

```bash
npm --prefix frontend test
npm --prefix frontend run build
.venv/bin/python -m pytest -q -rs
.venv/bin/python -m pytest -q -rs backend/tests/test_v033_ui.py
PYTHONPATH=backend .venv/bin/python scripts/check_browser.py
```

Read [TEST_REPORT.md](TEST_REPORT.md) for executed results and limitations. Browser tests are skipped where sandboxed Chromium cannot launch. Passing algorithm/component tests is not public-site or Docker-isolation acceptance. `--public` enables the existing real example.com navigation test. No live external AI request is required.

## Review material

- [Review guide and owner decisions](docs/V033_REVIEW.md)
- [Audited device/server/provider data flow](docs/V033_DATA_AUDIT.md)
- [Synthetic before/after prompt comparison](docs/review/v033/)
- Original SVG concepts: [Prism (provisional)](frontend/public/brand/veyra-prism.svg), [Orbit](frontend/public/brand/veyra-orbit.svg), [Signal](frontend/public/brand/veyra-signal.svg)
- Draft legal source: `frontend/src/content/policies.json`, also exported as Markdown under `docs/review/v033`.

## Data and operational limits

History is off by default. Only explicit Save Version/Duplicate persists prompt text on the current browser origin; no history service/upload exists. Limits are 20 versions, 512 KiB total and 60,000 characters per prompt. Storage failure keeps the editor text and reports the problem. Disable/delete/clear controls do not delete downloads, clipboard contents, server logs or provider copies. Edited/restored drafts survive selection changes as detached text; they do not claim an old inspection is live. There is no autosave.

Existing inspection sessions expire after 600 seconds total or 180 seconds idle by default. Public browsing still requires the supplied isolated Docker browser, validating gateway and firewall proof. Visible text/screenshots can contain private information despite minimization; inspect authorized public content and review exports before sharing.

Optional AI configuration remains backend-only and off by default; existing variables are documented in `.env.example`. Local mode makes no provider call. UI AI selection requires a per-generation acknowledgement when a provider is available; reduced evidence may be sent to that configured provider, whose terms/quotas must be reviewed by the owner. No credentials are put in frontend files, prompt history or review screenshots.

No raw inspection schema change (`0.1`) or prompt response schema version change (`0.3`) is made. The preset input and nested quality report are additive. Source security design and browser isolation remain in [SECURITY.md](SECURITY.md). Historical V0.3.2 release notes are retained in `docs/review/v033/baseline-test-report.md`.
