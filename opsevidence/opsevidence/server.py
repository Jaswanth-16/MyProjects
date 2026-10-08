"""Loopback-only demo server, limited concurrency and same-origin requests."""
import json
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .contracts import ContractError
from .api import handle, options
ASSETS=Path(__file__).parent

def handler_for(port,provider):
    gate=threading.BoundedSemaphore(2)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,fmt,*args):pass
        def host_ok(self):return self.headers.get('Host') in {f'127.0.0.1:{port}',f'localhost:{port}'}
        def send(self,status,data,kind='application/json'):
            if not isinstance(data,bytes):data=json.dumps(data).encode()
            self.send_response(status)
            for k,v in {'Content-Type':kind,'Content-Length':str(len(data)),'Cache-Control':'no-store',
                'X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"}.items():self.send_header(k,v)
            self.end_headers();self.wfile.write(data)
        def do_GET(self):
            if not self.host_ok():self.send(403,{'error':'Host rejected'});return
            if self.path=='/api/options':self.send(200,{'provider':provider,**options()});return
            files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','application/javascript'),'/style.css':('style.css','text/css')}
            if self.path not in files:self.send(404,{'error':'Not found'});return
            name,kind=files[self.path];self.send(200,(ASSETS/name).read_bytes(),kind)
        def do_POST(self):
            if not self.host_ok() or self.headers.get('Origin') not in {f'http://127.0.0.1:{port}',f'http://localhost:{port}'}:
                self.send(403,{'error':'Host or origin rejected'});return
            if self.path!='/api/run':self.send(404,{'error':'Not found'});return
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':self.send(415,{'error':'JSON required'});return
            if not gate.acquire(blocking=False):self.send(429,{'error':'Two investigations are already running'});return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=20000:raise ContractError('Request size out of bounds')
                self.connection.settimeout(5)
                payload=json.loads(self.rfile.read(size))
                self.send(200,handle(payload,provider))
            except (ContractError,ValueError,UnicodeError):self.send(400,{'error':'Invalid request; check input limits and fields'})
            except (TimeoutError,OSError):self.send(408,{'error':'Request timeout'})
            finally:gate.release()
    return Handler

def serve(port,provider='offline'):
    if not 1024<=port<=65535:raise ValueError('Use a port from 1024 to 65535')
    server=ThreadingHTTPServer(('127.0.0.1',port),handler_for(port,provider))
    print(f'Open http://127.0.0.1:{port} | provider={provider} | Ctrl+C to stop',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
