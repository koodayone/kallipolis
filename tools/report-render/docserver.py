#!/usr/bin/env python3
"""Tiny local doc-server: serves the editable one-pager and writes autosaves
straight back to the source file, so the file on disk is always current. The
HTML's toolbar JS POSTs edits to /save on a debounce; open the page, edit in the
browser (contenteditable), and the file updates underneath you.

    python3 docserver.py [SRC.html] [PORT]   # then open http://localhost:PORT/

Note: the toolbar also polls /mtime for cross-tab live-reload; this server does
not implement it (the client degrades gracefully — autosave still works).
"""
import http.server
import socketserver
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else '/Users/dayonekoo/Desktop/code/kallipolis/research/swp-strategy/svamp-pathway-49-9041-doc.html'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8787


class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body=b'', ctype='text/html; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        if self.path.split('?')[0] in ('/', '/index.html'):
            try:
                with open(SRC, 'rb') as f:
                    self._send(200, f.read())
            except Exception as e:
                self._send(500, str(e).encode())
        else:
            self._send(404, b'not found')

    def do_POST(self):
        if self.path.split('?')[0] == '/save':
            n = int(self.headers.get('Content-Length', 0))
            data = self.rfile.read(n)
            try:
                with open(SRC, 'wb') as f:
                    f.write(data)
                self._send(200, b'ok', 'text/plain')
            except Exception as e:
                self._send(500, str(e).encode(), 'text/plain')
        else:
            self._send(404, b'no', 'text/plain')

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORT), H) as s:
    print('doc-server live: http://localhost:%d/  ->  %s' % (PORT, SRC), flush=True)
    s.serve_forever()
