import http.client
import json
import re
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
import hosted_reader as hosted

class HostedTests(unittest.TestCase):
    def setUp(self):
        self.origin = 'https://reader.example.test'
        self.code = 'test-access-code-' * 3
        self.server = hosted.make_server(self.origin, self.code, ("127.0.0.1", 0))
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        conn.request(method, path, body, headers or {})
        res = conn.getresponse()
        result = res.status, dict(res.getheaders()), res.read().decode()
        conn.close()
        return result

    def login(self):
        status, headers, _ = self.request('POST', '/login', urlencode({'code': self.code}), {'Origin': self.origin})
        self.assertEqual(status, 303)
        cookie = headers['Set-Cookie']
        for flag in ('Secure', 'HttpOnly', 'SameSite=Strict'):
            self.assertIn(flag, cookie)
        cookie = cookie.split(';')[0]
        _, _, page = self.request('GET', '/', headers={'Cookie': cookie})
        token = re.search(r'const token="([^"]+)";', page)[1]
        return {'Origin': self.origin, 'Cookie': cookie, 'X-Reader-Token': token}

    def test_authentication_and_csrf_required(self):
        self.assertIn('Access code', self.request('GET', '/')[2])
        self.assertEqual(self.request('POST', '/session', '{}', {'Origin': self.origin})[0], 403)
        headers = self.login()
        self.assertEqual(self.request('POST', '/session', '{}', {**headers, 'Origin': 'https://wrong.test'})[0], 403)
        self.assertEqual(self.request('POST', '/session', '{}', {**headers, 'X-Reader-Token': 'wrong'})[0], 403)

    def test_browser_sessions_are_isolated(self):
        first, second = self.login(), self.login()
        with patch.object(hosted, 'create_call', return_value=b'v=0-answer'):
            status, _, body = self.request('POST', '/session', json.dumps({'sdp':'v=0'}), first)
        self.assertEqual(status, 200)
        rid = json.loads(body)['reader']
        payload = json.dumps({'reader': rid, 'arguments': {'action':'stop'}})
        self.assertEqual(self.request('POST', '/tool', payload, first)[0], 200)
        self.assertEqual(self.request('POST', '/tool', payload, second)[0], 400)

    def test_invalid_deployment_configuration(self):
        for origin, code in [('http://reader.test', self.code), (self.origin, 'short')]:
            with self.assertRaises(ValueError):
                hosted.make_server(origin, code)

if __name__ == '__main__':
    unittest.main()
