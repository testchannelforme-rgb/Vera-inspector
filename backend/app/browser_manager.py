import asyncio
import base64
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
import secrets
import time

from playwright.async_api import async_playwright
from .config import Settings
from .security import NetworkPolicy, PolicyError
from .proxy import EgressProxy


class SessionError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


@dataclass
class Session:
    token: str
    context: object
    page: object
    born: float = field(default_factory=time.monotonic)
    touched: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    element: object = None
    reference_id: str = ''
    frame_id: str = ''
    blocked: set[str] = field(default_factory=set)
    requests: int = 0
    closed: bool = False

    async def clear_selection(self):
        if self.element is not None:
            with suppress(Exception):
                await self.element.dispose()
        self.element, self.reference_id = None, ''

    def check_frame(self, frame_id):
        if not self.frame_id or frame_id != self.frame_id:
            raise SessionError('Preview changed. Refresh the screenshot and select again.', 409)

    def check_point(self, x, y):
        viewport = self.page.viewport_size
        if not (0 <= x < viewport['width'] and 0 <= y < viewport['height']):
            raise SessionError('Point is outside the browser viewport.', 422)

    async def screenshot_data(self):
        data = await self.page.screenshot(type='jpeg', quality=78, full_page=False, scale='css', timeout=5000)
        return 'data:image/jpeg;base64,'+base64.b64encode(data).decode()

    async def frame(self):
        image = await self.screenshot_data()
        self.frame_id = secrets.token_hex(12)
        return {'frameId': self.frame_id, 'image': image, 'viewport': self.page.viewport_size,
                'url': self.page.url, 'scroll': await self.page.evaluate('({x:scrollX,y:scrollY})'),
                'coordinateSystem': 'viewport-css-pixels', 'deviceScaleFactor': 1,
                'warnings': sorted(self.blocked)}


class BrowserManager:
    def __init__(self, settings: Settings, policy=None):
        self.settings = settings
        self.policy = policy or NetworkPolicy(set(settings.allowed_hosts))
        self.sessions: dict[str, Session] = {}
        self.browser = self.playwright = None
        self.guard = asyncio.Lock()
        self.reaper = None
        self.proxy = EgressProxy(self.policy)

    async def start(self):
        await self.proxy.start()
        try:
            self.playwright = await async_playwright().start()
            # Mandatory sandbox: never silently retry with --no-sandbox.
            self.browser = await self.playwright.chromium.launch(
                headless=True, channel='chromium', chromium_sandbox=True,
                args=['--disable-quic', '--dns-prefetch-disable', '--force-webrtc-ip-handling-policy=disable_non_proxied_udp', '--proxy-bypass-list=<-loopback>'],
                timeout=15000,
            )
        except Exception:
            if self.playwright:
                await self.playwright.stop()
            self.playwright = None
            await self.proxy.stop()
            raise
        self.reaper = asyncio.create_task(self._reap_loop())

    async def _reap_loop(self):
        while True:
            await asyncio.sleep(10)
            await self.reap()

    async def reap(self):
        now = time.monotonic()
        for token, session in list(self.sessions.items()):
            if now-session.born >= self.settings.session_ttl or now-session.touched >= self.settings.idle_ttl:
                await self.close(token)

    async def create(self, url: str, viewport: dict):
        url = await self.policy.validate(url)
        async with self.guard:
            if not self.browser or not self.browser.is_connected():
                raise SessionError('Chromium is unavailable. See terminal startup diagnostics and README.', 503)
            if len(self.sessions) >= self.settings.max_sessions:
                raise SessionError('All browser sessions are busy. Close a session or wait for expiry.', 429)
            context = await self.browser.new_context(
                viewport=viewport, device_scale_factor=1, service_workers='block',
                accept_downloads=False, java_script_enabled=True, proxy=self.proxy.config,
            )
            context.set_default_timeout(4000)
            context.set_default_navigation_timeout(self.settings.navigation_timeout_ms)
            try:
                page = await context.new_page()
            except BaseException:
                await context.close()
                raise
            session = Session(secrets.token_urlsafe(32), context, page)
            self.sessions[session.token] = session
        try:
            await context.route('**/*', lambda route: self._route(session, route))
            await context.route_web_socket('**/*', lambda ws: ws.close(code=1008, reason='WebSockets disabled in V0.1'))
            page.on('dialog', lambda dialog: dialog.dismiss())
            page.on('download', lambda download: download.cancel())
            # Inspection has no remote clicks. Popups and script-opened extra pages are closed.
            context.on('page', lambda new_page: new_page.close() if new_page != page else None)
            async with session.lock:
                async with asyncio.timeout(22):
                    await self.navigate(session, url)
                    frame = await session.frame()
            return session, frame
        except BaseException:
            await self.close(session.token)
            raise

    async def _route(self, session, route):
        session.requests += 1
        try:
            if session.requests > self.settings.max_requests:
                raise PolicyError('Page request budget exhausted; open a new session.')
            if route.request.resource_type in ('media', 'websocket'):
                raise PolicyError('Media and WebSocket requests are blocked to limit resources.')
            if route.request.method not in ('GET', 'HEAD'):
                raise PolicyError('Only read-only GET/HEAD website requests are allowed.')
            await self.policy.validate(route.request.url)
            await route.continue_()
        except PolicyError as exc:
            session.blocked.add(str(exc))
            await route.abort('blockedbyclient')
        except Exception:
            session.blocked.add('A network request could not be validated and was blocked.')
            with suppress(Exception):
                await route.abort('blockedbyclient')

    async def navigate(self, session, url):
        await session.clear_selection()
        session.frame_id = ''
        session.blocked.clear()
        response = await session.page.goto(url, wait_until='domcontentloaded')
        if response and response.status >= 400:
            raise SessionError(f'The website returned HTTP {response.status}. It may block automated browsers.', 502)
        await self.policy.validate(session.page.url)
        # A bounded settle period, not networkidle (which can hang on busy sites).
        await asyncio.sleep(0.35)
        await session.page.mouse.move(0, 0)

    @asynccontextmanager
    async def operation(self, token):
        session = self.sessions.get(token)
        if not session:
            raise SessionError('Session expired or closed. Open the website again.', 404)
        # Reject queued operations instead of allowing an unbounded request backlog.
        if session.lock.locked():
            raise SessionError('An inspection is already running. Please wait.', 409)
        async with session.lock:
            now = time.monotonic()
            if session.closed or now-session.born >= self.settings.session_ttl or now-session.touched >= self.settings.idle_ttl:
                raise SessionError('Session expired. Open the website again.', 404)
            session.touched = now
            try:
                async with asyncio.timeout(22):
                    yield session
            except BaseException:
                session.frame_id = ''  # A failed operation may have changed the page.
                raise
            finally:
                session.touched = time.monotonic()

    async def close(self, token):
        session = self.sessions.get(token)
        if session:
            async with session.lock:
                if self.sessions.pop(token, None) is None:
                    return
                session.closed = True
                await session.clear_selection()
                with suppress(Exception):
                    await asyncio.wait_for(session.context.close(), 5)

    async def stop(self):
        if self.reaper:
            self.reaper.cancel()
            with suppress(asyncio.CancelledError):
                await self.reaper
        for token in list(self.sessions):
            await self.close(token)
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        await self.proxy.stop()
