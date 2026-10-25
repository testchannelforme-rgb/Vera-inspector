# Prompt generation contract 0.3

`POST /api/prompts/generate`, same-origin and the existing `X-Veyra-Client: inspector-v0.1` header. The header value is retained for compatibility with V0.2. Request bodies remain limited to 8 KiB and extra fields are forbidden. Website text/HTML/URLs cannot be supplied by the client.

```json
{
  "sessionId": "CURRENT_SESSION_TOKEN",
  "frameId": "CURRENT_FRAME_ID",
  "referenceId": "CURRENT_SELECTION_REFERENCE",
  "scope": "element",
  "target": "react",
  "detail": "detailed",
  "style": "faithful",
  "mode": "local"
}
```

Enums: scope `element|section|page`; target `html-css|html-css-js|react`; detail `concise|detailed|highly-detailed`; style `faithful|responsive|accessible`; mode `local|auto`. Page needs no selection/reference; the other scopes require the active retained element reference. All scopes require the current screenshot frame ID. A fresh snapshot is collected under the existing session operation lock and a separate five-second evidence deadline. The provider runs after that browser lock is released.

Success includes `schemaVersion: "0.3"`, `generationId`, `prompt`, `mode: "ai"|"fallback"`, nullable provider/model metadata, warnings and an evidence summary (root tag, scope/boundary, sample count, viewport, capture timestamp and truncation flag). Inspection JSON remains schema 0.1. Typical failures: 409 stale selection/frame, 404 closed session, 422 no visible/safe target or malformed body, 429 concurrent/rate-limited generation. Provider failures return a 200 fallback result with a safe warning; raw provider errors are discarded.

Collection bounds: 55 visible nodes, at most 1,500 visited nodes, 16 levels, 120 ms best-effort page traversal budget, 48,000 serialized evidence bytes. A process may briefly exceed the traversal time in one DOM operation. The five-second backend deadline and existing browser resource limits remain the outer bounds. Detail modes describe up to 4/12/28 sampled nodes. These are bounded snapshots, not crawling or full-page coverage. Root and child rectangles use viewport CSS pixels. SVG placement/fill/stroke can be observed; paths, canvas and WebGL internals are not reconstructed.

The collector retains typed structure, direct visible text, selected computed CSS, image dimensions and interaction indicators. It excludes HTML, scripts, form values, editable descendant text, arbitrary attributes, full URLs, cookies and browser storage. `[data-veyra-private]` marks a private region whose copy/descendants are excluded (a selected root's styling can still be measured). Background asset URLs are replaced by a presence flag. Heuristic text redaction removes email addresses and common credential-like strings. Other personal information can remain in visible page copy: inspect public content only and use local mode unless sending reduced data to the configured provider is appropriate.

Section scope identifies the nearest `section/article/nav/header/footer/main/[role=region]`, otherwise the immediate parent, and marks the boundary as heuristic. Page samples the current document body at its current scroll position. Open shadow roots can be sampled; iframe documents and closed shadow roots are opaque. DOM visibility is a heuristic, not occlusion-aware pixel analysis. Navigation/button/disclosure attributes are indicators; they do not prove activation behavior. Existing hover capture contributes bounded style/geometry differences only for the exact selected element. Its timestamp can precede the fresh DOM sample; long transitions and already-hovered baselines are disclosed.

The local renderer emits objective, hierarchy, layout, styling, interactions, responsiveness, implementation requirements and accuracy notes. Known numbers remain measured; absent breakpoints/states/assets are never supplied as facts. Recommendations are explicitly labelled. React/HTML preferences change instructions only, not executable code.

The AI adapter uses a separate system message, JSON-encoded untrusted evidence, a fixed administrator-configured endpoint and no tools. It cannot receive cookies, API credentials or browser service capabilities through the evidence path. It validates three interpretation strings, rejects truncated/oversized/unusable output and preserves the deterministic measurements as authoritative. This reduces prompt-injection impact; it does not prove arbitrary model prose safe or correct. The downstream coding tool must also treat quoted website copy and AI interpretation as untrusted. All output is a React-controlled textarea; no HTML execution, Markdown renderer, tools, network commands or generated code execution is enabled.

Limits per single-worker app: one generation at a time, 3 attempts/session/minute, 10 attempts/global/minute; 64 KiB provider request/response envelopes, 1–20 second total provider deadline, output token cap and 60,000-character final prompt. Calls have no automatic retry, redirects, environment proxy inheritance or private-address endpoint support. The reused public-DNS gate pins the actual numeric connection and TLS verifies the configured hostname. Missing/invalid configuration fails closed to local mode. Configuration must be trusted backend administration; this is not a public multi-user service or a spending firewall.
