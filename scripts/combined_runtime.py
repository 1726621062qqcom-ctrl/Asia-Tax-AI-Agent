"""Bounded, real HTTP knowledge service for combined acceptance checks."""
from contextlib import contextmanager
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
from time import monotonic, sleep

import httpx

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def knowledge_server(*, on_start=None):
    from packages.domain_bridge.bridge import release_path, verify_release

    release = release_path()
    verify_release(release)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    token = secrets.token_urlsafe(32)
    # The C process needs library paths, not model or case-database credentials.
    env = {k: v for k, v in os.environ.items() if k in
           ('PATH', 'HOME', 'TMPDIR', 'SYSTEMROOT', 'LANG', 'LC_ALL')}
    env.update(FSIE_AGENT_C_TOKEN=token, FSIE_TAX_ENGINE_RELEASE_DIR=str(release))
    process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'apps.knowledge_api.main:app',
         '--host', '127.0.0.1', '--port', str(port), '--log-level', 'error'],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}'
    try:
        started = monotonic()
        while True:
            try:
                if httpx.get(url + '/health', timeout=2).json().get('knowledge_ready'):
                    break
            except (httpx.HTTPError, ValueError):
                pass
            if process.poll() is not None or monotonic() - started > 15:
                raise RuntimeError('knowledge_server_unavailable')
            sleep(.1)
        if on_start is not None:
            on_start(process)
        yield url, token
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
