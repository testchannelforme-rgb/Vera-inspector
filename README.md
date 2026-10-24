# Veyra Inspector V0.2

An incremental upgrade of the V0.1 screenshot inspector. The dark UI, DOM selection, computed CSS and inspection JSON schema 0.1 are preserved. No paid API is used.

**Delivery status:** smart URLs, diagnostics, readiness changes, startup scripts and an isolated public-browser implementation are supplied. The frontend build, HTTP/API behavior and unit tests ran here. This host cannot launch sandboxed Chromium and has no Docker, so real V0.2 website rendering, Roblox compatibility, container isolation and Codespaces rebuild/resume behavior are **not verified**. Read [TEST_REPORT.md](TEST_REPORT.md).

The GitHub connection exposed no accessible repositories. The upgrade is based on the V0.1 source retained in this conversation, not a fetched snapshot of the current `Vera-inspector` repository. The distribution includes a guarded updater, a unified patch and the complete source for review. No remote repository was changed.

## Apply the upgrade on your tablet

See [UPGRADE.md](UPGRADE.md). Do not replace or delete your repository. The updater checks every changed file, attempts nonconflicting three-way merges, creates backups and refuses to write if any conflict requires review. Unrelated files remain untouched.

## Start public inspection in Codespaces

1. Apply the update in the existing repository root.
2. Open the command palette and choose **Codespaces: Rebuild Container**. The development image builds matching Chromium binaries/libraries and includes Docker-in-Docker for the separate browser stack. This first rebuild can take several minutes and uses your existing GitHub included compute/storage quota. No paid usage or credit card is required by the code; stop the Codespace when finished.
3. In the repository terminal run:

```bash
bash start.sh --isolated
```

4. Open **Ports → 8000 → Open in Browser**. Keep port visibility **Private**. No browser or gateway control port is published.
5. Enter `example.com`, `www.roblox.com`, `react.dev`, or another valid public address. HTTPS is added when omitted. HTTP is supported explicitly. The backend performs the same normalization for the UI and API.

Public mode builds and starts the app, browser and egress gateway. The browser firewall permits new outbound connections only to the gateway on port 8888; IPv6 new connections are denied. The gateway resolves/checks destinations and connects to vetted numeric IPs. The startup command runs direct-network canary checks, then checks the real browser API. It stops public browsing if the isolation probe fails. **These container checks could not be run in the delivery environment.** The stack must be verified on the target host before relying on its isolation.

Docker requires a compatible Linux host, network-administration capability for the dedicated browser container's startup firewall, IPv4/IPv6 netfilter support and Chromium sandbox namespaces. The trusted development controller may have Docker/privileged capabilities through Docker-in-Docker; the website browser runs in a separate container, drops all capabilities before Chromium launches, and keeps Chromium's own sandbox. No development workspace, Docker socket or user account credentials are mounted into the browser.

Stop or restart without deleting source or secrets:

```bash
docker compose -f compose.inspection.yml stop
bash start.sh --isolated
```

After a Codespace stop/start, run the same start command. It reuses stored random capabilities, reapplies firewall rules, checks browser connectivity, and retries a stale backend connection when necessary. Clean rebuild/resume behavior still needs an actual Codespaces test.

## Restricted local development

The direct/local browser remains an optional restricted mode. It cannot be changed into an unrestricted local browser by setting an environment flag. Use the isolated stack for arbitrary public hosts.

```bash
bash scripts/setup.sh
bash start.sh
```

This serves frontend and backend on `http://127.0.0.1:8000`. The project `.venv/bin/python` is always used. Required local versions: Python 3.11+, Node 22.12+ or 24, npm, and a sandbox-capable non-root Chromium environment. The supplied devcontainer provides the matching browser libraries. Outside it, install required Linux libraries through your host's normal package management; Veyra no longer tries to modify third-party APT sources at startup.

Optional exact hosts for restricted development:

```bash
export VEYRA_NETWORK_MODE=restricted
export VEYRA_ALLOWED_HOSTS=example.com,www.example.com
bash start.sh
```

Wildcards are rejected. Never expose either mode as an unrestricted public service; authentication and public-service abuse controls are outside this prototype.

## What changed

