# V0.3.2 manual acceptance — run on your working Codespace

These checks were **not** performed here because Chromium/Docker were unavailable. Use only public non-sensitive pages; do not bypass access controls. Keep port 8000 Private and choose Local generation.

1. Start `bash start.sh --isolated`; verify readiness and the V0.3.2 badge. Load example.com, select a heading, inspect CSS, export JSON and generate an Element prompt. Confirm the eight numbered sections, actual text and dimensions. Edit/copy/regenerate; check tablet and narrow desktop widths.
2. Open unrelated accessible public sites such as a documentation page (docs.python.org), an encyclopedia article (wikipedia.org) and a public portfolio/e-commerce/SaaS page of your choice. Record exact URL, date, inspected viewport, scope, result and any block. These are test candidates, not claimed supported-site results. A CAPTCHA/denial should be reported without bypass.
3. On a real gradient/background page, select a transparent heading. In Element output verify its own background stays transparent; ancestor context names the background owner, parameters and position/size when captured. Do not accept a prompt that instructs putting the whole ancestor gradient on that child.
4. Select inside hero, card and navigation regions. Section scope should remain local and explain its boundary. Page scope should report a visible bounded sample. Ensure important late headings/buttons/media retain ancestor IDs. Off-screen content must not be presented as fully inspected.
5. For a gradient-filled heading, compare computed background-clip/text-fill and exact gradient values with the browser. Confirm computed `color` is not incorrectly instructed as an additional opaque layer. For overlapping same-copy text verify the output says possible composition/state/accessibility alternatives and keeps both DOM/style records. Separate nonoverlapping repeated headings must remain independent.
6. Where generated decoration exists, confirm `Node N::before/::after` owner, content classification and computed dimensions/offsets; no invented pseudo rectangle. Check masks/shadows/transforms/opacity/overflow, SVG placement and loaded/missing image status when available. Omitted assets must be identified, not invented.
7. Capture Hover on a harmless control. Generate again; distinguish measured changes from declarations/recommendations. Verify URL loading, selection overlay, scrolling, animation capture and JSON export still work.
8. Try all three scopes, targets, detail levels and fidelity preferences. Concise may cover fewer nodes but included CSS must reconstruct exactly from its referenced groups and specific values. No-key operation must work; optional AI is unnecessary for acceptance.
9. Run `bash scripts/test.sh --public`, then `.venv/bin/python scripts/test_public.py` and `.venv/bin/python scripts/test_prompt_public.py` against the isolated stack. Record failures/skips; never change CSP, sandbox or network policy to get a green result.

## Reproducible controlled visual fixture

`backend/tests/fixtures/visual.html` contains two gradient layers, transparent/clipped text, overlapping text alternatives, conic pseudo decoration, masked imagery, cards/buttons and a narrow-screen media rule. Protected-browser tests exercise Element/Section/Page plus an independently inspected 390px state. Run:

```bash
.venv/bin/python -m pytest -q -rs backend/tests/test_visual_browser.py
```

The existing test-only local origin exception is isolated to the test manager; never configure production browsing to access internal URLs. The tests do not discover an authored breakpoint or calculate visual similarity.

For optional manual recreation evaluation, save the prompt and observed viewport, ask your coding tool to implement it with authorized assets, and compare at the same viewport/state. Label human judgments separately from any future automated image difference. No recreation or screenshot comparison has been generated/tested as part of this update; do not invent accuracy scores.
