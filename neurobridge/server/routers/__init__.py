"""API routers for NeuroBridge server."""

from neurobridge.server.routers.adapt import router as adapt_router
from neurobridge.server.routers.health import router as health_router
from neurobridge.server.routers.profiles import router as profiles_router
from neurobridge.server.routers.quiz import router as quiz_router

__all__ = ["adapt_router", "health_router", "profiles_router", "quiz_router"]
