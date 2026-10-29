"""Implementation priorities, deliberately distinct from measured website evidence."""
from .selection import selection_plan

PRESETS = {
    'faithful': ('Faithful Recreation', 'Match the captured viewport first. Preserve measured geometry, CSS ownership and exact style mappings. Do not introduce a new visual identity.'),
    'responsive-first': ('Responsive First', 'Recommendation: build intrinsic grid/flex containers, fluid media and content-driven wrapping. Propose breakpoints only after overflow tests; no breakpoint or alternate layout is claimed as observed. Test proposed layouts at 390, 768 and 1280 CSS px as engineering test sizes, not captured measurements.'),
    'accessible-implementation': ('Accessible Implementation', 'Recommendation: start with semantic landmarks and native controls; preserve DOM reading order, supply keyboard and visible focus behavior, and respect prefers-reduced-motion. Verify contrast rather than inventing a contrast ratio. Use captured alt text as evidence, review its usefulness, and request missing descriptions. Document appearance tradeoffs separately.'),
    'clean-production-code': ('Clean Production Code', 'Recommendation: propose a file/component map from the captured subtree. Extract repeated style values into scoped tokens only after checking ownership; shared CSS does not prove repeated components. Separate presentation and verified interaction state. Avoid speculative routes, external libraries and new services. Include concise run steps and tests for implemented behavior.'),
    'maximum-visual-detail': ('Maximum Visual Detail', 'Use the largest supported node-detail budget with complete captured ancestry. Preserve exact gradients and layer order, font metrics, shadows, masks, transforms, clipping, opacity and owner-attributed pseudo CSS. Do not flatten compositing into an invented color or duplicate text layers. Preserve unknown font/asset files as labelled placeholders and list visual checks still needed.'),
}


def selected_evidence(evidence, request):
    maximum = {'concise': 4, 'detailed': 12, 'highly-detailed': 28}[request.detail]
    if request.preset == 'maximum-visual-detail':
        maximum = 28
    return selection_plan(evidence.get('nodes', []), maximum)
