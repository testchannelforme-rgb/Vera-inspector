"""Observe real computed values; never infer original animation source."""
import asyncio
import time
from .inspector import SNAPSHOT_JS, inspect_element
from .browser_manager import SessionError


async def capture_hover(session, duration_ms: int, interval_ms: int):
    page, element = session.page, session.element
    await page.mouse.move(0, 0)
    await asyncio.sleep(0.25)
    await element.scroll_into_view_if_needed(timeout=2000)
    baseline_hovered = await element.evaluate('(el)=>el.matches(":hover")')
    baseline = await element.evaluate(SNAPSHOT_JS)
    before = await session.screenshot_data()
    box = await element.bounding_box()
    if not box or not box['width'] or not box['height']:
        raise SessionError('The element is not visible. Select a visible element.')
    x, y = box['x']+box['width']/2, box['y']+box['height']/2
    target = await element.evaluate('(el,p)=>{let hit=document.elementFromPoint(p.x,p.y); while(hit?.shadowRoot){const n=hit.shadowRoot.elementFromPoint(p.x,p.y);if(!n||n===hit)break;hit=n;} return hit===el||el.contains(hit)}', {'x': x, 'y': y})
    if not target:
        raise SessionError('The element center is covered. Select an unobscured element.')
    await page.mouse.move(x, y)
    started = time.monotonic()
    samples, during = [], None
    for offset in range(0, duration_ms+1, interval_ms):
        await asyncio.sleep(max(0, started+offset/1000-time.monotonic()))
        snap = await element.evaluate(SNAPSHOT_JS)
        changes = {k: {'before': baseline['styles'][k], 'observed': v}
                   for k, v in snap['styles'].items() if v != baseline['styles'][k]}
        samples.append({'elapsedMs': round((time.monotonic()-started)*1000, 2),
                        'styles': snap['styles'], 'geometry': snap['geometry'],
                        'changesFromBaseline': changes, 'activeAnimations': snap['animations']['active']})
        if during is None and offset >= duration_ms/2:
            during = await session.screenshot_data()
    # If interval does not divide duration, take a final sample at the requested endpoint.
    if duration_ms % interval_ms:
        await asyncio.sleep(max(0, started+duration_ms/1000-time.monotonic()))
        snap = await element.evaluate(SNAPSHOT_JS)
        samples.append({'elapsedMs': round((time.monotonic()-started)*1000, 2), 'styles': snap['styles'], 'geometry': snap['geometry'],
                        'changesFromBaseline': {k:{'before':baseline['styles'][k],'observed':v} for k,v in snap['styles'].items() if v!=baseline['styles'][k]}, 'activeAnimations':snap['animations']['active']})
    after = await session.screenshot_data()
    result = await inspect_element(session)
    result.animations.observations = samples
    result.animations.detected |= any(s['changesFromBaseline'] or s['geometry'] != baseline['geometry'] or s['activeAnimations'] for s in samples)
    result.animations.hover = {
        'requestedIntervalMs': interval_ms, 'requestedDurationMs': duration_ms,
        'actualDurationMs': round((time.monotonic()-started)*1000,2),
        'baseline': {'styles':baseline['styles'],'geometry':baseline['geometry']},
        'baselineWasAlreadyHovered': baseline_hovered,
        'screenshots': {'before':before,'during':during or after,'after':after},
        'comparisonMethod': 'computed-style and bounding-box differences; screenshots are visual evidence, not pixel-difference analysis',
    }
    result.limitations.append('Hover stays active after capture. Baseline waits 250 ms; long prior transitions may still be settling. Actual sample times include browser/screenshot overhead.')
    if baseline_hovered:
        result.limitations.append('Pointer at the viewport corner still hovered the selected element; baseline may already include hover styling.')
    return result
