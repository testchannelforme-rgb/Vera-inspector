# V0.3.1 security preservation

This accuracy update does not alter browser launch flags, network/proxy validation, Docker/Compose services, seccomp, devcontainer, credentials, origin/body restrictions or provider integration. No dependency upgrade is introduced. Only .dockerignore/.gitignore exclude the new installer folder/backups/ZIP; main.py changes version metadata only.

Scored ancestor detection, candidate discovery, priority/byte admission and style factoring remain bounded. IDs/parents are not invented, and untrusted page strings stay quoted as data. Shared styles represent sanitized measured equality, not trusted authored instructions. CSS internal whitespace is preserved; privacy removals/length cuts are reported. Composed private ancestors are checked with a bounded fail-closed walk, and values/editable copy/HTML/cookies/storage/signed URLs remain excluded. Visible-text redaction still cannot guarantee removal of all personal information. Existing output remains an editable React textarea without executable HTML/code.

The new packaged installer refuses wrong branches, dirty tracked source, baseline conflicts, symlink/path escapes and checksum mismatches. Rollback refuses later edits before restoring files. Neither implementation nor packaging changes main or deploys anything. Real browser/Docker/network-isolation execution was unavailable here; see TEST_REPORT.md. The following V0.3/V0.2 security context still applies.

---

# V0.3 prompt-generation security additions

V0.2 browser sandboxing, isolated networks, firewall rules, proxy pinning, URL restrictions, quotas and private forwarding remain in place. Only the app service receives optional AI credentials; no credential is added to the browser service or frontend. The production app now includes pinned HTTPX for the optional adapter.

Prompt requests accept server-side session/frame/element references only. Collection has bounded time, traversal and byte budgets; HTML, input values, cookies and storage are excluded. Visible text redaction is best effort, not a guarantee that all personal data is removed. Local mode is the default. AI mode explicitly sends reduced page evidence to the configured provider; do not inspect private content. Payloads and provider responses are not logged or persisted by this feature.

The provider endpoint is trusted administrator configuration, not an API request field. HTTPS/443 only, no credentials/query/fragment, public destination checks on every proxy connection, numeric IP pinning, verified TLS, no redirects, no inherited environment proxies, bounded response bytes and total time. No automatic retries. Private/local provider servers are unsupported. The credential is an Authorization header and is never placed in the model messages. A response containing that exact credential is rejected. Provider errors return generic warnings and local fallback; malformed optional configuration disables AI.

Separate system instructions and JSON-encoded untrusted evidence reduce prompt-injection impact. There are no model tools, browser actions or secrets in model context. AI prose remains untrusted interpretation and may still be wrong or instruction-bearing; it is labelled and appended to authoritative measured sections. No complete prompt-injection immunity or hallucination prevention is claimed. Downstream coding tools must treat page copy as data. React displays output only as editable text; no unsafe HTML, script or generated code execution is added.

Rate limits are in-process for the supplied one-worker private app. They do not replace public authentication, provider spending controls or multi-user isolation. The V0.3 adapter was tested with mocked providers and a real local-proxy denial path; no live-key request or Docker/Codespaces test ran here. See [docs/PROMPTS.md](docs/PROMPTS.md) and [TEST_REPORT.md](TEST_REPORT.md).

---

# V0.2 security model

**Not a security certification.** The public-isolation implementation was not executed in this delivery host: it has no Docker and cannot launch protected Chromium. Validate it on the target host. Universal access is not enabled by deleting the allowlist or using `*`.

## Two modes

**Restricted local:** one local sandboxed Chromium process; exact public-host allowlist; application-level routing and a validating local proxy. This mode lacks a verified OS egress boundary and therefore remains restricted. There is no unrestricted direct-browser option.

**Isolated public:** `compose.inspection.yml` separates the trusted app/controller, sandboxed browser and outbound gateway. Browser networks are internal. Its startup firewall defaults both IPv4 and IPv6 OUTPUT to DROP, allowing established replies and new TCP connections only to the fixed gateway `172.30.88.2:8888`. It does not allow browser-originated connections to loopback, Docker DNS, the control service, application service, metadata or public Internet directly. The gateway has Internet access; the browser does not. No browser/gateway port is published; only app port 8000 binds to host loopback.

The browser entrypoint needs NET_ADMIN only in its own dedicated network namespace to install rules. It drops all bounding/inheritable/ambient capabilities and switches to non-root `pwuser` before launching Chromium with `chromiumSandbox:true`. If firewall or sandbox setup fails, no permissive fallback runs. Chromium is not launched inside the trusted privileged Docker-in-Docker controller.

