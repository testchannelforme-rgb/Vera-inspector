# V0.3.3 data-flow audit — draft policy source

This is a code audit, not a legal certification. No jurisdiction or operator identity was supplied. Review this against the final hosting configuration before finalizing any policy.

| Processing | Actual implementation | Persistence / controls |
| --- | --- | --- |
| VEYRA cookies | No `set_cookie`, `document.cookie`, analytics SDK or external tracker added | Hosting/authentication cookies are separate and must be inventoried by the owner |
| Interface preferences | `frontend/src/local-data.js`, `veyra.preferences.v1`: two booleans | Written only after a preference action or tutorial Skip/Finish; clear in Data preferences |
| Prompt versions | `veyra.prompt-history.v1`: explicit text snapshots, title, local ID, time, settings | Off by default; explicit opt-in/save; 20 versions, 512 KiB, 60,000 chars/prompt; no silent eviction; disable deletes history; reports, session tokens and URLs are not saved as separate metadata |
| Unsaved editor | React memory; edited/restored draft is retained when the selection changes, detached from old evidence | No autosave/upload; replacement has an in-memory Undo; unsaved manual edits trigger a page-close warning when supported |
| Remote browser | Existing nonpersistent Chromium context; inspected site may write its own cookies/storage | `Settings.session_ttl=600`, `idle_ttl=180`; checks on operations and periodic cleanup; context disposal on close; page-close cleanup best effort |
| Inspection data | Screenshots, selected DOM, sanitized HTML snippet, computed styles, geometry and hover samples | Server process memory and user-initiated JSON exports. Visible text/screenshots can contain personal data; minimization is not a privacy guarantee |
| Prompt evidence | Existing separate sanitizer excludes raw HTML, input/editable values, storage, private/signed URL paths | Bounded server-owned evidence; quoted untrusted values; no arbitrary client HTML accepted |
| Local generation | Deterministic renderer on backend | No model-provider request; no new persistent server store |
| Optional AI | Existing admin-enabled HTTPS provider adapter, reduced evidence, backend credential | UI mode selection plus per-generation acknowledgement; no history upload; provider/region/retention must be supplied by operator; failure falls back locally |
| Operational logs | Existing `logger.exception` for startup/unexpected failures and default Uvicorn access logging in `start.sh` | Logs can include request/session paths and upstream exception addresses; no log retention or infrastructure access guarantee is known |
| App requests | Same-origin API plus bundled local assets/fonts (system font stack) | No external font/analytics CDN; external GitHub links are navigations the user chooses |
| Inspected-site requests | Existing vetted browser/gateway | Target sites see server-side request metadata and can retain their own logs. Public mode still requires existing Docker isolation proof |

## Settings design

No blanket cookie-consent banner is added. The release adds no tracking/advertising processors. Device history is a genuine optional persistence choice; it has explicit enable/save/delete controls and storage failure feedback. Tutorial dismissal is a functional flag following Skip/Finish. Optional model processing is separately disclosed at generation time. This is not a claim that these controls alone satisfy any law.

## Unresolved owner information

Responsible operator/legal identity, support/privacy channel, jurisdiction, hosting/service providers and regions, log retention, configured AI provider terms, rights/request handling, asset/font licenses and finalized effective dates. No contact address, legal basis or compliance badge is invented.

## Security preserved

Browser manager, sandbox flags, network gate, DNS pinning, isolation proof, TTLs, origin/body/client-header protection, provider credentials and original inspection schema `0.1` remain unchanged. Prompt response schema remains `0.3`; optional `preset` request and nested `evidenceSummary.qualityReport` are additive. Local storage is not encrypted and is accessible to same-origin scripts and device/browser users. React renders saved text as inert text. No HTML/code execution or cloud coding engine was added.
