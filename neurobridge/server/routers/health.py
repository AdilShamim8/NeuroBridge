"""Health endpoints."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request):
    bridge = request.app.state.bridge
    return {
        "status": "ok",
        "version": "0.1.0",
        "memory_backend": bridge.config.memory_backend,
    }
