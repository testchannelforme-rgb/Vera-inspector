# Manual acceptance on your working Codespace

Keep port 8000 Private. Save existing work and install on `feature/v0.3.1-prompt-accuracy` using UPGRADE.md. Run `bash start.sh --isolated`. Do not disable sandbox/firewall checks if startup fails. These steps were **not** executed against real websites in the delivery environment.

## Regression checks

- Open `example.com` without typing a scheme. Confirm the real preview appears, tap a heading/link, check overlay and measured CSS, export JSON and confirm `schemaVersion` remains 0.1.
- Refresh, reload, scroll, clear and close/reopen a session. Confirm old selections/prompts do not get reused for a different frame.
- On a public site with a hoverable button, use Motion → Capture hover, then local element generation. Confirm the prompt includes actual interval/duration/changes and does not invent a resting state if the baseline was already hovered.
- Edit generated text, copy it and regenerate. Check that copying includes your edits and regeneration replaces them. Check desktop/tablet and mobile widths. No redesigned UI or horizontal page overflow should appear.

## Boundary precision on accessible public sites

Use a public page you can access in the remote browser, for example `react.dev` if available. No CAPTCHA, authentication or access restriction should be bypassed.

1. Tap a heading inside a visible hero. Choose Section → Detailed → Local. Compare the boundary tag/reasons and hierarchy with the visible hero. It should generally remain local instead of expanding to main/body.
2. Select a heading or button inside a visible card. Generate Section. Check whether the card or a coherent local group is selected, rather than unrelated sections. A heuristic can choose a different reasonable boundary; record the DOM/screenshot context for failures.
3. Select a navigation item. Generate Section. Check that unrelated hero/footer content is not included. Review candidate rejection reasons for broad wrappers.
4. Repeat on a page with div-based containers and no convenient section tags. Expect a painted/layout container or the documented local fallback, with explanation.
5. Select the main/body wrapper itself and request Section. Expect a clear request to choose a local child or use page scope, not a silent page-wide section prompt. Element/page modes should still work.

Observe the existing 3 generation attempts/session/minute and 10/global/minute limits. Wait one minute between batches rather than mistaking a rate-limit response for an accuracy failure.

## Prompt fidelity

- Try Element, Section and Page; all three targets; Concise, Detailed and Highly detailed. Recommendations must stay separate from measurements.
- Confirm headings, selected content, important buttons and images survive a bounded sample, even when early generic nodes are numerous. Every included non-root node must reference an included parent; source IDs must not be renumbered.
- For a static selected element, compare computed CSS in the inspector/JSON with the prompt's referenced shared groups plus node-specific values. Included values should reconstruct exactly after disclosed privacy/length limits. Do not compare different hover/dynamic states as simultaneous observations.
- Confirm typography, colors, borders, shadows, flex/grid/gaps and geometry retain numerical precision. Shared groups must state equality of observed values, not unproven inheritance.
- Confirm content/assets have node references, missing asset URLs stay omitted, responsive breakpoints remain unmeasured, and dropdown/navigation indicators are not described as tested behavior.
- Check coverage/omission warnings. Full page still means currently visible bounded content; it must not promise an inspected entire scrollable site.
- Leave Local selected without any API key. Generation must work. Optional configured AI remains supplementary; this update does not certify a live provider.

## Deterministic browser fixture suite

The fixture HTML contains known hero/card/nav/nonsemantic/direct-main/fallback structures. It is served only by tests using the existing local test-policy exception:

```bash
bash scripts/setup.sh
.venv/bin/python -m pytest -q -rs backend/tests/test_prompt_browser.py
npm --prefix frontend test
.venv/bin/python -m pytest -q -rs
bash scripts/test.sh --public
```

The Node collector tests use synthetic DOM rectangles; they are algorithm checks and cannot substitute for the browser suite. Browser tests require the supplied sandbox-capable non-root devcontainer. Public smoke scripts are available after the isolated stack starts:

```bash
.venv/bin/python scripts/test_public.py
.venv/bin/python scripts/test_prompt_public.py
```

Do not mark acceptance complete if Chromium, real site rendering or the manual fidelity checks fail. Save nonsensitive diagnostics and the boundary decision; avoid sharing credentials or private page content.
