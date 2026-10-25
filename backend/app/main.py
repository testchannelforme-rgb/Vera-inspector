import logging
from contextlib import asynccontextmanager
from pathlib import Path
import secrets
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from playwright.async_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeout

from .animation import capture_hover
from .browser_manager import BrowserManager, SessionError
from .config import Settings
from .inspector import HIT_TEST_JS, inspect_element
from .schemas import OpenRequest, PointRequest, ScrollRequest, FrameRequest, HoverRequest
from .security import PolicyError, normalize_url
from .diagnostics import startup_diagnostic
from .prompts.schemas import PromptRequest
from .prompts.service import PromptService
from .prompts.evidence import collect_evidence, hover_summary

logger = logging.getLogger('veyra')


def create_app(settings=None, manager=None, prompt_service=None):
    settings = settings or Settings.from_env()
    manager = manager or BrowserManager(settings)

    prompt_service = prompt_service or PromptService()

    @asynccontextmanager
    async def lifespan(app):
        app.state.startup_error = None
        try:
            await manager.start()
        except Exception as exc:
            app.state.startup_error = manager.startup_error or startup_diagnostic(exc)
            logger.exception('Chromium startup failed; the sandbox remains enabled')
        yield
        await manager.stop()

    app = FastAPI(title='Veyra Inspector', version='0.3.0', lifespan=lifespan,
                  docs_url=None, redoc_url=None)
    app.state.manager = manager
    app.state.startup_error = None

    @app.middleware('http')
    async def protections(request: Request, call_next):
        if request.url.path.startswith('/api/'):
            origin = request.headers.get('origin')
            # No permissive CORS. One forwarded port serves both frontend and API.
            if origin and origin != settings.ui_origin and urlsplit(origin).netloc != request.headers.get('host'):
                return JSONResponse({'detail': 'Cross-origin API access is disabled.'}, status_code=403)
            if request.method != 'GET' and request.headers.get('x-veyra-client') != 'inspector-v0.1':
                return JSONResponse({'detail': 'Missing Veyra client header.'}, status_code=403)
            try:
                declared = int(request.headers.get('content-length', '0'))
                if declared < 0: raise ValueError()
            except ValueError:
                return JSONResponse({'detail':'Invalid Content-Length.'},status_code=400)
            if declared > 8192:
                return JSONResponse({'detail':'Request body is too large.'},status_code=413)
            if request.method not in ('GET','HEAD'):
                body = bytearray()
                async for chunk in request.stream():
                    if len(body)+len(chunk)>8192:
                        return JSONResponse({'detail':'Request body is too large.'},status_code=413)
                    body.extend(chunk)
                # Starlette replays the bounded cached body to FastAPI's parser.
                request._body = bytes(body)
        response = await call_next(request)
        response.headers.update({
            'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff',
            'Referrer-Policy':'no-referrer', 'X-Frame-Options':'DENY',
            'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'",
        })
        return response

    @app.exception_handler(SessionError)
    async def session_error(request, exc):
        return JSONResponse({'detail': str(exc),'code':exc.code,'diagnostics':exc.diagnostics}, status_code=exc.status)

    @app.exception_handler(PolicyError)
    async def policy_error(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=400)

    @app.exception_handler(PlaywrightTimeout)
    @app.exception_handler(TimeoutError)
    async def timed_out(request, exc):
        return JSONResponse({'detail':'Browser operation timed out. The website may be slow or block automation. Open it again.','code':'operation-timeout'}, status_code=504)

    @app.exception_handler(PlaywrightError)
    async def browser_error(request, exc):
        return JSONResponse({'detail':'Website operation failed. The site may be blocked, the selected element may have changed, or the browser may have closed. Refresh or open again.','code':'website-operation-failed'}, status_code=502)

    @app.exception_handler(ValueError)
    async def value_error(request, exc):
        return JSONResponse({'detail':str(exc) if isinstance(exc, SessionError) else 'The selected element cannot be inspected in its current state. Select it again.'}, status_code=400)

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logger.exception('Unexpected operation failure')
        return JSONResponse({'detail':'An unexpected operation failed. Open a new session.'}, status_code=500)

    @app.get('/api/health')
    async def health():
        return {'status':'ready' if manager.browser and manager.browser.is_connected() else 'browser-unavailable',
                'detail':app.state.startup_error, 'allowedHosts':sorted(settings.allowed_hosts),'networkMode':settings.network_mode,'version':'0.3.0','prompts':{'aiAvailable':prompt_service.config.available,'defaultMode':'local','version':'0.3'},
                'schemaVersion':'0.1'}

    @app.post('/api/browser/retry')
    async def retry_browser():
        async with manager.guard:
            if manager.sessions and (not manager.browser or not manager.browser.is_connected()):
                for token in list(manager.sessions):await manager.close(token)
            if manager.sessions:
                raise SessionError('Close active sessions before retrying the engine.',409)
            await manager.stop()
            try:
                await manager.start()
                app.state.startup_error=None
            except Exception as exc:
                app.state.startup_error=manager.startup_error or startup_diagnostic(exc)
                raise SessionError('Browser engine could not restart.',503,'browser-engine-failure',app.state.startup_error) from exc
        return await health()

    @app.post('/api/normalize')
    async def normalize(body: dict):
        if set(body)!={'url'} or not isinstance(body['url'],str):
            return JSONResponse({'detail':'Provide one website address.'},status_code=422)
        return {'url':normalize_url(body['url'])}

    @app.post('/api/sessions', status_code=201)
    async def open_session(body: OpenRequest):
        session, frame = await manager.create(body.url, body.viewport.model_dump())
        return {'sessionId':session.token, 'frame':frame, 'inspection':None,
                'expiresInSeconds':settings.session_ttl}

    @app.delete('/api/sessions/{token}')
    async def close_session(token: str):
        await manager.close(token)
        return {'closed':True}

    async def result(session, inspection=None):
        return {'frame':await session.frame(), 'inspection':inspection.model_dump(mode='json') if inspection else None}

    @app.post('/api/sessions/{token}/reload')
    async def reload_page(token: str):
        async with manager.operation(token) as session:
            url = await manager.policy.validate(session.page.url)
            await manager.navigate(session, url)
            return await result(session)

    @app.post('/api/sessions/{token}/refresh')
    async def refresh(token: str):
        async with manager.operation(token) as session:
            await session.clear_selection()
            return await result(session)

    @app.post('/api/sessions/{token}/select')
    async def select(token: str, body: PointRequest):
        async with manager.operation(token) as session:
            session.check_frame(body.frameId)
            session.check_point(body.x, body.y)
            await session.clear_selection()
            handle = await session.page.evaluate_handle(HIT_TEST_JS, {'x':body.x,'y':body.y})
            element = handle.as_element()
            if element is None:
                await handle.dispose()
                raise SessionError('No element at that position.')
            session.element = element
            session.reference_id = secrets.token_hex(12)
            return await result(session, await inspect_element(session))

    @app.post('/api/sessions/{token}/scroll')
    async def scroll(token: str, body: ScrollRequest):
        async with manager.operation(token) as session:
            session.check_frame(body.frameId)
            session.check_point(body.x, body.y)
            await session.clear_selection()
            await session.page.mouse.move(body.x, body.y)
            await session.page.mouse.wheel(body.deltaX, body.deltaY)
            await session.page.wait_for_timeout(200)
            return await result(session)

    @app.post('/api/sessions/{token}/hover')
    async def hover(token: str, body: HoverRequest):
        async with manager.operation(token) as session:
            session.check_frame(body.frameId)
            if session.element is None:
                raise SessionError('Select an element before capturing hover.')
            inspection = await capture_hover(session, body.durationMs, body.intervalMs)
            session.prompt_hover = hover_summary(inspection)
            return await result(session, inspection)

    @app.post('/api/sessions/{token}/clear')
    async def clear(token: str):
        async with manager.operation(token) as session:
            await session.clear_selection()
            await session.page.mouse.move(0, 0)
            await session.page.wait_for_timeout(250)
            return await result(session)

    @app.post('/api/prompts/generate')
    async def generate_prompt(body: PromptRequest):
        # Client supplies references and preferences only; website evidence stays server-owned.
        async with prompt_service.admission(body.sessionId):
            async with manager.operation(body.sessionId) as session:
                evidence = await collect_evidence(session, body)
            return await prompt_service.generate(evidence, body)

    dist = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
    if dist.exists():
        app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
    return app


app = create_app()
