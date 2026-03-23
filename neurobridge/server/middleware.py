"""Custom FastAPI middleware for NeuroBridge server."""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import time
from typing import Deque, DefaultDict
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Processing-Time"] = f"{elapsed:.2f}ms"
        return response


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str, enabled: bool) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.api_key = api_key
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if not self.enabled:
            return await call_next(request)
        auth_header = request.headers.get("Authorization", "")
        provided = ""
        if auth_header.startswith("Bearer "):
            provided = auth_header[7:].strip()
        if provided != self.api_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
        request.state.api_key_id = provided[:12] if provided else "unknown"
        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int = 1_048_576) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.max_bytes = max(1, max_bytes)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400, content={"detail": "Invalid Content-Length header"}
                )
            if size > self.max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request payload too large (max {self.max_bytes} bytes)"},
                )
        return await call_next(request)


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout_seconds: int = 30) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.timeout_seconds = max(1, timeout_seconds)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            return JSONResponse(status_code=504, content={"detail": "Request timed out"})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, per_ip_per_minute: int = 60, per_key_per_minute: int = 120) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.per_ip_per_minute = max(1, per_ip_per_minute)
        self.per_key_per_minute = max(1, per_key_per_minute)
        self._ip_requests: DefaultDict[str, Deque[datetime]] = defaultdict(deque)
        self._key_requests: DefaultDict[str, Deque[datetime]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        ip = request.client.host if request.client else "unknown"
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)

        ip_queue = self._ip_requests[ip]
        while ip_queue and ip_queue[0] < window_start:
            ip_queue.popleft()
        if len(ip_queue) >= self.per_ip_per_minute:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        ip_queue.append(now)

        key_id = getattr(request.state, "api_key_id", "")
        if key_id:
            key_queue = self._key_requests[key_id]
            while key_queue and key_queue[0] < window_start:
                key_queue.popleft()
            if len(key_queue) >= self.per_key_per_minute:
                return JSONResponse(
                    status_code=429, content={"detail": "Rate limit exceeded for API key"}
                )
            key_queue.append(now)

        return await call_next(request)
