# V0.4.2 changes

- Central Blue Hour design tokens and selective approved gradient; generated website styling remains isolated.
- Supplied Prism image cropped/resized without redrawing or recoloring. Optimized WebP, favicon PNG and original reference retained as source assets.
- Independent native/fallback editor, inspector and generated-preview fullscreen, plus comparison fullscreen. Code remains mounted; original screenshot selection uses measured image coordinates after resizing.
- Original hover outline via a bounded read-only hit test; existing captured hover analysis remains available.
- Side-by-side original inspection / generated iframe, independent scroll areas, logical viewport matching and explicit one-way original-to-preview scroll synchronization. No remote original-site clicks are introduced.
- Desktop/tablet/mobile/custom viewports, bounded to 320–1440 by 320–1000 CSS pixels. Original viewport updates do not navigate/reload the website.
- Preview click-to-edit uses unique `data-veyra-node` source markers. Unmapped/duplicate identifiers remain explicit, with no guessed source jump.
- Debounced local code drafts, five checkpoints, original-generation checkpoint, 2 MiB total limit, failed-save indicators, cross-tab conflict protection and explicit restore confirmation.
- Error console with bounded/redacted runtime/asset/compiler messages, source-window/token checks, and deliberate AI-fix preparation through existing refinement consent.
- Server-reported progress stages; no fabricated percentages. Generation/refinement provider configuration and quotas remain intact.
- Motion 14.8.0 core and shared motion tokens, reduced-motion behavior, shortcut reference and focus mode.
- Added targeted storage, mapping, progress, bridge, fullscreen, comparison, persistence and security acceptance tests.