- URL input accepts bare hostnames and uses the backend's `/api/normalize` endpoint. It trims surrounding whitespace, adds HTTPS, canonicalizes IDN/IPv6/ports, rejects arbitrary text, unsupported schemes, credentials, malformed hosts and unsafe/alternate numeric IPs.
- Isolated public mode uses a separate sandboxed browser and validating egress gateway, with an outbound firewall and unguessable private browser-control capability. Restricted local mode remains available.
- Page rendering waits for bounded content/network readiness instead of a fixed 350 ms delay. It observes visible DOM content, completed images, fonts and pending requests. This is a heuristic, not proof that every SPA is ready.
- Page diagnostics report HTTP status, navigation state, empty-content observations, blocked/failed resource hosts, JavaScript/console error categories and screenshot status. Queries, credentials and raw console text are omitted. Potential access-check messages are flagged; no bypass is attempted.
- Navigation timeout, inaccessible/blocked site, empty content, screenshot failure, transfer/decode failure and browser failure are distinguished.
- Startup diagnostics identify missing binaries, missing libraries, sandbox restrictions, unavailable browser service and missing isolation configuration. **Retry engine** reconnects safely; stale disconnected contexts are cleaned up.
- The full `chromium` channel is used consistently, so a missing Headless Shell cannot silently select a different browser. Node/Python Playwright versions are pinned together. Browser/system packages are installed during clean image build, avoiding manual edits to a running Codespace and its stale Yarn repository.

The UI still sends selection coordinates rather than remote clicks. Tap to select; swipe/wheel or Scroll buttons to scroll; use Motion → Capture hover and the existing JSON controls. Website HTML is escaped text evidence. Cross-origin DOM access is performed only inside the remote browser, never through an iframe bypass.

## Tests

```bash
bash scripts/test.sh --public
```

Runs Node tests/build, unit and deterministic local browser tests, then the strict browser-startup probe. An unavailable browser makes acceptance fail even if unit tests pass. Deterministic local-site exceptions exist only in test fixtures.

After the **isolated public stack** is ready:

```bash
.venv/bin/python scripts/test_public.py
```

This checks `example.com`, JavaScript-driven `react.dev`, and Roblox through the actual API. It refuses unrestricted tests against the local/restricted browser. It writes real screenshots, inspection JSON and diagnostics only after each site's checks pass, under `artifacts/generated-v02`. Review those screenshots for complete rendering: HTTP 200 and a nonempty DOM alone do not prove Roblox compatibility.

Inspect environment/startup:

```bash
bash scripts/doctor.sh
bash scripts/doctor.sh --environment-only
docker compose -f compose.inspection.yml logs --tail=80 browser gateway app
```

Do not share control endpoints, secret files, raw page console output or credentials. The UI's **Copy diagnostics** deliberately omits raw console messages and URL queries. Existing `artifacts` audit/smoke files outside `artifacts/v02` are legacy V0.1 evidence, not current V0.2 verification.

## Blank previews and limitations

The old allowlist could block CDN/API assets, the old short settle delay could capture an unhydrated page, and GET/HEAD-only routing could break HTTPS SPA API POSTs. These are compatibility risks found in source review, **not a demonstrated diagnosis of Roblox's blank page**. V0.2 permits bounded HTTPS API POSTs to validated public destinations, broadens hosts only in isolated mode and exports evidence to distinguish the cause.

The preview is a screenshot, not an embedded website frame. A site's frame-embedding policy does not itself block the data-URL preview. Its own CSP can still block resources inside Chromium; diagnostics classify relevant console errors. Veyra's UI CSP permits screenshot data URLs. Frontend decoding failures are reported separately from browser screenshot failures.

Service workers, WebSockets and large/media resources remain restricted. Plain HTTP proxying is GET/HEAD only; HTTPS can carry bounded API requests under Playwright policy. Fixed transfer/time/request limits can interrupt complex sites. Empty-content and access-check heuristics may miss canvas-only content or unusual site behavior. No CAPTCHA, authentication, paywall or automation restriction is bypassed. No Roblox success is claimed in this delivery.

Inspect [SECURITY.md](SECURITY.md) before wider use. Inspection JSON stays at schema 0.1; diagnostic metadata is attached to frames/errors, not substituted for actual inspection values.
