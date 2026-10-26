# Veyra AI V0.3.1 — prompt accuracy upgrade

This is a focused update to the **attached clean V0.3 source**. It improves section boundaries, prioritization, CSS organization and reconstruction guidance. It preserves the inspector, hover, JSON export, existing UI, three scopes, three targets/detail levels, no-key generation and optional AI enhancement. No new dependency version or browser/network setting is introduced.

**Verified:** 214 Python tests and 34 Node tests passed, including exact style reconstruction and execution of the real collector against a synthetic DOM. The Vite production build passed. **Blocked:** 16 real-browser tests and the strict browser-startup probe because Chromium's executable is absent here. Docker/Codespaces, real-site V0.3.1 accuracy and live AI were not tested. Synthetic geometry is test data, not captured website evidence. See [TEST_REPORT.md](TEST_REPORT.md).

## Install into your existing Codespace

Use [UPGRADE.md](UPGRADE.md). The ZIP contains changed files only, baseline copies for comparison, a complete manifest and a conservative installer. It refuses other branches, uncommitted tracked changes, mismatching baseline files, unsafe paths and corrupt payloads. It never auto-stashes, resets or merges your work.

After saving your current work, upload `Veyra_AI_V0.3.1_Update.zip` to the repository root using the Explorer upload action. In the Codespaces terminal:

```bash
git status --short
git switch -c feature/v0.3.1-prompt-accuracy
unzip -q Veyra_AI_V0.3.1_Update.zip
python3 veyra-v031-update/apply_update.py --check
python3 veyra-v031-update/apply_update.py --apply
bash start.sh --isolated
```

If that branch already exists, use `git switch feature/v0.3.1-prompt-accuracy` instead of `git switch -c`. Stop if `git status` shows unsaved tracked changes; commit or back them up first. Apply only after the check passes. Modified committed source that differs from the attachment also requires manual reconciliation; no file is overwritten to force compatibility.

Open forwarded port **8000**, visibility **Private**. The existing isolated stack rebuilds the app/frontend. A working V0.3 Codespace needs no devcontainer change. On a fresh environment, use **Codespaces: Rebuild Container** and let the existing setup finish. Codespaces quotas still apply; no paid resource is purchased by the code.

Rollback, before making further source edits:

```bash
python3 veyra-v031-update/apply_update.py --rollback latest
bash start.sh --isolated
```

Rollback verifies installed-file hashes before restoring originals/removing newly added files. It refuses to overwrite later edits. Backups are under `.v031-backups/update-*`; unrelated files are preserved.

## What improves

- Section scope scores local semantic regions, painted component boundaries, measured layout/spacing and visible child groups. It rejects page landmarks, disproportionate tall ancestors and containers grouping unrelated landmarks. It reports reasons/candidates and a predictable local fallback. Explicit main/body/html selections in section mode ask you to select a local child. Element/page scopes remain available.
- Bounded discovery reaches later sibling headings, controls and images. The selected ancestry is pinned; original IDs, parent paths and DOM sibling indices are retained. The renderer prioritizes important nodes with complete ancestor paths instead of taking a prefix.
- Every captured **sanitized** CSS property for an included node is retained, including Concise output. Equal values are factored into exact shared groups plus node-specific mappings. This is not proof of inheritance or original CSS classes. Length-bounded/privacy-modified values are flagged.
- Prompts clearly organize hierarchy, content/assets, geometry/parent deltas, layout, typography, appearance, interactions, responsiveness, accessibility and limitations. Viewport intersection is geometric evidence, not a proof of pixel visibility or clipping.
- URL-free computed gradients, additional flex/spacing/overflow/font properties and DOM accessibility attributes improve evidence. Signed asset URLs, form values, editable text, HTML, cookies and storage remain excluded. Private composed/shadow ancestors are checked conservatively.

## Use the feature

1. Open a public site and tap a heading, card title, navigation item or button.
2. Choose **Selected section** and **Local**, then Generate Prompt. Review the reported boundary tag and reasons; compare it visually with the intended component.
3. Check original node IDs/parent hierarchy and exact shared style references. Merge referenced groups plus node-specific values to recover included CSS.
4. Try all targets and detail levels. Detail changes coverage rather than dropping measured properties. An unusually deep selected path can exceed the nominal Concise node count to preserve context.
5. Existing edit/copy/regenerate, hover capture and JSON export work as before. Wait for the existing three-generation/session/minute limit when necessary.

