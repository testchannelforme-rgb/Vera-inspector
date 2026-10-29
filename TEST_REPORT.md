# V0.3.2 verification report — 26 October 2026

Tests ran locally against the supplied V0.3 base plus manifest-verified V0.3.1 update, with V0.3.2 changes. This environment is not GitHub Codespaces. Latest installed checkpoint `29ef127` was reported by the user but inaccessible; it is not the tested source baseline. No prior V0.3.2 draft was used.

## Executed results

| Command/check | Actual result |
| --- | --- |
| Fresh reconstructed V0.3.1 `.venv/bin/python -m pytest -q -rs` | 214 passed, 16 skipped, 0 failed |
| Fresh reconstructed V0.3.1 `npm --prefix frontend test` | 34 passed, 0 failed |
| Fresh reconstructed V0.3.1 Vite build | Passed |
| Final V0.3.2 `.venv/bin/python -m pytest -q -rs` | **299 passed, 20 skipped, 0 failed**, 1 dependency deprecation warning; 7.94 seconds |
| Final V0.3.2 `npm --prefix frontend test` | **50 passed, 0 failed**, 257 ms |
| `npm --prefix frontend run build` | Passed; 22 modules; 135 ms |
| `.venv/bin/python -m compileall -q backend/app scripts/install_v032.py` | Passed |
| `git diff --check` | Passed |
| Actual localhost Uvicorn/HTTP smoke | Passed frontend HTML route, CSP header, V0.3.2 health version, smart URL normalization and malformed prompt rejection; browser health correctly unavailable |
| `PYTHONPATH=backend .venv/bin/python scripts/check_browser.py` | **Failed**: browser-binary-missing; sandbox remains enabled |
| `.venv/bin/python -m playwright install --no-shell chromium` | **Failed**: incomplete Chromium download; ZIP central-directory signature missing |
| Docker/Codespaces | Not run: Docker unavailable and no accessible Codespace |
| Public websites / real screenshots / visual comparison / live AI | Not run: Chromium unavailable; no compatibility or image-similarity claim |

Python uses 3.12.14 and the supplied requirements; Node 24.22.1 uses the existing lockfile. No dependency version was upgraded. Starlette emits an existing TestClient/httpx deprecation warning. React test renderer emits its existing deprecation warning. Neither warning was hidden by a security/config change.

The reported historical 229-passed/1-skipped checkpoint could not be reproduced from an inaccessible Codespace. Our own supplied-source baseline is shown above; this update adds **85 passing Python tests, four additional blocked browser cases and 16 passing JavaScript tests** to that baseline.

## What the passing tests establish

- Existing API/session/URL/SSRF/proxy/provider/inspection regressions continue passing where they do not require a browser. Provider calls are mocked, not paid/live.
- Node executes the actual assembled collector against a controlled synthetic DOM: gradient types/layers/order, background ownership, generated/no pseudo content, private pseudo exclusion, clip/fill/stroke/shadow/mask/blend/transform, nearby overlap limits, URL omission, size limits and critical paint priority.
- Python validates/sanitizes CSS, redacts dangerous/credential-bearing references and control-byte obfuscation, enforces metadata/geometry/byte budgets and handles malformed optional evidence.
- The real collector source → Python sanitizer → deterministic service is exercised across languages with synthetic DOM measurements. This is not a real browser screenshot or live website.
- Overlapping same-copy hypotheses require geometric/DOM/layer evidence. Nonoverlapping or ordinary duplicate text is not merged. Exact shared styles reconstruct to original sanitized node values, including new visual CSS.
- All 27 scope/detail/target combinations retain the eight sections. Legacy V0.3.1 evidence, empty/partial/truncated handling, no-key generation, provider fallback, untrusted text and strict client request validation are covered.
- Actual React prompt panel tests exercise generate, edit, copy edited draft, regenerate, missing selection/page scope, duplicate requests and failure behavior. They run in React test renderer, not mobile Chromium.
- Installer tests cover check/apply/backups/rollback, wrong branch, dirty/staged safeguards, incompatible committed files/anchors, payload/baseline tampering, traversal/symlinks/protected paths, later-edit refusal and preservation of unrelated Codespace test fixes.

## Skips and failed acceptance

The 20 skipped cases require the existing sandbox-enabled Chromium fixture: 7 inspection/browser, 8 prompt/browser, 1 UI/browser and 4 new visual/browser cases. Missing executable caused the skips. The separate strict browser probe fails rather than converting that condition into acceptance. No sandbox, CSP or network setting was weakened. Full browser acceptance is outstanding.

New fixture `backend/tests/fixtures/visual.html` and `test_visual_browser.py` cover gradients, transparent/clipped/layered text, conic pseudo decoration, image overlay/mask, cards/buttons and one 390px responsive observation. They were collected by pytest but skipped, so their assertions have not run against Chromium here. No authored breakpoint discovery or screenshot similarity is claimed.

## Re-run on Codespaces

```bash
bash scripts/setup.sh
.venv/bin/python -m pytest -q -rs
npm --prefix frontend test
npm --prefix frontend run build
PYTHONPATH=backend .venv/bin/python scripts/check_browser.py
bash scripts/test.sh --public
bash start.sh --isolated
.venv/bin/python scripts/test_public.py
.venv/bin/python scripts/test_prompt_public.py
```

Keep forwarded port 8000 Private. Preserve your existing working Docker/devcontainer configuration and run `docs/V032_ACCEPTANCE.md` on several unrelated public websites. Do not infer a full pass from unit tests or add permissive flags. Optional AI must be deliberately configured and validated separately; no API key is required for this release.

Package installation/rollback end-to-end results are recorded in the ZIP's `verification/PACKAGE_INSTALL_TEST.md`, generated after final payload assembly.
