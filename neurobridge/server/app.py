"""FastAPI application entrypoint for NeuroBridge server."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from neurobridge.core.bridge import Config, NeuroBridge
from neurobridge.server.config import ServerConfig
from neurobridge.server.middleware import (
    ApiKeyMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    TimeoutMiddleware,
    TimingMiddleware,
)
from neurobridge.server.routers import adapt_router, health_router, profiles_router, quiz_router


def create_app(config: Config | None = None, server_config: ServerConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI app instance."""
    cfg = config or Config.from_env()
    srv_cfg = server_config or ServerConfig.from_env()

    app = FastAPI(
        title="NeuroBridge API",
        description="REST API for adaptive cognitive text transformation",
        version="0.1.0",
    )
    app.state.bridge = NeuroBridge(config=cfg)
    app.state.server_config = srv_cfg

    app.add_middleware(
        CORSMiddleware,
        allow_origins=srv_cfg.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=srv_cfg.max_request_size_bytes)
    app.add_middleware(TimeoutMiddleware, timeout_seconds=srv_cfg.request_timeout_seconds)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        per_ip_per_minute=srv_cfg.rate_limit_per_minute,
        per_key_per_minute=srv_cfg.api_key_rate_limit_per_minute,
    )
    app.add_middleware(ApiKeyMiddleware, api_key=srv_cfg.api_key, enabled=srv_cfg.require_api_key)

    app.include_router(health_router, prefix=srv_cfg.api_prefix)
    app.include_router(adapt_router, prefix=srv_cfg.api_prefix)
    app.include_router(profiles_router, prefix=srv_cfg.api_prefix)
    app.include_router(quiz_router, prefix=srv_cfg.api_prefix)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        _ = request
        safe_errors = []
        for error in exc.errors():
            safe_errors.append(
                {
                    "type": error.get("type"),
                    "loc": error.get("loc"),
                    "msg": error.get("msg"),
                }
            )
        return JSONResponse(
            status_code=422, content={"detail": "Validation error", "errors": safe_errors}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        _ = exc
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    return app


app = create_app()
