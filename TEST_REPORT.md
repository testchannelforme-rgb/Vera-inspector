# Veyra Inspector V0.2 — change and verification report

24 October 2026 (IST).

**Mission 02 success criterion is not verified complete.** The incremental implementation and tests are supplied, but this host cannot launch sandboxed Chromium and has no Docker. Public V0.2 rendering, Roblox compatibility, the isolated firewall and Codespaces rebuild/resume behavior remain unverified.

## Source and repository status

The authorized GitHub connection returned no accessible repositories. Fetching `testchannelforme-rgb/Vera-inspector` returned 404. No remote repository was modified; no branch, commit, PR, deployment or Codespace was created remotely. Development continued on the retained delivered V0.1 source, as permitted by the requested fallback. The generated update includes a baseline-aware three-way merge/check tool so it will not silently overwrite newer repository edits.

The user's reported prior Codespaces success with V0.1/example.com is accepted as user-provided history. It is not reported as a V0.2 test performed here.

## Implemented features

- A single authoritative smart URL normalizer shared by frontend/API, with HTTPS defaults, canonical hosts/ports/IPv6/IDNs and clear malformed/unsupported-address errors.
- Optional isolated public mode without per-host allowlisting: separate sandboxed Chromium, validating/pinning egress proxy, kernel outbound firewall, private control capability, resource limits and startup network probes. Restricted local mode remains. Missing isolation configuration fails closed.
- Public IPv4/IPv6 validation, mixed-DNS rejection, alternate IPv4 rejection, mapped/transition/NAT64 handling, metadata rejection, repeated DNS validation and numeric-IP connection pinning. Redirects and subresources cannot rely only on initial URL validation.
- Bounded SPA readiness/content/font/network observations, HTTP/resource status diagnostics, failed requests, safe console/CSP/JavaScript categories and explicit screenshot/transfer errors. HTTPS public API POSTs are no longer rejected merely because they are POSTs; unsupported operations and oversized bodies remain restricted.
- Full Chromium channel and pinned client/server versions; build-time browser/system installation in a clean Node 24/Debian image; intended project virtual environment; diagnostic doctor, safe engine retry and stale disconnected-context cleanup.
- Preserved dark visual styling, selection-coordinate conversion, DOM extraction, hover capture and inspection JSON schema 0.1. Diagnostics are additional frame/error data, not synthetic inspection data.
- Guarded incremental updater with checksums, nonconflicting three-way merge, all-conflict preflight, backups and rollback. Complete source and unified patch are also included.

“Implemented” describes code present. It does not imply the unexecuted browser/container paths passed acceptance.

## Files modified

See [docs/MODIFIED_FILES.md](docs/MODIFIED_FILES.md) for the exact list relative to the retained V0.1 baseline. Changes are concentrated in backend network/browser/startup/diagnostic modules, the URL/error UI, container/start scripts, tests and documentation. `frontend/src/styles.css`, `frontend/src/coordinates.js`, `backend/app/inspect.js`, `backend/app/inspector.py` and the core hover/extraction implementation remain unchanged.

## Actual tests performed

| Test | Actual result |
|---|---|
| Python unit/API/security/proxy/update tests | **118 passed**, zero failures |
| Browser-dependent pytest tests | **8 skipped/blocked** by sandboxed Chromium startup |
| Frontend coordinate/API tests | **9 passed**, zero failures |
| Vite production build | **Passed**, Vite 8.3.5 |
| Strict `bash scripts/test.sh --public` | **Exit 1** because the essential browser startup probe failed |
| Actual `bash start.sh` HTTP smoke | Frontend HTTP **200**, backend health **200**, bare Roblox URL normalized correctly; health truthfully reports `browser-sandbox-unavailable` |
| Direct sandboxed Chromium attempt | **Failed**: root without a supported sandbox/non-root namespace environment |
| `bash start.sh --isolated` | **Stopped safely**: Docker is unavailable in this host |
| Multi-public-site API test attempt | **Stopped safely** before navigation: isolated public browser was not ready |
| Compose YAML / private-port / internal-network / capability configuration assertions | **Passed as static checks**; containers were not run |
| Python compilation, JavaScript syntax, shell syntax, devcontainer JSON | **Passed** |
| Frontend npm dependency audit | No known vulnerabilities reported |
| Node browser-service package npm audit | No known vulnerabilities reported |
| Codespaces clean rebuild and stop/start | **Not executed** |
| Runtime firewall/direct-egress tests | **Not executed**; no Docker available |

One pytest deprecation warning relates to Starlette TestClient's httpx integration; the API tests passed. Audits are point-in-time package checks, not security certification or a scan of every binary/OS package. Raw current evidence lives under `artifacts/v02/`; older audit/smoke files elsewhere in `artifacts/` belong to V0.1.

