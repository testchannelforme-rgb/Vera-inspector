# Veyra AI V0.3.1 — actual verification report

25 October 2026, IST.

**Implementation and automated algorithm/regression checks delivered. Real-browser/real-site acceptance remains unverified on this host.** The attached `Veyra_V0.3_Clean_For_Sol.zip` was extracted and used as the primary baseline. No private GitHub access, remote checkout, main modification, deployment or paid service was used. Development is on the local `feature/v0.3.1-prompt-accuracy` branch.

## Findings and delivered changes

Source audit confirmed broad `closest(...main...)` section expansion, prefix-based renderer selection, prefix-based byte truncation, per-node CSS repetition and property removal in Concise mode. V0.3 scopes/targets/detail/style options, no-key fallback, optional provider, edit/copy/regenerate, current API shape and browser isolation were present in the attachment.

The update adds scored local boundaries with explanations/rejections, pinned selected ancestry and bounded breadth-first candidate discovery, importance-aware admission at collection/time/byte/detail stages, unchanged IDs and true sibling order, exact reversible shared-style groups, complete included sanitized CSS across detail modes, richer measured CSS/geometry/accessibility evidence and explicitly labelled recommendations/limitations. An explicit page-wrapper selection in section mode yields a useful 422 instead of a giant section. Element/page behavior remains available.

## Actual tests

| Check | Result |
| --- | --- |
| Attached baseline Python suite | 165 passed, 10 skipped |
| Updated Python suite | **214 passed, 16 skipped**, one existing Starlette/HTTPX deprecation warning |
| Updated Node suite | **34 passed**, zero failed; includes existing frontend/coordinate tests and 19 new collector/boundary algorithm tests |
| Frontend production build | Passed, Vite 8.3.5 |
| Python compileall | Passed |
| Collector and boundary JavaScript syntax | Passed |
| Python dependency consistency (`pip check`) | Passed |
| npm audit | Zero reported known vulnerabilities; not an OS/security certification |
| Actual HTTP server smoke | Frontend 200, health 200 and app version 0.3.1 |
| Protected/core source hash comparison against attachment | **29 files byte-identical** |
| Strict browser probe | **Failed**, `browser-binary-missing`; protected Chromium executable is absent |
| `bash scripts/test.sh --public` | **Exit 1** at the mandatory browser probe; preceding Python/Node/build checks passed |
| Real website inspection and section fidelity in V0.3.1 | Not verified here |
| Codespaces/Docker execution | Not run; Docker unavailable here |
| Live AI provider | Not called; existing mocked adapter/fallback tests passed |
| Visual device/browser clipboard validation | Not run in a real browser; actual React component behavior is Node-tested |

The final Node count includes two additional CSS-materialization/shadow-ancestry regressions added after the strict command's earlier Node run; the final standalone Node run passed all 34. The unchanged strict failure remains the missing browser, not an application test failure.

The 16 skipped tests comprise the existing 10 browser-dependent checks plus six new real-browser hero/card/nav/nonsemantic/direct-main/fallback cases. The existing sandbox requirement was not disabled. Synthetic DOM rectangles are explicit test inputs, not observed website measurements or evidence of public-site compatibility. No screenshot or fabricated browser inspection output is supplied as a successful test.

## Coverage of the accuracy changes

- Hero heading → section, nested card → local article, nav link → navigation, painted nonsemantic card → local div.
- Direct-main fallback; tall wrapper and unrelated-landmark rejection; explicit page-wrapper section requests ask for a local child.
- Late CTA/image retention after early generic nodes; 1,400-sibling selected ancestry retention; true sibling indices; 1,500-node/55-output bounds and time-cutoff reporting.
- Priority-preserving **CSS materialization** under a time cutoff (not reverting to discovery-prefix loss).
- Ancestor closure, deep selected paths exceeding nominal detail counts, unchanged IDs, invalid/orphan/cycle handling and selected-node omission warnings.
- Lossless shared-style reconstruction, overlapping memberships, all included properties retained in Concise, CSS whitespace preservation, exact numerical values and flagged sanitization/length cuts.
- Every combination of three scopes × three detail levels × three output targets; missing/empty/truncated evidence; no-key local fallback and maximum-size sanitized evidence.
- Measured gradients preserved; signed assets/private values/editable/shadow-private copy excluded; existing URL/DNS/proxy/API/session/security/provider regressions.
- Installer branch/dirty-work guards, committed baseline conflicts, checksum/path/symlink checks, backup/rollback and refusal to clobber later edits.

## Reproduce in Codespaces

```bash
bash scripts/setup.sh
.venv/bin/python -m pytest -q -rs
npm --prefix frontend test
npm --prefix frontend run build
bash scripts/test.sh --public
```

Run the deterministic actual-browser section cases separately with:

```bash
.venv/bin/python -m pytest -q -rs backend/tests/test_prompt_browser.py
```

After the existing isolated stack starts, use `scripts/test_public.py`, `scripts/test_prompt_public.py` and the [manual acceptance checklist](docs/V031_ACCEPTANCE.md). The optional `--ai` public probe deliberately consumes configured provider quota and is not required for local-mode testing.

## Limitations and remaining acceptance

Section scoring is heuristic; tall heroes, unusual markup and ambiguous components can yield conservative/incorrect boundaries. Collection remains visible-only and bounded, not a full scroll crawl. Visibility/viewport intersection does not fully solve clipping, stacking, fixed descendants under excluded ancestors or pixel occlusion. Byte/detail limits can omit important content; selected coverage/omissions are disclosed. CSS values over 180 characters or privacy-sensitive strings are flagged, not described as fully exact originals. No hidden interaction, authored stylesheet, original asset, unobserved responsive breakpoint, iframe/closed-shadow/canvas internals or live-provider behavior is invented.

Prompt injection defenses, provider configuration and browser/network controls remain as in V0.3. Quoted page/AI text is still untrusted and must be reviewed downstream. No complete segmentation, privacy-redaction or prompt-injection immunity is claimed. Real public-site accuracy, real tablet/mobile rendering and target-host browser/isolation regression acceptance must still be performed; passing synthetic/unit tests does not establish those outcomes.
