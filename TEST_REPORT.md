# Veyra AI V0.3 — implementation and verification report

25 October 2026, IST.

**Implementation delivered; full Mission 03 acceptance remains blocked.** The deterministic engine, optional provider adapter and UI have automated coverage. No real V0.3 browser inspection, Codespaces run or live model response was verified in this environment. The user's reported working V0.2 Codespace is useful context, not a V0.3 test result.

## Repository and changes

GitHub `get_repo` for `testchannelforme-rgb/Vera-inspector` returned 404. Current remote architecture/commits could not be read, and no remote branch, commit, PR, push or deployment was created. Development uses a dedicated **local** `feature/v0.3-prompt-engine` branch based on the retained V0.2 source. Files and patch are supplied for guarded application to the actual repository; local differences may conflict.

Implemented: server-reference-based selected-element, heuristic section and visible-page evidence; measured eight-section local prompts; target/detail/style choices; optional configurable HTTPS compatible adapter; bounded provider calls and local fallback; visible AI/local metadata; editable textarea, copy fallback, regenerate, stale-output clearing and duplicate prevention. No source-code generation. Existing inspection JSON remains version 0.1.

HTTPX 0.28.1 moved from existing test dependencies into production requirements for the adapter. Its already-pinned closure is recorded in requirements.lock. React test renderer 19.1.1 is a dev-only dependency for actual component lifecycle/copy/edit/regenerate tests, with Vite's existing JSX transform. It adds no frontend runtime framework. It is deprecated upstream; a warning is retained rather than hidden. Browser UI tests remain the target-host acceptance check.

The browser manager adds only a small selected-hover summary and clears it with selection. The browser service scripts, browser image, devcontainer, sandbox flags, seccomp, network/firewall code, URL policy and proxy implementation are unchanged. Compose adds AI variables **only to the app environment**. No `.env`, API key, runtime capability, virtual environment or node_modules is distributed.

## Actual results

| Check | Result |
| --- | --- |
| Python unit/API/security/proxy/updater + prompt tests | **165 passed** |
| Browser-dependent Python tests | **10 skipped**: Chromium executable unavailable |
| Frontend Node tests | **15 passed**, including actual React component behavior |
| Vite production build | Passed |
| Python compilation / collector JavaScript syntax / browser-test JS syntax | Passed |
| Actual `bash start.sh` HTTP smoke | Frontend 200; health 200/version 0.3.0; missing-session prompt 404 |
| Browser startup probe | Failed: `browser-binary-missing`; sandbox remains enabled |
| Chromium install attempt | Failed: CDN downloads yielded invalid/truncated ZIP archives |
| User-namespace probe | Denied: writing `/proc/self/uid_map` not permitted |
| `bash start.sh --isolated` | Refused correctly: Docker unavailable |
| Frontend npm audit | 0 reported known vulnerabilities (not an OS security certification) |
| Live public websites inspected in this V0.3 run | None |
| Real AI provider / real key test | Not run; no credentials or paid calls used |
| Docker build/start, firewall, Codespaces rebuild/resume, visual tablet/mobile | Not run on this host |

An inherited timeout test assumed `monotonic() > 600` and initially failed on this recently started runtime. Its setup now sets the birth time relative to the current monotonic clock; production expiry behavior did not change. Initial prompt-test fixture/assertion errors were fixed. The final unit suites have no failures. Acceptance still fails at protected browser startup, so passing unit tests do not make the milestone fully verified.

One existing Starlette HTTPX deprecation warning remains. Frontend component tests also report the upstream React test renderer deprecation. No protections were disabled to make tests pass.

## Coverage

- Simple measured button, navigation hierarchy, complex section and representative visible page.
- Exact measured CSS, formats, detail lengths, recommendation styles and incomplete evidence.
- Stale session/frame/reference, strict request schema, request-size/origin protections and rate/concurrency admission.
- Redaction/minimization and instruction-bearing page text treated as quoted data.
- Mocked compatible request contract, successful model interpretation, rate limit, HTTP errors, redirects refused, timeout, oversized/truncated/malformed output, secret echo rejection and deterministic fallback.
- Real HTTPX-to-local-egress-gate refusal for a private destination; no external provider needed.
- Actual React component generate/edit/copy/regenerate, failed-regenerate draft preservation and stale-output clearing, plus existing coordinate and API tests.
- New actual-browser fixture tests and the extended tablet UI selection/hover/export/prompt test are present but skipped here.

## Reproduce

```bash
bash scripts/setup.sh
.venv/bin/python -m pytest -q -rs
npm --prefix frontend test
npm --prefix frontend run build
bash scripts/test.sh --public
bash start.sh --isolated
.venv/bin/python scripts/test_prompt_public.py
```

`test.sh` additionally performs the strict sandboxed startup probe; it must not be described as passing here. `test_prompt_public.py --ai` explicitly requests one live configured provider call and fails acceptance if fallback is returned. Do not use it until provider quotas/budget are acceptable.

Evidence logs are under `artifacts/v03`. Packaging checks and the guarded updater are also tested against the retained V0.2 baseline. The ZIP includes a patch, baseline/updated copies and full source for review. See [UPGRADE.md](UPGRADE.md) for exact tablet instructions and conflict handling.

## Limitations

Visible-only bounded sampling (not a complete scroll crawl); heuristic section boundaries/visibility; best-effort PII redaction; no hidden-state or multi-viewport breakpoint verification; no cross-origin iframe/closed-shadow/canvas internals; no authored stylesheet recovery or asset reproduction. AI prose may hallucinate or carry injected instructions despite the isolated data contract, and must be reviewed. Measured sections remain authoritative. No absolute prompt-injection immunity is claimed. There are no tools or secret-bearing model context and no executable output rendering.

AI provider compatibility is wire-format/mock-tested, not live-verified. Some compatible providers need different structured-output/model behavior and may fall back. Local/private provider endpoints are deliberately unsupported. Per-process rate limits assume the supplied single-worker private deployment; authentication, production multi-user budgets, persisted prompt history and full code generation are outside V0.3.
