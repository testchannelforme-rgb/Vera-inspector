import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import pytest
import pytest_asyncio
from playwright.async_api import Error as PlaywrightError
from app.browser_manager import BrowserManager
from app.config import Settings
from app.security import NetworkPolicy, PolicyError
from urllib.parse import urlsplit


def pytest_addoption(parser):
    parser.addoption('--public', action='store_true', help='Also inspect the real https://example.com site')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == '/redirect-private':
            self.send_response(302)
            self.send_header('Location', 'http://127.0.0.1:1/private')
            self.end_headers()
        elif self.path == '/blocked-fetch':
            self.send_response(200)
            self.send_header('Content-Type','text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Network test</h1><img src="http://169.254.169.254/latest/meta-data"><script>fetch("http://127.0.0.1:1/secret").catch(()=>{});new WebSocket("ws://127.0.0.1:1/ws");</script>')
        else:
            super().do_GET()


@pytest.fixture(scope='session')
def fixture_site():
    handler=functools.partial(QuietHandler,directory=str(Path(__file__).parent/'fixtures'))
    server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown();server.server_close();thread.join()


class FixturePolicy(NetworkPolicy):
    """Test-only exception, exact ephemeral origin only. Never imported by the app."""
    def __init__(self, origin):
        super().__init__({'example.com','www.example.com'})
        self.origin=origin

    async def validate(self,url):
        if url==self.origin or url.startswith(self.origin+'/'):
            return url
        return await super().validate(url)


@pytest_asyncio.fixture
async def browser_manager(fixture_site):
    manager=BrowserManager(Settings(),FixturePolicy(fixture_site))
    original_resolve=manager.proxy.resolve
    async def fixture_resolve(url):
        if urlsplit(url).netloc==urlsplit(fixture_site).netloc:
            return url,'127.0.0.1',int(fixture_site.rsplit(':',1)[1])
        return await original_resolve(url)
    manager.proxy.resolve=fixture_resolve
    try:
        await manager.start()
    except PlaywrightError as exc:
        pytest.skip(f'Sandboxed Chromium could not start in this host ({type(exc).__name__}). Run on a sandbox-capable host; do not disable its sandbox.')
    try:
        yield manager
    finally:
        await manager.stop()
