# Complete V0.3.2 changed-file manifest

32 source/documentation/test files are installed. The ZIP also contains packaging-only baseline copies, manifest, checksums, installer entry point and verification reports. No full-project replacement.

| Path | Purpose |
| --- | --- |
| `.dockerignore` | Exclude the V0.3.2 package and rollback backups from Docker build context. |
| `.gitignore` | Exclude V0.3.2 release extraction, ZIP and local rollback backups. |
| `README.md` | V0.3.2 usage, honest validation status and preserved optional AI settings. |
| `TEST_REPORT.md` | Exact fresh test results, blocked browser acceptance and re-run commands. |
| `UPGRADE.md` | Tablet-friendly guarded installation, conflict handling and rollback. |
| `backend/app/main.py` | Health/FastAPI version strings only; security middleware unchanged. |
| `backend/app/prompts/collect.js` | Reuse collector budgets; integrate bounded visual reads, context and paint priority. |
| `backend/app/prompts/composition.py` | Explain CSS indicators, attributed context and uncertain text-layer relationships. |
| `backend/app/prompts/css_safety.py` | Bounded CSS layer parser, asset omission and defensive sanitization. |
| `backend/app/prompts/deterministic.py` | Composition summary and precise attributed detail within eight-section output. |
| `backend/app/prompts/evidence.py` | Assemble visual helper and sanitize additive metadata inside existing byte budget. |
| `backend/app/prompts/selection.py` | Prioritize paint, generated decoration and layering evidence with ancestry retained. |
| `backend/app/prompts/visual.js` | New URL-safe gradients, pseudo-elements and attributed ancestor/nearby paint context. |
| `backend/app/prompts/visual_evidence.py` | Strict optional visual metadata minimization, finite geometry and sub-budgets. |
| `backend/tests/fixtures/visual.html` | Generic controlled layered/gradient/pseudo/image/responsive browser fixture. |
| `backend/tests/js/collector.test.mjs` | Assemble visual helper and make synthetic timing assertions deterministic. |
| `backend/tests/js/synthetic-dom.mjs` | Support computed pseudo styles and DOM containment in synthetic collector tests. |
| `backend/tests/js/visual.test.mjs` | 16 added visual capture, URL/privacy, bounds and paint-priority checks. |
| `backend/tests/test_install_v032.py` | Nine guarded installer/rollback and baseline compatibility tests. |
| `backend/tests/test_prompts.py` | Expected health version only. |
| `backend/tests/test_visual_browser.py` | Four protected-browser pipeline/responsive cases; skipped here due missing Chromium. |
| `backend/tests/test_visual_fidelity.py` | 75 visual sanitation, composition, exact styles, options and security tests. |
| `backend/tests/test_visual_pipeline.py` | Cross-language production collector -> sanitizer -> local prompt using synthetic DOM. |
| `docs/MODIFIED_FILES.md` | Complete changed-file purpose manifest. |
| `docs/V032_ACCEPTANCE.md` | Controlled-fixture and unrelated public-site manual acceptance checklist. |
| `docs/V032_ACCURACY.md` | Visual evidence model, bounds, uncertainty, compatibility and security design. |
| `docs/V032_CHANGELOG.md` | Focused technical release changelog. |
| `frontend/package-lock.json` | App version only; dependency resolution unchanged. |
| `frontend/package.json` | App version only; dependency versions unchanged. |
| `frontend/src/App.jsx` | Existing UI version badge only. |
| `frontend/src/components/PromptPanel.jsx` | Existing prompt panel version badge only. |
| `scripts/install_v032.py` | Guarded hash-checked branch-specific installer with backups and rollback; old installer retained. |

Not replaced: existing UI layout/control logic, `backend/tests/test_ui.py`, `backend/app/inspect.js`, browser/network/security configuration, Docker/Compose/devcontainer files, dependency versions, V0.3.1 installer and stable backup branches. `main.py` changes are version strings only; touched paths still require exact baseline compatibility. Unknown newer changes cause a safe stop rather than automatic reconciliation.
