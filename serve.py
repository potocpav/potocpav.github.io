#!/usr/bin/env python3
"""Local preview server that reloads the browser whenever a file in this folder changes.

Usage: python3 serve.py [port]    (default port 8000, then open http://localhost:8000/)

Standard library only. HTML pages are served with a small script injected that listens on
/__reload (server-sent events); only the top-level page listens.
Files and folders starting with a dot (such as .git) are not watched.
"""
import http.server
import os
import sys
import threading
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
SNIPPET = b"""<script>
  // Injected by serve.py: reload when a file changes.
  if (window.top === window) new EventSource('/__reload').onmessage = () => location.reload();
</script>
"""

version = 0
changed = threading.Condition()


def snapshot():
    state = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for name in filenames:
            if name.startswith('.'):
                continue
            path = os.path.join(dirpath, name)
            try:
                state[path] = os.stat(path).st_mtime_ns
            except FileNotFoundError:
                pass
    return state


def watch():
    global version
    last = snapshot()
    while True:
        time.sleep(0.3)
        current = snapshot()
        if current == last:
            continue
        # Let editors finish writing (save, rename, reformat) before reloading.
        time.sleep(0.15)
        previous, last = last, snapshot()
        changes = sorted(os.path.relpath(p, ROOT) for p in previous.keys() | last.keys() if previous.get(p) != last.get(p))
        print('changed:', ', '.join(changes), flush=True)
        with changed:
            version += 1
            changed.notify_all()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_GET(self):
        url_path = self.path.split('?', 1)[0].split('#', 1)[0]
        if url_path == '/__reload':
            return self.events()
        path = self.translate_path(self.path)
        if os.path.isdir(path) and url_path.endswith('/'):
            path = os.path.join(path, 'index.html')
        if path.endswith('.html') and os.path.isfile(path):
            return self.html(path)
        return super().do_GET()

    def html(self, path):
        with open(path, 'rb') as f:
            body = f.read()
        i = body.rfind(b'</body>')
        body = body[:i] + SNIPPET + body[i:] if i >= 0 else body + SNIPPET
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def events(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.end_headers()
        with changed:
            seen = version
        try:
            while True:
                with changed:
                    changed.wait_for(lambda: version != seen, timeout=15)
                    reload, seen = version != seen, version
                # A comment line every 15 s keeps the connection alive.
                self.wfile.write(b'data: reload\n\n' if reload else b': ping\n\n')
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        if not self.path.startswith('/__reload'):
            super().log_message(format, *args)


if __name__ == '__main__':
    threading.Thread(target=watch, daemon=True).start()
    server = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    server.daemon_threads = True
    print(f'Previewing {ROOT} at http://localhost:{PORT}/ (reloads on change, Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
