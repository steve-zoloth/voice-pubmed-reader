"""Private single-user hosted entry point; local reader and voice engine unchanged.
Run behind an HTTPS reverse proxy. See HOSTED_SETUP.md before deployment.
"""
import hmac
import json
import os
import secrets
import threading
import time
from collections import deque
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from realtime_adapter import Reader, create_call
import voice_pubmed_bot as backend

COOKIE = 'vpr_session'
LOGIN = b'''<!doctype html><html lang="en"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Voice PubMed Reader sign in</title><main><h1>Voice PubMed Reader</h1><form method="post" action="/login"><label for="code">Access code</label><input id="code" name="code" type="password" autocomplete="current-password" required autofocus><button type="submit">Sign in</button></form></main></html>'''


def make_server(origin, access_code, address=('127.0.0.1', 8080)):
    parsed = urlsplit(origin)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('VPR_PUBLIC_ORIGIN must be an HTTPS origin with no path.')
    if len(access_code) < 32:
        raise ValueError('VPR_ACCESS_CODE must contain at least 32 characters.')
    sessions, login_attempts = {}, deque()
    guard = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(50)

        def log_message(self, *args):
            pass

        def reply(self, code, body, kind='application/json', headers=None):
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'same-origin')
            self.send_header('Content-Security-Policy', "frame-ancestors 'none'")
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def session(self):
            try:
                cookie = SimpleCookie(self.headers.get('Cookie', ''))
                sid = cookie[COOKIE].value if COOKIE in cookie else ''
            except Exception:
                return None
            with guard:
                now = time.monotonic()
                for key in list(sessions):
                    if sessions[key]['expires'] < now:
                        del sessions[key]
                return sessions.get(sid)

        def do_GET(self):
            if self.path == '/health':
                return self.reply(200, b'{"ok":true}')
            if self.path not in ('/', '/login'):
                return self.reply(404, b'{}')
            session = self.session()
            if self.path == '/login' or not session:
                return self.reply(200, LOGIN, 'text/html; charset=utf-8')
            page = Path(__file__).with_name('realtime_reader.html').read_text()
            page = page.replace("const token=location.hash.slice(1);", 'const token=' + json.dumps(session['csrf']) + ';')
            page = page.replace('Muse fallback: end this session, then open run_voice_pubmed_bot.command.', 'If voice disconnects, activate Start voice to reconnect. Keep this page open while reading.')
            page = page.replace('Voice is off. Press Enter to start voice and allow microphone access.', 'Voice is off. Activate Start voice and allow microphone access.')
            page = page.replace('or use the Muse launcher', 'or reload this page').replace('or use Muse', 'or reload this page')
            return self.reply(200, page.encode(), 'text/html; charset=utf-8')

        def do_POST(self):
            if self.headers.get('Origin') != origin:
                if self.path == '/login':
                    return self.reply(403, b'<html lang="en"><title>Sign in again</title><main><h1>Please sign in again</h1><p>Open the login page in Safari and try again.</p><a href="/login">Return to login</a></main></html>', 'text/html; charset=utf-8')
                return self.reply(403, b'{"error":"Request origin rejected."}')
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 100000:
                    return self.reply(400, b'{"error":"Invalid request size."}')
                raw = self.rfile.read(length)
                if self.path == '/login':
                    with guard:
                        now = time.monotonic()
                        while login_attempts and login_attempts[0] < now - 60:
                            login_attempts.popleft()
                        if len(login_attempts) >= 10:
                            return self.reply(429, b'Too many sign-in attempts. Wait one minute.', 'text/plain')
                        login_attempts.append(now)
                    submitted = parse_qs(raw.decode()).get('code', [''])[0]
                    if not hmac.compare_digest(submitted.encode(), access_code.encode()):
                        return self.reply(401, b'Access code not accepted. Return to sign in and retry.', 'text/plain')
                    sid = secrets.token_urlsafe(32)
                    with guard:
                        now = time.monotonic()
                        for key in list(sessions):
                            if sessions[key]['expires'] < now:
                                del sessions[key]
                        if len(sessions) >= 16:
                            return self.reply(429, b'Too many signed-in browsers. Retry later.', 'text/plain')
                        sessions[sid] = {'expires': now + 8*3600, 'csrf': secrets.token_urlsafe(32),
                                         'reader': None, 'reader_id': None, 'lock': threading.Lock(), 'calls': deque()}
                    return self.reply(303, b'', headers={'Location': '/', 'Set-Cookie': f'{COOKIE}={sid}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=28800'})
                session = self.session()
                if not session or not hmac.compare_digest(self.headers.get('X-Reader-Token', '').encode(), session['csrf'].encode()):
                    return self.reply(403, b'{"error":"Sign in again to use the reader."}')
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError('Invalid request.')
                if self.path == '/session':
                    sdp = data.get('sdp')
                    if not isinstance(sdp, str) or not sdp.startswith('v=0'):
                        raise ValueError('Invalid audio offer.')
                    with session['lock']:
                        now = time.monotonic()
                        while session['calls'] and session['calls'][0] < now - 3600:
                            session['calls'].popleft()
                        if len(session['calls']) >= 12:
                            return self.reply(429, b'{"error":"Voice start limit reached. Retry later."}')
                        session['calls'].append(now)
                        answer = create_call(sdp)
                        session['reader'] = Reader()
                        session['reader_id'] = secrets.token_urlsafe(24)
                        result = {'sdp': answer.decode(), 'reader': session['reader_id']}
                elif self.path == '/tool':
                    with session['lock']:
                        if not session['reader'] or data.get('reader') != session['reader_id']:
                            raise ValueError('Reader expired. Start voice again.')
                        arguments = dict(data['arguments'])
                        arguments.pop('heard_seconds', None)
                        result = session['reader'].execute(**arguments, heard_seconds=data.get('heard_seconds', 0))
                else:
                    return self.reply(404, b'{}')
                return self.reply(200, json.dumps(result).encode())
            except Exception as exc:
                message = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else 'Request failed. Please retry.'
                return self.reply(400, json.dumps({'error': message}).encode())

    return ThreadingHTTPServer(address, Handler)


def main():
    origin = os.environ.get('VPR_PUBLIC_ORIGIN', '')
    code = os.environ.get('VPR_ACCESS_CODE', '')
    if not os.environ.get('OPENAI_API_KEY'):
        raise SystemExit('Set OPENAI_API_KEY in the hosting secret store.')
    backend.Entrez.email = os.environ['NCBI_EMAIL']
    backend.REF_FILE = str(Path(os.environ.get('VPR_DATA_DIR', '/data')) / 'references.txt')
    Path(backend.REF_FILE).parent.mkdir(parents=True, exist_ok=True)
    server = make_server(origin, code, ('127.0.0.1', int(os.environ.get('PORT', '8080'))))
    try:
        server.serve_forever()
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