Only the current visible page sample is inspected; no scroll crawl, hidden-state activation, breakpoint discovery or source-code generation is added. Recommendations and AI interpretation remain labelled separately from measurements. Section segmentation is heuristic, not perfect. Follow [the manual acceptance checklist](docs/V031_ACCEPTANCE.md) on your working host before claiming real-site accuracy.

## Optional AI adapter

Local mode never contacts a model provider. AI mode requires deliberate administrator configuration and selection of **Optional AI + local fallback** in the UI. No paid account or live API call was used for these tests. A provider may charge or impose quotas; choose a currently available model and provider under your own budget before enabling it.

Use Codespaces repository secrets for the key (preferred), or an ignored `.env` file in the repository root for Compose. Keep `.env` out of Git. These are all supported variables:

| Variable | Default / meaning |
| --- | --- |
| `VEYRA_AI_ENABLED` | `false`; set to `true` to enable AI requests |
| `VEYRA_AI_PROVIDER` | `openai-compatible`; display label, letters/numbers/`._-` only |
| `VEYRA_AI_ENDPOINT` | `https://api.openai.com/v1/chat/completions`; full canonical HTTPS chat-completions endpoint, no query, credentials or fragment; port 443 only |
| `VEYRA_AI_MODEL` | Empty; supply the provider's available chat model identifier |
| `VEYRA_AI_API_KEY` | Empty; backend-only credential |
| `VEYRA_AI_TIMEOUT_SECONDS` | `15`; accepted range 1–20 seconds |
| `VEYRA_AI_MAX_OUTPUT_TOKENS` | `1500`; accepted range 128–2500 |
| `VEYRA_AI_TOKEN_PARAMETER` | `max_completion_tokens`; use `max_tokens` only if required by your compatible provider |

For Compose, an ignored `.env` may contain:

```dotenv
VEYRA_AI_ENABLED=true
VEYRA_AI_PROVIDER=openai-compatible
VEYRA_AI_ENDPOINT=https://api.openai.com/v1/chat/completions
VEYRA_AI_MODEL=YOUR_AVAILABLE_MODEL_ID
VEYRA_AI_API_KEY=YOUR_PRIVATE_KEY
```

Restart with `bash start.sh --isolated` after changing configuration. Only the app receives AI settings; the browser and gateway do not. For restricted local development, export these variables in the shell before `bash start.sh`; that script does not load `.env`. Never put credentials in Vite variables, frontend files, prompts or screenshots.

The adapter uses the chat-completions messages interface, no tools, no streaming and no automatic retries. It asks for three bounded interpretation fields and appends them to the eight-section measured prompt. AI prose is labelled interpretation, not observation. The credential is an HTTP header only. DNS validation and numeric-IP connection pinning reuse V0.2's egress gate; redirects and private endpoints are refused. A local/private model server is intentionally unsupported. Timeout, rate-limit, malformed response or missing configuration yields a useful local prompt. Wire-format behavior is mock-tested; a real configured model still needs verification.

## Test commands

```bash
bash scripts/setup.sh
.venv/bin/python -m pytest -q -rs
npm --prefix frontend test
npm --prefix frontend run build
bash scripts/test.sh --public
```

The last command includes the strict sandboxed Chromium probe. Unit/synthetic tests do not satisfy browser acceptance when that probe fails. The new browser cases are in `backend/tests/test_prompt_browser.py` and use `backend/tests/fixtures/accuracy.html` under the existing test-only local-site exception; production URL protections are unchanged.

After starting the real isolated stack:

```bash
.venv/bin/python scripts/test_public.py
.venv/bin/python scripts/test_prompt_public.py
```

Both scripts predate this update. The prompt probe defaults to local mode. Its `--ai` flag deliberately sends public evidence to your configured provider and can consume quota; use it only under your chosen budget. No live AI was called here.

Stop with `docker compose -f compose.inspection.yml stop`. No deployment, remote push, PR or changes to main are made by this package.

See [change list](docs/MODIFIED_FILES.md), [prompt contract](docs/PROMPTS.md), [accuracy design](docs/V031_ACCURACY.md), [security](SECURITY.md), and [test report](TEST_REPORT.md). Existing V0.2 runtime notes are historical context only.
