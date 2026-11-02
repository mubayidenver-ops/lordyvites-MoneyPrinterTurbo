"""Pairing and studio routes around the unmodified MoneyPrinterTurbo API."""

import hashlib
import hmac
import ipaddress
import json
import os
import secrets
import time
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

ASSETS = Path(__file__).parent / "studio"
COOKIE = "lordyvites_session"


def install_studio(app, api_key, pairing_code, source="pexels"):
    sessions = {}
    attempts = {}
    router = APIRouter()
    public = {"/", "/studio.js", "/studio.css", "/pair", "/health"}

    @app.middleware("http")
    async def paired_access(request: Request, call_next):
        # Host allowlisting also prevents DNS rebinding against the LAN server.
        host = request.url.hostname or ""
        try:
            address = ipaddress.ip_address(host)
            valid_host = address.is_private or address.is_loopback
        except ValueError:
            valid_host = host == "localhost"
        if not valid_host:
            return JSONResponse({"message": "Use the PC's local IP address"}, 400)
        if request.method not in {"GET", "HEAD"}:
            origin = request.headers.get("origin")
            if origin and origin != str(request.base_url).rstrip("/"):
                return JSONResponse({"message": "Origin not allowed"}, 403)
        if request.url.path not in public:
            token = request.cookies.get(COOKIE, "")
            digest = hashlib.sha256(token.encode()).hexdigest()
            expires = sessions.get(digest, 0)
            if expires < time.time():
                sessions.pop(digest, None)
                return JSONResponse({"message": "Pair with your PC to continue"}, 401)
            # Keep the engine's existing API and file authentication in place.
            headers = [(k, v) for k, v in request.scope["headers"] if k != b"x-api-key"]
            headers.append((b"x-api-key", api_key.encode()))
            request.scope["headers"] = headers
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    @router.get("/health")
    def health():
        return {"application": "lordyvites", "ready": True}

    @router.get("/")
    def index():
        return FileResponse(ASSETS / "index.html")

    @router.get("/studio.js")
    def javascript():
        return FileResponse(ASSETS / "studio.js", media_type="application/javascript")

    @router.get("/studio.css")
    def stylesheet():
        return FileResponse(ASSETS / "studio.css", media_type="text/css")

    @router.post("/pair")
    async def pair(request: Request):
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        # A bounded global bucket also avoids unbounded remote-client state.
        attempts.clear() if len(attempts) > 1024 else None
        recent = [t for t in attempts.get(client, []) if t > now - 60]
        if len(recent) >= 5:
            return JSONResponse({"message": "Wait one minute before trying again"}, 429)
        attempts[client] = recent + [now]
        if int(request.headers.get("content-length", "0") or 0) > 1024:
            return JSONResponse({"message": "Pairing request too large"}, 413)
        try:
            body = await request.body()
            if len(body) > 1024:
                return JSONResponse({"message": "Pairing request too large"}, 413)
            code = str(json.loads(body).get("code", "")).replace("-", "").replace(" ", "")
        except (ValueError, AttributeError):
            return JSONResponse({"message": "Invalid pairing request"}, 400)
        if not hmac.compare_digest(code.encode(), pairing_code.encode()):
            return JSONResponse({"message": "The pairing code is incorrect"}, 401)
        token = secrets.token_urlsafe(32)
        current = time.time()
        for key, expiry in list(sessions.items()):
            if expiry < current:
                del sessions[key]
        if len(sessions) >= 100:
            return JSONResponse({"message": "Restart the PC app to pair more devices"}, 429)
        sessions[hashlib.sha256(token.encode()).hexdigest()] = current + 86400
        response = JSONResponse({"paired": True})
        response.set_cookie(COOKIE, token, max_age=86400, httponly=True, samesite="strict",
                            secure=request.url.scheme == "https")
        return response

    @router.post("/unpair")
    def unpair(request: Request):
        token = request.cookies.get(COOKIE, "")
        sessions.pop(hashlib.sha256(token.encode()).hexdigest(), None)
        response = JSONResponse({"paired": False})
        response.delete_cookie(COOKIE)
        return response

    @router.get("/studio-status")
    def status():
        return {"source": source, "application": "Lordyvites Money Printer Turbo"}

    # Place the studio before the engine's catch-all static mount.
    app.router.routes[0:0] = router.routes
    return app


def main():
    import uvicorn
    from app.config import config
    # Never persist the engine API key. Sessions expire on every restart.
    api_key = secrets.token_urlsafe(32)
    config.app["api_key"] = api_key
    config.app["endpoint"] = ""
    config.app["max_concurrent_tasks"] = 1
    config.app["max_queued_tasks"] = 5
    from app.asgi import app
    code = os.environ.pop("LORDYVITES_PAIR_CODE")
    install_studio(app, api_key, code, config.app.get("desktop_video_source", "pexels"))
    uvicorn.run(app, host="0.0.0.0", port=8765, access_log=False, log_level="warning")


if __name__ == "__main__":
    main()
