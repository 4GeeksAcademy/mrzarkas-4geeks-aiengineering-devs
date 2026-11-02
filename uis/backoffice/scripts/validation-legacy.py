"""Read-only legacy fixture server for local comparison; synthetic backend only."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
root = Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        route = unquote(urlsplit(path).path).lstrip('/')
        base = root / 'operational-incidents'
        if route == 'management' or route.startswith('management/'):
            base = root / 'management'
            route = route.removeprefix('management').lstrip('/')
        candidate = (base / route).resolve()
        return str(candidate if candidate.is_relative_to(base) else base / 'not-found')
    def log_message(self, *_):
        pass
print('Read-only legacy fixture: http://127.0.0.1:8080', flush=True)
ThreadingHTTPServer(('127.0.0.1',8080),Handler).serve_forever()
