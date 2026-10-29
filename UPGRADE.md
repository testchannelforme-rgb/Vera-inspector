# V0.3.3 review candidate — safe update notes

Baseline: 349db3b671fc77c543b5073cdb85cd9a0a115b6e. Development branch: feature/v0.3.3-ui-prompt-polish. Branding, design and policies remain provisional.

1. Inspect git status -sb. Preserve uncommitted work; do not reset, clean, stash automatically or overwrite it. The original seven Codespace files were hash-checked during this upgrade and retained.
2. Use the V0.3.3 development branch. If obtaining it from GitHub, fetch the exact branch and switch only after checking for conflicting local paths. Do not merge into main or force-push.
3. Run npm --prefix frontend ci, then npm --prefix frontend run build. No dependency or browser image version was upgraded.
4. Start the existing private development stack with bash start.sh --isolated. This repository retains app port 8001 in compose.inspection.yml; keep forwarding Private. Restricted local bash start.sh uses port 8000.
5. Open /#/ for the landing page and /#/inspector for the workspace. Review /#/brand and the draft legal pages before finalization.

Full validation and host limits are recorded in TEST_REPORT.md; feature review and owner decisions are in docs/V033_REVIEW.md. Do not disable the Chromium sandbox or change URL/network policy to make a failed check pass.

No production deployment, main merge, repository visibility change or external AI activation is part of this update. Rollback by returning to the preserved V0.3.2 branch only after protecting any current changes; never reset or copy an old archive over this branch.
