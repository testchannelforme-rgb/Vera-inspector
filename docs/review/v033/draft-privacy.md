# DRAFT — Privacy Policy

OWNER REVIEW REQUIRED. Not finalized.

Draft for owner review. This describes the V0.3.3 review candidate’s source-code behavior, not a statement of legal compliance.

## What the application processes

Opening a URL sends that address to the VEYRA backend. The remote Chromium browser requests the target site and its permitted resources. The target site and network providers can receive the browser server’s IP address and request metadata. Inspected sites may set cookies or browser storage inside that temporary browser context; those are separate from this VEYRA interface’s device storage.

The backend keeps session identifiers, remote browser state, screenshots, selected DOM information, sanitized HTML snippets, computed styles, geometry and hover observations in process memory. Inspection JSON exports can contain visible website text and screenshots. Prompt evidence is separately minimized and excludes raw HTML, form values, editable fields, browser storage and signed asset URLs, but visible text and images may still include personal information. Do not inspect sensitive or authenticated content.

## Lifetime and copies

Default source settings expire inspection sessions after 600 seconds total or 180 seconds idle. The application checks these limits during operations and periodic cleanup. Closing a session disposes its browser context; page-close cleanup is best effort. These are runtime limits, not a guarantee covering crash dumps, infrastructure logs or provider copies.

The app has no prompt-history database. Unsaved editor text is held in the page’s memory. Saved versions are optional browser-local data, retained until you delete them, disable history, clear site data or the browser removes them. Downloads are files you control. No retention duration has been supplied for hosting, operational logs or external AI providers; the owner must document those before a finalized policy.

## Optional external AI

Local generation is the default and makes no model-provider request. If the operator has configured and enabled an external AI provider and you deliberately choose AI mode, reduced inspection evidence is sent from the backend to that configured provider. V0.3.3 asks for a per-generation acknowledgement in the interface. A provider timeout or failure falls back to deterministic generation.

Provider identity, processing location, retention terms and any contractual safeguards depend on the operator’s configuration. The owner has not supplied these details. API credentials remain backend configuration; they are not saved with local prompt versions. The history feature itself does not upload saved prompts. Copying or exporting a prompt and using another service is your separate action.

## Device storage and logs

This interface adds no advertising, analytics or third-party tracking scripts and sets no application cookies. It uses only the local preference and optional prompt-history keys listed in Cookie Policy and Data preferences. Hosting or GitHub Codespaces authentication cookies are controlled by those services, not by this frontend.

The backend records startup and unexpected-operation exceptions. The supplied Uvicorn startup uses standard access logging, which can include request paths and session identifiers. Upstream errors may expose addresses in operational logs. This release does not add an analytics or log-upload service. The owner must review hosting logs, access restrictions and log retention.

## Your controls and owner information

Use Data preferences to enable or disable prompt history, delete all saved versions or clear VEYRA’s two local data keys. Clearing local data does not remove downloaded files, clipboard contents, remote browser sessions or provider/hosting records. Close the browser session in the inspector separately.

OWNER REVIEW REQUIRED: responsible operator/legal identity, contact channel, jurisdiction, hosting providers/regions, provider-specific disclosures, log retention and an appropriate rights/request process have not been supplied. No effective date or finalized legal basis is asserted.
