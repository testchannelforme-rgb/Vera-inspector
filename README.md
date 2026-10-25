# Veyra AI V0.3 — website recreation prompts

An incremental prompt-generation feature for the V0.2 inspector. It preserves the existing preview, element selection, hover capture, computed CSS, JSON schema 0.1 and isolated browser services. No model, GPU or API key is required for local generation.

**Verified here:** 165 Python tests and 15 frontend tests passed, plus the production frontend build and actual HTTP startup smoke check. **Not verified here:** real browser inspection in V0.3, Docker/Codespaces execution, visual tablet rendering or a live AI provider. This host lacks Docker and Chromium; its browser download failed and user-namespace creation is denied. See [TEST_REPORT.md](TEST_REPORT.md).

The GitHub API returned 404 for `testchannelforme-rgb/Vera-inspector`. This update uses the retained V0.2 delivery, not a fetched copy of your latest repository. The guarded incremental updater is the intended application route. It refuses conflicting changes; do not replace your repository wholesale.

## Apply and start on your Android tablet

Upload `Veyra_AI_V0.3.zip` into your existing Codespaces repository using the Explorer upload action. In its terminal:

```bash
git switch -c feature/v0.3-prompt-engine
unzip -q Veyra_AI_V0.3.zip
python3 veyra-v03-update/apply_update.py --check
python3 veyra-v03-update/apply_update.py --apply
bash start.sh --isolated
```

Run `--apply` only if `--check` reports no conflicts. The updater backs up replaced files and leaves unrelated files alone. Read [UPGRADE.md](UPGRADE.md) for conflicts, review and test commands. If your working V0.2 environment already has its dependencies, no devcontainer change is needed. `--isolated` rebuilds the app with the new frontend and HTTPX dependency. On a fresh Codespace, choose **Codespaces: Rebuild Container** and let the existing setup finish first. Codespaces included quotas still apply; the application does not purchase resources.

Open **Ports → 8000 → Open in Browser**, with visibility **Private**. No public deployment or repository push is performed by the scripts.

## Generate your first prompt

1. Open `example.com` or another public website in the inspector.
2. Tap an element. Keep using the existing inspector and JSON export normally.
3. In **Generate AI Prompt**, choose Selected element, Selected section, or Full page · visible sample.
4. Choose HTML + CSS, HTML + CSS + JavaScript, or React. The default detail is Detailed and style is Faithful recreation.
5. Leave **Local · no API key or cost** selected, then press **Generate Prompt**.
6. Review the measured values and accuracy notes. Edit the text directly and use **Copy Prompt**. If clipboard permission is unavailable, the text is selected for manual copying.
7. **Regenerate** replaces your edits. Scrolling, selection, refreshing the image or opening a page clears the old draft. Capture Hover in the Motion tab before generation to include that selected element's observed style changes.

Full page means a bounded sample of **currently visible content**, not an automatic scroll crawl. Section scope uses the nearest semantic ancestor, or immediate parent, and labels this heuristic. Exact breakpoints, hidden states and off-screen content are not claimed as inspected. No source code is generated or executed.

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

## Tests and verification

```bash
bash scripts/setup.sh
npm --prefix frontend test
npm --prefix frontend run build
.venv/bin/python -m pytest -q -rs
bash scripts/test.sh --public
```

The final command also requires a successful sandboxed Chromium probe; unit tests alone cannot satisfy acceptance. Actual browser tests use a deterministic local fixture through a test-only policy exception. No production local-network exception was introduced.

After starting the isolated stack, test public inspection and all prompt scopes through its live API:

```bash
.venv/bin/python scripts/test_public.py
.venv/bin/python scripts/test_prompt_public.py
```

The prompt probe defaults to local generation and records only a public test site's results. To verify your configured AI provider deliberately, run `scripts/test_prompt_public.py --ai`; it sends reduced public evidence to that provider and may consume its quota. A fallback response does not count as live AI success. No live-provider test was performed here.

Stop safely:

```bash
docker compose -f compose.inspection.yml stop
```

See [SECURITY.md](SECURITY.md), [docs/PROMPTS.md](docs/PROMPTS.md), [docs/MODIFIED_FILES.md](docs/MODIFIED_FILES.md), and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). The original V0.2 runtime notes are retained in [docs/V02_RUNTIME.md](docs/V02_RUNTIME.md) as historical context. V0.3 has no authentication or public-service abuse protection; retain private forwarding.
