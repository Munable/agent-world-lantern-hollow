"""Explicit, isolated frontend test environments. No engine fallback in matrix runs."""
import os
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from pathlib import Path

def launch_browser(p,name=None):
    name=name or os.getenv('FRONTEND_BROWSER','chromium')
    if name=='edge':return p.chromium.launch(channel='msedge',headless=True)
    if name not in ('chromium','firefox','webkit'):raise ValueError('Unsupported test browser')
    return getattr(p,name).launch(headless=True)

@contextmanager
def static_client(directory):
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    for port in range(24200,24300):
        try:s=ThreadingHTTPServer(('127.0.0.1',port),partial(Quiet,directory=str(directory)));break
        except OSError:continue
    else:raise RuntimeError('No browser-safe fixture port')
    thread=Thread(target=s.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{s.server_port}'
    finally:s.shutdown();s.server_close();thread.join(timeout=5)
