"""Loopback-only, read-only demo. Not a production web deployment."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .core import Assistant
from .safety import InputError

PAGE = Path(__file__).with_name('index.html').read_bytes()

def handler_for(assistant, port):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass
        def allowed(self):
            return self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}
        def send(self, code, content, content_type='application/json'):
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(content)
        def do_GET(self):
            if not self.allowed():
                self.send(403, b'{"error":"Host rejected"}'); return
            if self.path == '/':
                self.send(200, PAGE, 'text/html; charset=utf-8')
            elif self.path in {'/app.js', '/style.css'}:
                filename = self.path[1:]
                self.send(200, Path(__file__).with_name(filename).read_bytes(), 'application/javascript' if filename.endswith('.js') else 'text/css')
            else:
                self.send(404, b'{"error":"Not found"}')
        def do_POST(self):
            if not self.allowed():
                self.send(403, b'{"error":"Host rejected"}'); return
            if self.path != '/api/ask':
                self.send(404, b'{"error":"Not found"}'); return
            if self.headers.get('Origin') not in {f'http://127.0.0.1:{port}', f'http://localhost:{port}'}:
                self.send(403, b'{"error":"Origin rejected"}'); return
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                self.send(415, b'{"error":"JSON required"}'); return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 20000:
                    raise InputError('Request exceeds size limit or is empty')
                self.connection.settimeout(5)
                payload = json.loads(self.rfile.read(length))
                self.send(200, json.dumps(assistant.ask(payload)).encode())
            except (InputError, ValueError, UnicodeError):
                self.send(400, b'{"error":"Invalid request. Check question and log limits."}')
            except (TimeoutError, OSError):
                self.send(408, b'{"error":"Request timed out"}')
    return Handler

def serve(port=8765, use_llm=False, provider='azure'):
    if not 1024 <= port <= 65535:
        raise ValueError('Use a port between 1024 and 65535')
    server = ThreadingHTTPServer(('127.0.0.1', port), handler_for(Assistant(use_llm=use_llm,provider=provider), port))
    print(f'Open http://127.0.0.1:{port} | LLM: {use_llm} | Ctrl+C to stop', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
