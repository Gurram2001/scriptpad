"""Tiny fake of the Supabase auth + REST endpoints Scriptpad uses (for tests only)."""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROWS, USERS, LOG = {}, {}, []

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code=200, body=None):
        b = b'' if body is None else json.dumps(body).encode()
        self.send_response(code)
        for k, v in (('Access-Control-Allow-Origin', '*'), ('Access-Control-Allow-Headers', 'apikey,authorization,content-type,prefer,x-client-info'),
                     ('Access-Control-Allow-Methods', 'GET,POST,OPTIONS'), ('Content-Type', 'application/json'), ('Content-Length', str(len(b)))):
            self.send_header(k, v)
        self.end_headers(); self.wfile.write(b)
    def user(self):
        a = self.headers.get('Authorization', '')
        return a[len('Bearer tok-'):] if a.startswith('Bearer tok-') else None
    def do_OPTIONS(self): self._send(204)
    def do_GET(self):
        if self.path.startswith('/_log'): return self._send(200, LOG)
        if self.path.startswith('/_rows'): return self._send(200, [dict(r) for r in ROWS.values()])
        u = self.user()
        if not u: return self._send(401, {'message': 'no auth'})
        self._send(200, [r for (k, _), r in ROWS.items() if k == u])
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'null'); p = self.path
        tok = lambda em: {'access_token': 'tok-' + em, 'refresh_token': 'ref-' + em, 'expires_in': 3600, 'user': {'id': em, 'email': em}}
        if p.startswith('/auth/v1/signup'):
            if d['email'] in USERS: return self._send(422, {'msg': 'User already registered'})
            USERS[d['email']] = d['password']; return self._send(200, tok(d['email']))
        if 'grant_type=password' in p:
            if USERS.get(d['email']) != d['password']: return self._send(400, {'msg': 'Invalid login credentials'})
            return self._send(200, tok(d['email']))
        if p.startswith('/auth/v1/logout'): LOG.append('logout ' + str(self.user())); return self._send(204)
        if 'grant_type=refresh_token' in p:
            if not str(d.get('refresh_token', '')).startswith('ref-'): return self._send(400, {'msg': 'Invalid Refresh Token'})
            return self._send(200, tok(d['refresh_token'][4:]))
        if p.startswith('/rest/v1/scripts'):
            u = self.user()
            if not u: return self._send(401, {})
            for r in d: r['user_id'] = u; ROWS[(u, r['id'])] = r
            return self._send(201)
        self._send(404, {})

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 8766), H).serve_forever()
