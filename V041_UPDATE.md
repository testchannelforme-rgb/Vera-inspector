# Veyra AI V0.4.1 update

Baseline: V0.4 commit `1c885d0a7b1419fd972edec896a08c13b28f90a5`. Target branch: `feature/v0.4.1-generation-fidelity`.

Unzip the release outside the repository. Preserve existing uncommitted changes first. The exact feature commit is supplied in `Veyra_AI_V0.4.1.bundle`. From your Veyra repository:

```bash
git status --short
git bundle verify /path/to/Veyra_AI_V0.4.1/Veyra_AI_V0.4.1.bundle
git fetch /path/to/Veyra_AI_V0.4.1/Veyra_AI_V0.4.1.bundle feature/v0.4.1-generation-fidelity:feature/v0.4.1-generation-fidelity
git switch feature/v0.4.1-generation-fidelity
bash scripts/setup.sh
```

If the destination branch exists, use another new branch name; do not force-update it. Push with your own authenticated GitHub access if the release was not remotely pushed.

Alternatively, from your existing repository root, use the incremental installer:

```bash
python3 /path/to/Veyra_AI_V0.4.1/update/apply_update.py --repo . --check
python3 /path/to/Veyra_AI_V0.4.1/update/apply_update.py --repo . --apply
```

It merges against the exact V0.4 baseline, preserves unrelated files and secrets, backs up replacements, and refuses conflicts before writing. Do not copy the source snapshot over a dirty checkout.

Stop the previous Veyra instance deliberately. For Compose, stop with `docker compose -f compose.inspection.yml stop`, then:

```bash
bash start.sh --isolated
python3 scripts/verify-version.py
```

Use private forwarded **8001**. Health must show `0.4.1`, the imported source commit and browser readiness. A source update applied without committing has `sourceDirty: true`; a Git-bundle checkout preserves the exact clean commit identity.

## Optional AI

Code generation is still local unless AI is deliberately selected. Local output is clearly labelled. No API key is bundled and no provider is automatically enabled. The UI distinguishes configured providers from a successful live inference.

Configure independent code/refinement/repair providers through `.env.example`. `VEYRA_CODE_AI_MAX_OUTPUT_TOKENS` and `VEYRA_REPAIR_AI_MAX_OUTPUT_TOKENS` default to 8192 (bounded 128–12000). Prompt generation retains its earlier budget. The existing timeout remains 1–20 seconds; incomplete responses are rejected, never silently accepted as complete code.

Repair requires `VEYRA_REPAIR_AI_ENABLED=true`, its model/key/endpoint, and the user's separate opt-in plus consent to send code/evidence. Maximum **one repair attempt** per generation; it consumes one refinement allowance. Screenshots stay local and are never sent to a model. Embedded selected source images can be included in generation evidence only with the explicit AI consent shown in the UI. Code and evidence may contain private information; review before consenting.

Local startup uses exported shell environment variables. Compose reads `.env` and forwards documented settings. Keep secrets out of frontend variables and Git.

## Comparison and limitations

Reference screenshots are captured once from the current selection. The protected existing browser renders preview code offline at the same viewport, with all subresource/network requests blocked. Screenshots stay in bounded in-memory operation data and are discarded after comparison; no screenshot files are accumulated. Comparison reports mean channel error (0–255), root-relative box error, style mismatch count, missing nodes, overflow and runtime errors. It is not an accuracy percentage.

Comparison can be unavailable if the protected browser is not ready, the crop is offscreen/too large, the compiler fails or the operation times out. Existing code generation/editing/preview still work. Only a successfully validated candidate with lower combined discrepancy, no runtime errors and no additional missing mapped nodes replaces the prior result. Missing map IDs are penalized. No unbounded repair loop or silent generic fallback is added.

Origin-clean, already-loaded raster images up to 512px can be embedded within a 64KB budget. CORS-tainted images, external fonts, SVG artwork and background image URLs remain limited. No network/SSRF/CORS protection is bypassed. Font names and measured typography remain; external font files are not downloaded. Menu actions, original application state, keyframe rules and offscreen responsive states remain unknown unless already captured. No new remote-click inspection is introduced.

The preview remains an opaque-origin development sandbox, not a VM or complete CPU/navigation firewall. Keep the deployment private. Fresh Docker/protected-browser and live-provider checks must still be run in your actual Codespace.