A random 256-bit browser-control path and proxy password are generated under private `.veyra-runtime`. Compose mounts these capabilities only into the services needing them. No workspace or Docker socket is mounted into the website browser. The password/token are not returned by the API or included in inspection JSON. Host parent directory permissions restrict access; individual secret bind files are readable across service UIDs. Protect the host and its Docker administrator account.

The browser writes sandbox/firewall readiness metadata tied to the control token hash. The app requires it in public mode. This is configuration evidence from trusted startup code, not hardware attestation and not a defense against a malicious Docker administrator. The start script also checks the live proxy port, a live gateway canary on a forbidden port, loopback control access, metadata and direct public IPv4/IPv6. These runtime tests must pass on the actual host.

## URL and connection policy

- Normalize bare hostnames to HTTPS, preserve explicitly supported HTTP/HTTPS, reject malformed/unsupported schemes, credentials, whitespace/control/backslash ambiguities and unusual ports.
- Canonicalize IDNs/IPv6/default ports. Reject alternate numeric IPv4 forms rather than relying on inconsistent Python/Chromium parsing.
- Reject private, loopback, link-local, multicast, reserved and non-global IPv4/IPv6. Check mapped IPv4; block transition/NAT64 prefixes that can encode unsafe IPv4 and the public-looking Azure platform address. Reject local/internal names and single-label hosts.
- Validate every DNS answer, including mixed public/private answers. Repeat validation at the gateway and connect to a vetted **numeric IP**, avoiding DNS rebinding/TOCTOU for proxied connections. Prefer an available IPv4 result where dual-stack connectivity differs; IPv6-only public destinations require gateway IPv6 reachability.
- The firewall prevents browser subresources or alternative browser networking features from bypassing the proxy. Redirects to new authorities require another validated proxy connection. Existing TLS tunnels remain pinned to their vetted peer; TLS is end-to-end with certificate verification intact. No TLS interception or ignore-certificate setting is used.
- Playwright routing additionally validates subresources and limits methods/body sizes, blocks media, service workers, WebSockets, downloads and popups. HTTPS GET/HEAD/POST/OPTIONS support dynamic public APIs; no remote destructive click/input endpoint exists. Plain HTTP proxying remains GET/HEAD-only.

## Resource/privacy limits

Two isolated contexts; one browser process; 600-second absolute / 180-second idle session expiry; 600 routed requests per session. Navigation timeout 20 seconds; readiness budget 5 seconds; operation budget 35 seconds; screenshots 5 seconds. Proxy: 48 simultaneous connections, 16 KiB headers, 24 MiB bidirectional transfer per connection, 90-second connection life and 10-second read-idle limit. These can interrupt complex websites.

Compose limits browser memory to 1200 MiB, app to 512 MiB and gateway to 256 MiB, with CPU/PID/shared-memory bounds. These are per-service limits, not per-context heap isolation or total per-session transfer accounting. A hostile page can still exhaust a shared browser process. The gateway can access the configured DNS resolver; DNS is not resolved by the untrusted browser. A compromised gateway/controller, host or kernel is outside these boundaries.

The API remains a private development service without user authentication or public abuse controls. Session IDs are capabilities; access logging is disabled in the start command. Origin checks, custom write headers, no permissive CORS, request-body cap, no-cache responses, framing denial and UI CSP remain. Credentials and raw console text are not captured for diagnostics; diagnostic network locations omit paths and query strings. Startup control URLs are redacted. Existing source URL fields in inspection JSON may contain user-supplied queries; never inspect URLs containing credentials or secrets.

The existing HTML evidence sanitation and size caps remain. Screenshots and public text are observations, not privacy-redacted assets. Public site scripts execute naturally and may have GET/POST side effects even without a click. Use only sites you are authorized to inspect; do not log in, bypass CAPTCHA/authentication/paywalls or collect sensitive information.

## Residual restrictions and verification

The isolated deployment depends on Docker namespace/capability/netfilter behavior, the supplied image build and the host kernel. Configuration checks and unit tests do not prove these runtime properties. Codespaces rebuild/stop-start tests and public-site tests remain outstanding. Do not publish an unrestricted public service on the basis of this patch.

The local deterministic fixture has an exact ephemeral loopback-origin exception and resolver override in tests only. Production never imports it. The UI test injects the same exact-origin normalizer exception within pytest scope only; no production localhost bypass flag exists.
