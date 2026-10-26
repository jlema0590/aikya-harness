"""Capability-scoped loopback presentation; no filesystem browser or write routes."""
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
import threading
from aikya.code_index.policy import project_root, read_source
from aikya.documentation.language import resolve
from .contracts import LiveEndpoint
from .publication import read_publication
from .render import render_html
from .watch import STATE


def serve_live(root, *, stop_event, language=None):
    root = project_root(root)
    capability = secrets.token_urlsafe(32)
    prefix = '/view/' + capability + '/'

    class Handler(BaseHTTPRequestHandler):
        server_version = 'AikyaMemory'

        def log_message(self, *_args):
            pass

        def do_GET(self):
            authority = '127.0.0.1:' + str(self.server.server_port)
            origin = self.headers.get('Origin')
            if (self.headers.get('Host') != authority or (origin and origin != 'http://' + authority)
                    or self.headers.get('Sec-Fetch-Site') == 'cross-site'):
                self.send_error(403)
                return
            if self.path not in (prefix, prefix + 'status', prefix + 'snapshot'):
                self.send_error(404)
                return
            try:
                snapshot, generation = read_publication(root)
                if self.path == prefix:
                    payload = render_html(snapshot, live=True, language=resolve(root,language)).encode()
                    content_type = 'text/html; charset=utf-8'
                elif self.path.endswith('/snapshot'):
                    payload = json.dumps({'generation': generation, 'snapshot': asdict(snapshot)}).encode()
                    content_type = 'application/json'
                else:
                    status = {'state': 'Watching', 'published_generation': generation}
                    try:
                        status.update(json.loads(read_source(root, STATE, 16000)))
                    except (OSError, ValueError):
                        pass
                    payload = json.dumps(status).encode()
                    content_type = 'application/json'
            except (OSError, ValueError, TypeError):
                self.send_error(503)
                return
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "frame-ancestors 'none'; form-action 'none'")
            self.end_headers()
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.1), daemon=True)
    thread.start()
    closed = threading.Event()

    def close():
        if not closed.is_set():
            closed.set()
            server.shutdown()
            server.server_close()
            thread.join(3)

    def wait():
        while not closed.is_set():
            if stop_event.wait(.1):
                close()
                return
    threading.Thread(target=wait, daemon=True).start()
    return LiveEndpoint('http://127.0.0.1:' + str(server.server_port) + prefix, close)
