# Security model and limits

## Intended exposure

Private, single-developer prototype. Keep Codespaces port 8000 private. No public deployment was made. There is no login, multiuser authorization, or public-service abuse protection. Session IDs are unpredictable capabilities held only in React memory; logs from `start.sh` omit access URLs to avoid recording them. Any user who obtains a session ID can operate that session.

## Implemented defenses

- Only HTTP/HTTPS, ports 80/443, exact configured hostnames, and no URL credentials. Reject localhost, internal/local suffixes, malformed host syntax, trailing-dot aliases, unsupported schemes and IPv6 zone IDs.
- Resolve DNS with a timeout and validate **every** returned address. Reject private, loopback, link-local, unspecified, multicast, reserved/non-global and mapped private IPv4 addresses, including common metadata IPs.
- A local, ephemeral, Basic-authenticated outbound proxy gates HTTP and CONNECT destinations. It repeats DNS validation and calls `open_connection` with a numeric vetted IP, avoiding DNS rebinding between validation and the proxied connection. TLS remains end-to-end; certificates are not ignored.
- Redirected traffic must traverse the proxy too. A redirect to another host requires a newly approved proxy destination. A same-host tunnel remains pinned to the public address selected when it was opened. Playwright routing applies a second request-level policy; the proxy is important because routing alone is not a complete egress boundary.
- Force proxying of loopback destinations (`<-loopback>`), disable QUIC and DNS prefetch, restrict WebRTC to proxied handling. Service workers, WebSockets, media requests, downloads, additional browser pages, dialogs, and non-GET/HEAD website requests are blocked/cancelled where supported.
- Chromium sandbox explicitly enabled. Browser launch fails closed rather than retrying without it. Same-origin restrictions remain intact; iframe content is not inspected. No remote click or keyboard-input endpoint exists.
- Fresh isolated, nonpersistent contexts; two maximum sessions, 600-second absolute / 180-second idle expiry, reaper every 10 seconds, navigation 15 seconds, operation 22 seconds, default element operations 4 seconds, screenshots 5 seconds. One worker only: in-memory sessions are not shared across workers.
- 250 routed requests per session (reload does not reset this lifetime budget). Proxy allows at most 32 concurrent connections, 16 KiB headers, 12 MiB bidirectional transfer per connection, a 25-second connection lifetime and 10-second read idle timeout. Some long-lived resources will be interrupted.
- Viewports bounded to 1440×1000, screenshots DPR=1 and JPEG quality 78, no continuous capture. Hover limited to 2 seconds and minimum 50 ms requested sample interval.
- API request bodies capped at 8 KiB including chunked bodies, no permissive CORS, same-host Origin checks, custom client header on writes, no-cache responses, framing denied, script/image restrictions in the UI. The UI renders snippet strings as escaped React text.
- HTML evidence strips script/style contents, form values, inline event handlers, srcdoc and nonce. Text is capped at 1,000 characters, HTML at 20,000, active animations/keyframes and variables are capped. Screenshots are observations of approved **public** pages, not a general sensitive-data redaction system.

## Residual risks — restrictions are mandatory

This development host does not provide a verified outbound firewall. An application proxy and Chromium command-line settings do **not** prove that every present/future browser subsystem uses that proxy. Browser vulnerabilities, DNS resolver traffic, WebRTC changes, alternative protocols, and container/network configuration remain possible gaps. The controlled allowlist is mandatory; there is no unrestricted mode. Do not store cloud secrets, credentials, or private files in a browser-accessible deployment. A Codespace may have developer credentials in its environment; do not treat it as an isolation boundary for arbitrary hostile pages.

The proxy checks destination IPs, not website trustworthiness. A trusted public host can change or serve malicious JavaScript. A single browser process shares resources across contexts. Application caps do not enforce per-context CPU or heap quotas; a hostile page can still exhaust resources. The supplied devcontainer caps the overall container at 2 GiB and two CPUs, subject to runtime support. Outside that container, operators must apply their own limits.

GET/HEAD is not a proof of non-destructiveness: websites can implement state changes with GET, and page scripts run naturally. Use only approved public test pages with no authentication. Do not bypass CAPTCHA, authentication, paywalls or access controls.

Session-close on tab exit is best effort. The reaper and process shutdown provide fallback cleanup. A screenshot can differ from the next DOM observation on animated or self-updating pages. API-only checks do not establish browser behavior: read the delivery test report.

## Test-only access

Tests start one local HTTP server on an ephemeral loopback port. `backend/tests/conftest.py` injects an exact-origin policy and exact-IP resolver **only** into a test manager. Production `app.main:app` never imports that code and offers no localhost bypass flag. Proxy unit tests use local fixture overrides to test transport without weakening production policy.

## Before any wider deployment

Enforce an outbound firewall/proxy boundary that blocks all browser direct egress, isolate the browser from application/developer credentials, add authentication and request-rate limits, enforce total transfer/CPU/memory budgets per session, and independently test redirects, mixed DNS answers, rebinding, IPv6, WebRTC, service-worker and popup paths. Update and audit browser/dependencies regularly. The current version is not approved for an unrestricted public deployment.
