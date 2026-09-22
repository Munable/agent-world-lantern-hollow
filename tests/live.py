from pathlib import Path
import os
import socket
import subprocess
import sys
import tempfile
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]


class LiveServer:
    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'test.sqlite3'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.url = f'http://127.0.0.1:{self.port}'
        self.logpath = Path(self.tmp.name) / 'server.log'
        self.log = self.logpath.open('w', encoding='utf-8')
        self.proc = None
        try:
            self.start()
            return self
        except BaseException:
            self.__exit__()
            raise

    def start(self):
        self.proc = subprocess.Popen(
            [sys.executable, '-u', '-m', 'lantern_hollow.server', '--db', str(self.db), '--port', str(self.port)],
            stdout=self.log, stderr=subprocess.STDOUT, cwd=ROOT,
        )
        timeout = min(240, max(30, float(os.getenv('WORLD_TEST_STARTUP_TIMEOUT', '120'))))
        last = 'no response'
        with httpx.Client(trust_env=False, timeout=.4) as client:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if self.proc.poll() is not None:
                    raise RuntimeError(self.logpath.read_text(encoding='utf-8', errors='replace')[-3000:])
                try:
                    response = client.get(self.url + '/health')
                    if response.status_code == 200:
                        return
                    last = f'HTTP {response.status_code}'
                except httpx.HTTPError as exc:
                    last = type(exc).__name__
                time.sleep(.1)
        raise RuntimeError('Readiness timeout: ' + last + chr(10) + self.logpath.read_text(encoding='utf-8', errors='replace')[-3000:])

    def stop(self):
        if self.proc is None:
            return
        if self.proc.poll() is None:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(self.proc.pid), '/T', '/F'], capture_output=True)
            else:
                self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)

    def restart(self):
        self.stop()
        self.start()

    def __exit__(self, *args):
        self.stop()
        self.log.close()
        self.tmp.cleanup()
