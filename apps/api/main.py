"""Local research API and optional built chat frontend."""

from __future__ import annotations

import os
import re

from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from apps.api.chat import router
from fastapi import Request
from fastapi.responses import JSONResponse
import logging
import traceback

logger = logging.getLogger(__name__)

app = FastAPI(title="Asia Tax AI Agent — HK FSIE L0", version="0.1.0")
from apps.api.auth import router as auth_router
app.include_router(auth_router)
app.include_router(router)
# Trust only this service's platform hostname, never every Render tenant.
allowed_hosts = ["127.0.0.1", "localhost", "testserver"]
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
if re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.onrender\.com", render_hostname):
    allowed_hosts.append(render_hostname)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


@app.middleware("http")
async def private_responses(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        # Provider errors, database URLs and user input must not escape into responses.
        # Log locations and exception types only: exception messages/locals may contain secrets.
        frames = traceback.extract_tb(exc.__traceback__)
        logger.error('Request failed: %s; locations=%s', type(exc).__name__,
                     ' > '.join(f'{Path(frame.filename).name}:{frame.lineno}:{frame.name}' for frame in frames))
        response = JSONResponse({"detail": "service_unavailable"}, status_code=503)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "release_level": "L0"}


frontend = Path(__file__).resolve().parents[1] / "web" / "dist"
if frontend.is_dir():
    app.mount("/", StaticFiles(directory=frontend, html=True), name="chat_frontend")
