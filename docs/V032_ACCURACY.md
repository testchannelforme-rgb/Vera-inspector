# V0.3.2 visual evidence design

## Source and compatibility

Implementation baseline: supplied `Veyra_V0.3_Clean_For_Sol.zip` plus manifest-verified `Veyra_AI_V0.3.1_Update.zip`, safely applied to a fresh local working tree. GitHub returned 404 for the private repository; Codespaces was not accessible. Local baseline commit `aac056d` records these supplied bytes, not remote checkpoint `29ef127`. No previous V0.3.2 draft was used. Package manifest records source archive SHA-256s, touched-file preimages and untouched API/evidence anchors. Unknown newer touched files/anchors cause a safe stop. Unrelated local source is not included or overwritten.

## Four evidence categories

1. **Direct CSS:** sanitized exact computed strings belonging to an included DOM node or its generated pseudo. Exact style factoring remains reversible; no approximate color summaries replace values.
2. **Observed context:** bounded ancestor/nearby CSS and bounding rectangles, with separate owner IDs. An ancestor's gradient is never assigned to its transparent child. Context does not expand the selected content boundary.
3. **Inferences:** matching direct copy + at least 80% smaller-rectangle overlap + related DOM + layering CSS can indicate text composition/state/accessibility alternatives. Connected candidate groups are labelled uncertain. No merging/reparenting occurs. Nearby context uses at least 50% target-rectangle overlap, absolute/fixed positioning and paint or matching copy; metadata does not establish paint order.
4. **Unknowns:** no final pixel colors, occlusion, complete stacking tree, pseudo bounding rectangles, font files, exact assets, other responsive states or hidden interactions are established.

## Capture

`visual.js` reads non-default paint properties, background/mask layers, text fill/clip/stroke/shadow, filters, blend modes, isolation, transforms, positioning, opacity, clipping and image availability. It makes no network requests, DOM changes or screenshot transfers. Gradients preserve CSS layer order; background sizing/position/clip/origin/blending retain owner attribution. External asset layers are placeholders and must never be pasted as executable CSS.

Generated pseudo-elements are read only when computed content is not none/normal and display is not none. Their own computed dimensions/offsets, paint and bounded sanitized content are associated with the DOM owner. Generated content on private/form/editable owners is excluded. CSS `content` references, attr/counter forms and CSS URL references are omitted. Images report observed completion/natural dimensions as loaded/unavailable/pending/unknown; this does not recover assets. SVG/canvas/video remain placement evidence, not reconstructed internals.

## Limits and prioritization

Existing 120 ms collection budget (including boundary/visual work), 95 ms discovery cutoff, 1,500 visited/queued nodes, depth 16 and 55 materialized nodes remain. No timer or screenshot loop was added. Clock bounds are cooperative and cannot interrupt a single browser style/layout read; the existing 5-second collection timeout remains.

Added bounds: six ancestor levels, 24 sibling checks at the nearest two non-page-level ancestors, two nearby records, eight pseudo records across nodes/context, two per owner; maximum eight background layers/function depth 16/input 8,192 characters. Browser visual maps are capped at 3,500 JSON characters, context 10,000; source nodes 110,000 aggregate characters and declared total envelope cap 128,000 characters. Worst-case UTF-8 cost can exceed character counts; backend byte limits are authoritative.

Selected/root and ancestor chains retain priority. Paint owners, masks/text layers and distinctive decoration gain priority alongside headings/controls/media. Context is read after the root, before generic descendants; it can consume time/pseudo coverage, which is reported. It does not scan a whole page for decorations.

Sanitized backend evidence remains **48,000 ASCII-JSON bytes**, including context and the existing 6,500-byte hover reserve. Context is limited to about 5,500 bytes plus bounded coverage; individual context/pseudo style maps to 2,500 bytes. Critical visual properties are prioritized there. Relevant visual CSS can retain up to **1,024 characters** (previous generic cap 180); other CSS retains 180. This explicit bounded increase protects gradient parameters without increasing the total provider/evidence budget. Omitted/truncated/privacy-modified fields and coverage remain visible. In extreme samples selected-node omission is disclosed, or generation returns a clear size error; choose a smaller target/detail.

## Output and contracts

The eight numbered sections, request/response schema, internal `0.3-evidence` label and raw inspection `0.1` JSON are retained. New internal optional `node.visual`, `visualContext`, image availability and aria-hidden metadata are additive. The existing frontend requires no new control. Composition summary appears within Objective; precise CSS still appears through shared groups/node-specific maps plus separately attributed pseudo/context records. Old V0.3.1 evidence without these fields remains supported.

No-key local generation is independent of AI. Existing optional provider receives only bounded sanitized evidence, never raw DOM, cookies or screenshots. AI prose remains separate interpretation. Live provider integration was not revalidated.

## Security

Network policy, DNS-pinned egress, browser sandbox settings, Docker rules, same-origin/API protections, CSP, rate limits and raw inspection code were left unchanged. New metadata is whitelisted, unknown fields discarded and coordinates required finite. CSS is length-bounded before regex redaction; control bytes are normalized before URL checks. Escapes/comments/URL-bearing CSS references are omitted; text/token redaction remains best effort, not PII classification. Collected content remains untrusted quoted evidence, never executable markup or governing instructions.

## Why no pixel sampling

No pixel colors or screenshot similarity claims are made. CSS/geometry attribution addresses the known failure modes with no new imaging dependency or third-party transfer. Chromium was unavailable for trustworthy pixel calibration/verification, so adding an unverified sampler would create misleading evidence. Optional future local pixel sampling should be tested under the protected browser and preserve privacy/budgets first.

## Remaining limits

This is not universal website segmentation or visual reverse engineering. Complex stacking/masks, image-set/URL asset internals, transformed/rotated overlap, pseudo occlusion, duplicated states, authored breakpoints, WebGL/canvas and closed/cross-origin content can remain uncertain. Unseen decoration outside the bounded ancestor/sibling neighborhood may be omitted. Computed border boxes do not prove pixel visibility. No reconstruction image comparison or fidelity percentage was performed. Real-site quality needs the manual/browser acceptance steps on a working host.
