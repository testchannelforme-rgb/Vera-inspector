seccomp_profile.json is vendored from Microsoft Playwright v1.64.1:
https://github.com/microsoft/playwright/blob/v1.64.1/utils/docker/seccomp_profile.json
Licensed under Apache License 2.0; see LICENSE.playwright.
It keeps the Docker default policy plus namespace permissions needed for Chromium's own sandbox.
This is a container syscall policy, NOT an SSRF egress firewall.
Codespaces runtime support still needs verification; no Codespace was created during delivery.
