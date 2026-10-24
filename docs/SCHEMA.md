# Inspection JSON schema 0.1

Authoritative model: `backend/app/schemas.py`. Generated JSON Schema: `docs/inspection.schema.json` (Draft 2020-12). Regenerate using `PYTHONPATH=backend .venv/bin/python scripts/export_schema.py`.

Computed style keys use native CSS kebab-case (`background-color`, `font-size`); they are not camelCase. Values are browser-computed strings. These are **not** original authored stylesheet declarations. Numeric geometry is remote viewport CSS pixels. Empty or unavailable metadata uses null or an empty collection, not invented values.

| Field | Meaning |
|---|---|
| `schemaVersion` | Literal `"0.1"`; consumers should reject unsupported versions |
| `capturedAt` | UTC ISO-8601 timestamp for extraction |
| `source` | Final source URL, viewport, DPR, coordinate convention, page scroll, computed style origin |
| `element` | Tag, ID, classes, safe text, sanitized/truncated HTML, selector/scope/uniqueness, session reference, best-effort accessible name/role |
| `geometry` | Actual `getBoundingClientRect()` x/y/width/height and four edges |
| `styles` | Flat computed-property dictionary, including appearance, typography, layout, transitions and CSS animations |
| `styleGroups` | The same computed values organized by purpose |
| `pseudoElements` | Computed `::before` / `::after` when they have non-none/normal content |
| `customProperties` | Up to 100 exposed computed custom properties, each up to 500 characters |
| `animations.metadata` | CSS animation/transition computed metadata |
| `animations.active` | Up to 30 `getAnimations({subtree:false})` records, with timing and up to 30 keyframes each |
| `animations.observations` | Actual hover samples; initially empty |
| `animations.hover` | Initially null; later baseline, timing, baseline-hover flag and before/during/after screenshot data URLs |
| `limitations` | Explicit caveats for this observation |

Each hover sample records `elapsedMs`, real `styles`, `geometry`, `changesFromBaseline` (before/observed pairs), and `activeAnimations`. `detected` means a CSS/active animation or observed visual-property/geometry change was found. A transition declaration alone is metadata; it does not prove that a transition ran.

Infinite animation timing numbers become JSON strings such as `"Infinity"` so output remains valid JSON. The top-level typed fields reject extra keys in 0.1; dictionaries intentionally permit future property names without changing their containers. A breaking shape/meaning change needs a new schemaVersion.

Selectors are best effort and declare their scope and uniqueness at capture time. IDs can repeat and DOM structure can change. The internal element handle is used for active inspection, not re-querying the exported selector. A reference ID expires with its browser session.

HTML is text evidence, not a safe recreation asset or reusable live markup. Input/textarea/select contents, script/style contents, inline events, nonce and srcdoc are stripped. Exported screenshots and public text are not automatically privacy-redacted; use only approved public pages.

## Real examples

The browser tests generate real inspection JSON in `artifacts/` only after assertions pass. No generated example is bundled in this delivery because this host prevented protected Chromium startup. A hand-authored specimen would not satisfy the real-data requirement, so none is presented as captured evidence.
