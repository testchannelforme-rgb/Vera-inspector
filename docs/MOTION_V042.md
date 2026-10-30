# V0.4.2 motion dependency decision

Evaluated Motion for React and Animate.css using their official documentation on 30 October 2026. Motion's core is MIT licensed; Animate.css's current site documents the Hippocratic License, so it was not assumed to be MIT. Selected one primary library: Motion 14.8.0 (exact npm lock), compatible with the installed React 19 peer range. No Motion+ examples or premium assets were copied.

Motion supplies stage-entry animation and its useReducedMotion hook. Existing host transitions share `--motion-fast`, `--motion-normal`, and `--motion-ease`; CSS handles simple color/focus/hover feedback without additional libraries. `prefers-reduced-motion` disables host transitions and reduces animation duration. Generated project bundles do not import Motion or the host stylesheet.

Primary documentation: https://motion.dev/docs/react , https://motion.dev/docs/react-use-reduced-motion , https://www.motion.dev/ , https://animate.style/ . The installed license is retained at `frontend/node_modules/motion/LICENSE.md` during dependency installation; dependencies are excluded from the release ZIP and recovered from the lockfile.
