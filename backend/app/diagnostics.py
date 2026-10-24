"""Bounded diagnostics without raw URLs, query strings, source text or tokens."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
import time
from urllib.parse import urlsplit


def safe_location(url):
    try:
        p=urlsplit(url)
        return {'scheme':p.scheme,'host':p.hostname or ''}
    except ValueError:return {'host':'invalid-url'}


def scrub_error(value):
    # Startup logs can contain control endpoints, proxy credentials and paths.
    lines=str(value).splitlines()
    useful=[line for line in lines if any(word in line.lower() for word in ('error','root without','executable doesn','operation not permitted','no usable sandbox','missing dependencies')) and '<launching>' not in line]
    text='\n'.join(([lines[0]] if lines else [])+useful) if useful else str(value)
    text=re.sub(r'(?:wss?|https?)://\S+','[redacted endpoint]',text)
    text=re.sub(r'--user-data-dir=\S+','--user-data-dir=[temporary profile]',text)
    text=re.sub(r'/[^\s]+/(?:[^\s/]+/)*','[local path]/',text)
    return text[:1800]


def startup_diagnostic(exc):
    text=str(exc)
    low=text.lower()
    category='browser-engine-failure'
    hint='Run bash scripts/doctor.sh and check the intended virtual environment and browser installation.'
    if 'public mode requires' in low or 'readiness proof' in low:
        category='isolation-configuration-failure';hint='Start the supplied isolated Compose stack. Public browsing is disabled without its gateway, firewall and sandbox readiness evidence.'
    elif 'executable doesn' in low or 'executable not' in low:
        category='browser-binary-missing';hint='Run bash scripts/setup.sh; Veyra uses the full chromium channel, not Headless Shell.'
    elif 'shared librar' in low or 'host system is missing dependencies' in low:
        category='browser-libraries-missing';hint='Rebuild the supplied development container, which includes matching browser libraries.'
    elif 'sandbox' in low or 'running as root' in low or 'operation not permitted' in low:
        category='browser-sandbox-unavailable';hint='Use a non-root account and a host that supports Chromium sandbox namespaces. Security is kept enabled.'
    elif 'econnrefused' in low or 'connect' in low:
        category='browser-service-unavailable';hint='Check docker compose -f compose.inspection.yml logs browser; never expose the control port.'
    return {'category':category,'message':scrub_error(text),'hint':hint,'sandboxEnabled':True}


@dataclass
class PageDiagnostics:
    requested: dict = field(default_factory=dict)
    httpStatus: int | None = None
    documentPolicy: dict = field(default_factory=dict)
    httpErrors: list = field(default_factory=list)
    navigationState: str = 'starting'
    readiness: dict = field(default_factory=dict)
    failures: list = field(default_factory=list)
    consoleErrors: list = field(default_factory=list)
    blocked: list = field(default_factory=list)
    screenshot: dict = field(default_factory=dict)
    inflight: set = field(default_factory=set)
    last_activity: float = field(default_factory=time.monotonic)

    def attach(self,page):
        def started(request):
            if len(self.inflight)<600:self.inflight.add(id(request))
            self.last_activity=time.monotonic()
        def finished(request):
            self.inflight.discard(id(request));self.last_activity=time.monotonic()
        def failed(request):
            finished(request)
            if len(self.failures)<30:self.failures.append({**safe_location(request.url),'resourceType':request.resource_type,'error':scrub_error(request.failure or 'failed')})
        def response(result):
            if result.status>=400 and len(self.httpErrors)<30:
                self.httpErrors.append({**safe_location(result.url),'status':result.status,'resourceType':result.request.resource_type})
        def console(message):
            # Do not export console text: sites may log personal data or tokens.
            if message.type=='error' and len(self.consoleErrors)<20:
                self.consoleErrors.append({'type':'console-error','category':'csp-resource-block' if 'content security policy' in message.text.lower() else 'page-console-error','location':safe_location(message.location.get('url',''))})
        def js_error(error):
            if len(self.consoleErrors)<20:self.consoleErrors.append({'type':'javascript-error','message':'Page JavaScript raised an exception; raw text omitted for privacy.'})
        page.on('response',response);page.on('request',started);page.on('requestfinished',finished);page.on('requestfailed',failed);page.on('console',console);page.on('pageerror',js_error)

    def export(self):
        return {'requested':self.requested,'httpStatus':self.httpStatus,'documentPolicy':self.documentPolicy,'resourceHttpErrors':self.httpErrors,'navigationState':self.navigationState,
                'readiness':self.readiness,'failedRequests':self.failures,'consoleErrors':self.consoleErrors,
                'pendingRequestCount':len(self.inflight),'blockedRequests':self.blocked,'screenshot':self.screenshot,'capturedAt':datetime.now(timezone.utc).isoformat()}
