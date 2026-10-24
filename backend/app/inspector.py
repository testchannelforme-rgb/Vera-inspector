from datetime import datetime, timezone
from pathlib import Path
from .schemas import Inspection

SNAPSHOT_JS = Path(__file__).with_name('inspect.js').read_text()
HIT_TEST_JS = '''({x,y}) => {
    let el=document.elementFromPoint(x,y);
    // Open shadow roots are inspectable; closed roots remain opaque.
    while(el?.shadowRoot) {
        const nested=el.shadowRoot.elementFromPoint(x,y);
        if(!nested || nested===el) break;
        el=nested;
    }
    return el;
}'''


async def inspect_element(session) -> Inspection:
    raw = await session.element.evaluate(SNAPSHOT_JS)
    raw['element']['referenceId'] = session.reference_id
    limitations = [
        'Computed CSS values, not original authored stylesheet declarations.',
        'Screenshot and DOM are successive observations; continuously moving content can drift.',
        'Accessibility name/role is best effort; closed shadow roots are opaque.',
        'Scripts, form values and inline event handlers are removed from HTML evidence.',
        'Canvas/WebGL pixels and arbitrary JavaScript animation source are not reconstructed.',
    ]
    if raw['element']['tagName'] in ('iframe', 'frame'):
        limitations.append('Iframe content is not inspected in V0.1. This is the frame element only, including cross-origin frames.')
    return Inspection(capturedAt=datetime.now(timezone.utc).isoformat(), source={
        'url': session.page.url, 'viewport': session.page.viewport_size,
        'deviceScaleFactor': 1, 'coordinateSystem': 'viewport-css-pixels',
        'scroll': await session.page.evaluate('({x:scrollX,y:scrollY})'),
        'styleOrigin': 'computed',
    }, limitations=limitations, **raw)
