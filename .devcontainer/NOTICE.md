seccomp_profile.json is vendored from Microsoft Playwright v1.64.1:
https://github.com/microsoft/playwright/blob/v1.64.1/utils/docker/seccomp_profile.json
Licensed under Apache License 2.0; see LICENSE.playwright.
It keeps the Docker default policy plus namespace permissions needed for Chromium's own sandbox.
This is a container syscall policy, NOT an SSRF egress firewall.
Codespaces runtime support still needs verification; no Codespace was created during delivery.

V0.2 builds on Node 24 / Debian Bookworm and installs pinned Playwright 1.64.1 plus its full Chromium and system dependencies during image build. Newer prebuilt Playwright image tags returned 404 in delivery-time registry checks, so no unavailable image tag is required. Docker-in-Docker is a trusted development-controller capability; the website browser runs in a separate container with a sandbox and its own outbound firewall.
