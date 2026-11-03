#!/usr/bin/env python3
"""Serve the folder for local use, telling the browser never to keep a copy.

`python3 -m http.server` sends no caching instructions, so a browser may keep showing an old script or an old
asset sheet after you rebuild. This sends `Cache-Control: no-store`, so a normal reload always shows the newest files.
It listens on this machine only.

    python3 tools/serve.py [port]        then visit http://localhost:4321
"""
import functools
import http.server
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4321
    print(f'serving {ROOT} at http://localhost:{port} (no caching, this machine only)')
    http.server.test(HandlerClass=functools.partial(NoCache, directory=str(ROOT)), port=port, bind='127.0.0.1')
