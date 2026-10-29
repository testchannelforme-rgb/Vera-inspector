# V0.3.3 candidate verification — 29 October 2026

Baseline: `349db3b671fc77c543b5073cdb85cd9a0a115b6e`. Branch: `feature/v0.3.3-ui-prompt-polish`. Review candidate only.

## Existing Codespace — executed

- Node/React/JavaScript: **60 passed, 0 failed**.
- Vite production build: **passed**.
- Full Python/API/security/browser suite: **330 passed, 1 skipped, 0 failed**, one inherited Starlette/httpx deprecation warning; 100.97 seconds. The single skip is the explicit opt-in public-site case.
- Separate public-site case with `--public`: **1 passed, 0 skipped, 0 failed**; 4.12 seconds. It verifies example.com identity/title, HTTP 200, real selection geometry and computed font CSS. Current external markup has no h1; the test selects the actual body when h1 is absent.
- Strict protected Chromium startup probe: **PASS**. No sandbox or network protection was relaxed.
- `git diff --check`: passed before commit.

Tests ran in an isolated source copy using the existing Codespace dependencies. This prevents inherited tests from replacing the owner’s seven pre-existing untracked source/export/screenshot files. Their SHA-256 hashes were checked against the pre-import snapshot.

The two new real-browser acceptance cases ran against actual FastAPI + built React + protected Chromium. They exercised desktop (1440×1000), tablet (1024×900) and mobile (390×844), navigation and route focus, no horizontal overflow, tutorial Skip/Back/Next/Finish/Replay and dismissal, keyboard tabs, reduced motion, no implicit history or application cookies, real screenshot-coordinate selection/hover, preset generation, evidence report, exact manually edited TXT/Markdown exports and checklist, explicit history enable/save/reload/restore/duplicate/delete, and confirmed data deletion.

Browser acceptance found and fixed route-scroll focus and an accessible History-tab badge issue. The deletion test now correctly checks the required confirmation instead of expecting immediate destructive deletion. Real screenshots are in `docs/review/v033/screenshots/`; the workspace views use the test fixture inspected through the real engine. The homepage’s decorative specimen is labelled illustrative.

Final Python/public logs are beside the screenshots. Earlier failing runs were used for diagnosis; they are not reported as passes.

## Work runtime — executed

- Node/React/JavaScript: **60 passed**.
- Python: **309 passed, 22 skipped**, one inherited warning.
- Production build and whitespace check: passed.

The official Chromium download in this separate runtime returned incomplete/invalid archives; Docker is unavailable here. Browser acceptance was therefore completed in the existing Codespace. The initial baseline serving test raced the first dist build; build-first and that exact rerun passed.

## Coverage and limits

Additional unit/integration checks cover strict five-preset output differences, eight-section contract, visual node budgets/report agreement, sanitization/truncation/unknowns, local generation without provider calls, optional AI acknowledgement/fallback, manual draft preservation/stale responses/Undo, opt-in history caps and corrupt/quota errors, exact section/text exports and object URL cleanup. No accuracy percentage is invented.

A fresh Docker Compose isolated-stack build and live external AI-provider call were **not executed**. Existing network/security behavior and deployment configuration were preserved. No production deployment, paid service, legal certification, trademark clearance or final branding/design/legal approval is claimed.
