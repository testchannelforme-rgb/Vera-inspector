# Veyra AI V0.3.2 — visual fidelity update

Incremental upgrade to the supplied V0.3 base plus V0.3.1 update. It improves visual evidence and deterministic recreation prompts without changing the UI layout, eight-section prompt contract, raw inspection JSON schema, browser isolation or network configuration. No new dependency or mandatory AI service.

**Verification on 26 October 2026:** 299 Python tests passed, 20 browser-dependent tests skipped; 50 JavaScript/frontend tests passed; Vite production build passed. The HTTP application/frontend smoke test passed. **Browser acceptance remains blocked:** Chromium download failed with an incomplete archive, the strict sandbox-enabled startup probe failed, and Docker is unavailable here. No public website, real screenshot comparison, Codespace or live AI provider was validated for this release. This is an installable, regression-tested update awaiting browser acceptance on your working host.

## Install and start

Read [UPGRADE.md](UPGRADE.md) first. The package checks exact baseline hashes, protects newer source, creates backups and supports rollback. It never switches branches, resets or stashes your work. The reported Codespaces checkpoint `29ef127` was not accessible; this is **not** an exact snapshot of that checkpoint.

After saving/committing your existing work, create the target branch from your actual installed V0.3.1 branch, upload/extract the ZIP, then run:

```bash
python3 veyra-v032-update/apply_update.py --check
python3 veyra-v032-update/apply_update.py --apply
bash start.sh --isolated
```

Keep forwarded port **8000 Private**. If the check reports a conflict, stop and reconcile against the latest source. Do not replace files manually to defeat the guard. The unchanged isolated startup rebuilds the app/frontend and verifies the browser network rules. No devcontainer or Compose change is required by this upgrade.

## What changes

- Single/multiple linear, radial, conic and repeating gradients retain sanitized parameters and layer order; URL assets remain explicit placeholders.
- A transparent selected element keeps its own CSS. Bounded ancestor/nearby paint context records the actual background owner instead of assigning that background to the child.
- Generated `::before`/`::after` decoration retains owner, computed dimensions/offsets and paint. No pseudo bounding rectangle is invented.
- Text clipping/fill/stroke/shadow, masks, blend modes, opacity, transforms, clipping, stacking indicators and image availability receive useful evidence.
- Geometrically overlapping matching text with DOM/layering indicators is described as a **possible** composition/state/accessibility alternative. Separate DOM nodes and exact CSS remain available; equal text alone never merges content.
- A Visual Composition Summary leads the existing eight-section prompt. Exact shared styles and node-specific mappings remain lossless for included sanitized properties. Unknown paint order, pixel colors, states and responsive layouts stay explicit.

See [technical design and limits](docs/V032_ACCURACY.md), [manual acceptance](docs/V032_ACCEPTANCE.md), [changed files](docs/MODIFIED_FILES.md), [changelog](docs/V032_CHANGELOG.md) and [test report](TEST_REPORT.md). Existing V0.3.1 documentation is retained as historical design context.

## Use it

1. Open a permitted public website and select a heading, card or control as before.
2. In the existing prompt panel choose Element/Section/Page, target and detail. Use **Local** to avoid provider calls, then Generate Prompt.
3. Review Visual Composition Summary, original node hierarchy, exact CSS references and attributed context/pseudos. Ancestor paint is context, not additional selected content.
4. Compare with the preview; verify proposed text-layer relationships rather than treating them as proven pixel visibility. Edit, copy and regenerate using the existing controls.
5. Capture Hover and regenerate to include actual measured hover observations. Transition declarations alone do not establish an observed effect.

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
PYTHONPATH=backend .venv/bin/python scripts/check_browser.py
```

For combined checks including the public example.com test: `bash scripts/test.sh --public`. A green unit suite with skipped browser cases is not browser acceptance. New protected-browser cases live in `backend/tests/test_visual_browser.py` and use a generic local fixture under the existing test-only exception; production URL policy is unchanged.

On the running isolated stack, execute `scripts/test_public.py` and `scripts/test_prompt_public.py` with `.venv/bin/python`, then follow the real-site acceptance checklist. No live AI is needed. Stop using `docker compose -f compose.inspection.yml stop`.

No remote push, PR, production change or public deployment was performed.
