# DRAFT — Cookie Policy

OWNER REVIEW REQUIRED. Not finalized.

Draft device-storage inventory. No cookie banner is shown because this build does not add analytics, advertising or optional tracking cookies.

## VEYRA interface cookies

The audited frontend and FastAPI application do not set application cookies. No external analytics, font CDN or marketing tag is loaded by this release. Hosting and authentication services may set their own cookies; the owner must disclose the actual hosting configuration before publication.

## Local storage keys

veyra.preferences.v1 stores only historyEnabled and tutorialDismissed booleans after a preference action, tutorial Skip or Finish. It is a functional device preference, not a user identifier. There is no scheduled expiry; clear it in Data preferences or your browser.

veyra.prompt-history.v1 stores explicit prompt snapshots, a user-editable title, timestamp, local version ID and prompt preferences only when history is enabled and you choose Save Version or Duplicate. No automatic saving occurs. It is limited to 20 versions and 512 KiB total; each prompt is limited to 60,000 characters. No server upload is performed by history operations. These locally saved prompts may contain sensitive information you type; device/browser users may be able to read them.

## Remote website storage

An inspected website may set its own cookies, cache or browser storage in its isolated, nonpersistent Chromium context. Those are not cookies in this VEYRA interface. Context disposal and expiry follow the inspection runtime; the inspected website’s own network-side records are outside VEYRA’s control. No logged-in browser profile is imported.

## Change your choices

History is off until you enable it. Disabling it deletes saved versions on this origin. You can clear VEYRA local data without affecting unrelated application keys. A private browser, storage restriction or quota may prevent saving; the editor reports a failure and keeps its open draft. OWNER REVIEW REQUIRED: review whether additional consent or disclosures are needed for the final deployment and its jurisdiction.