The tests include URL canonicalization, unsafe IPv4/IPv6 forms, all-answer DNS validation, rebinding rejection, pinned proxy transport, API origin/body limits, navigation error categories, empty-content/screenshot errors, diagnostic redaction, full Chromium channel/sandbox options, preserving nonconflicting local edits, conflicts and backup behavior. Browser tests cover the original deterministic fixture plus delayed client-rendered content/empty content, DOM/style/hover/export behavior and the tablet UI flow once run on a supported host.

## Websites successfully inspected

**None verified through V0.2 in this delivery environment.** Browser startup failed before real website navigation. No screenshot or real inspection JSON is manufactured to fill this gap.

`example.com`, JavaScript-driven `react.dev`, and Roblox are configured in `scripts/test_public.py`. That script must be run against the actual private isolated instance; it captures real diagnostics/screenshots/inspection output only after success. Review rendered screenshots for completeness before claiming compatibility. HTTP 200 or selecting an HTML shell is not enough.

## Roblox / blank-preview investigation

Source review found plausible compatibility risks in V0.1: an exact-host allowlist can reject CDN/API resources; a 350 ms settle period can capture an unhydrated SPA; GET/HEAD-only Playwright routing can block HTTPS API POSTs; short proxy connection life can interrupt resources. V0.2 addresses these risks and exports the evidence needed to distinguish them.

**The original Roblox blank preview was not reproduced here**, so these are source-backed hypotheses, not a confirmed root cause. No automation-detection bypass, CAPTCHA handling, login, user-agent spoofing or certificate bypass was introduced. The screenshot preview does not iframe-embed the target; frame-embedding headers therefore are not themselves an explanation for a decoded screenshot being blank. The target's own CSP/resource failures are observed rather than disabled.

## Startup/container work

Newer prebuilt Playwright image tags checked at the registry returned 404. To avoid shipping an unavailable tag, both development and browser Dockerfiles build from maintained Node 24/Debian, install pinned Playwright 1.64.1, and install its matching full Chromium/system packages at **image build time**. The clean image avoids inheriting the old running container's Yarn APT signing-key problem. No old APT source was disabled and no Chromium security option was weakened.

Container builds themselves could not be executed here. Docker-in-Docker, IPv4/IPv6 netfilter, required capabilities and sandbox namespace support must be verified in the target Codespace. An unsupported host must remain blocked, not be made permissive to get a green result.

## Known limitations and security considerations

- The public-stack firewall design is implemented but unverified on this host; do not claim complete SSRF protection or deploy an unrestricted public service based only on unit/static checks.
- The trusted development/Docker controller is privileged infrastructure. The website browser is separately isolated and drops capabilities before launch. A malicious Docker administrator, gateway/controller compromise or kernel compromise is outside this boundary.
- Restricted local mode still needs exact approved hosts. The code refuses local unrestricted public browsing.
- WebSockets, service workers, media and some resource/method patterns remain restricted. Plain HTTP proxying is GET/HEAD only. Per-connection transfer/time budgets and per-session request limits can interrupt complex sites. Total per-session transfer accounting and per-context heap quotas remain future work.
- The default Docker subnet must not overlap another network. IPv6-only sites require gateway IPv6 reachability. IPv6 netfilter or sandbox restrictions can prevent startup; failure is intentional.
- Readiness, empty-content and access-check detection are heuristics. Canvas-heavy sites and long-running hydration may need manual refresh; no arbitrary JavaScript animation source is recovered.
- Iframe/closed-shadow content limitations, best-effort selectors/accessibility, bounded snippets and successive-screenshot timing remain from V0.1.
- No authentication/public abuse protection was added; keep Codespaces port 8000 **Private**. Secret files, .env, virtual environments, node_modules and Git metadata are excluded. No paid service or public deployment was used.

## Exact deployment and startup

Follow [UPGRADE.md](UPGRADE.md): upload/extract the update ZIP inside the existing repository, run the updater's `--check` then `--apply`, review conflicts if any, and choose **Codespaces: Rebuild Container**. Then:

```bash
bash start.sh --isolated
```

Open private forwarded port 8000. For optional restricted local development use `bash start.sh`. After Codespace resume, use the same isolated start command; it checks and, when necessary, retries the backend's browser connection. Test:

```bash
bash scripts/test.sh --public
.venv/bin/python scripts/test_public.py
```

Stop without deleting the project:

```bash
docker compose -f compose.inspection.yml stop
```

Resolve all actual browser/container/public-site test failures on the target host before marking Mission 02 complete. No such success is claimed in this delivery.
