"""Metadata-only diagnostics: no URLs, query strings, bodies, cookies or tokens."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from uuid import uuid4


def classify(url: str) -> str | None:
    parsed = urlsplit(url)
    host, path = parsed.hostname, parsed.path
    if host == 'consulta.car.gov.br':
        if path.rstrip('/') == '/api/hcaptcha/validate':
            return 'site_validation'
        if path.startswith('/api/download'):
            return 'site_download'
    if host in {'www.google.com', 'www.recaptcha.net', 'www.gstatic.com'}:
        match = re.fullmatch(r'/recaptcha/(?:api2|enterprise)/(anchor|bframe|reload|userverify|payload|replaceimage)', path)
        if match:
            return 'recaptcha_' + match[1]
    return None


class SessionDiagnostics:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.path = directory / f'captcha-{stamp}-{uuid4().hex[:6]}.jsonl'
        self.write('session_started')

    def write(self, event: str, **fields):
        try:
            if self.path.exists() and self.path.stat().st_size > 1_000_000:
                return
            row = {'time': datetime.now(timezone.utc).isoformat(), 'event': event, **fields}
            with self.path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(row) + '\n')
        except OSError:
            pass  # Diagnostics must not interrupt the browser session.

    def attach(self, context):
        context.on('request', self.request)
        context.on('response', self.response)
        context.on('requestfailed', self.failed)
        context.on('page', lambda page: self.watch_page(page))
        for page in context.pages:
            self.watch_page(page)

    def watch_page(self, page):
        page.on('download', lambda download: self.write('browser_download_event'))

    def request(self, request):
        category = classify(request.url)
        if category:
            self.write('request', category=category, method=request.method)

    def response(self, response):
        category = classify(response.url)
        if category:
            self.write('response', category=category, status=response.status)

    def failed(self, request):
        category = classify(request.url)
        if category:
            match = re.search(r'net::ERR_[A-Z_]+', request.failure or '')
            self.write('request_failed', category=category,
                       reason=match[0] if match else 'network_failure')
