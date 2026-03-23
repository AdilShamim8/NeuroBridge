"""Server configuration for NeuroBridge FastAPI app."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import List


@dataclass(slots=True)
class ServerConfig:
    """HTTP server settings and middleware behavior."""

    allowed_origins: List[str]
    api_prefix: str = "/api/v1"
    require_api_key: bool = False
    api_key: str = ""
    rate_limit_per_minute: int = 60
    api_key_rate_limit_per_minute: int = 120
    max_request_size_bytes: int = 1_048_576
    request_timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "ServerConfig":
        origins_raw = os.getenv("NEUROBRIDGE_ALLOWED_ORIGINS", "*")
        origins = [item.strip() for item in origins_raw.split(",") if item.strip()]
        if not origins:
            origins = ["*"]

        api_key = os.getenv("NEUROBRIDGE_API_KEY", "")
        require_api_key = bool(api_key)

        try:
            rate_limit = int(os.getenv("NEUROBRIDGE_RATE_LIMIT_PER_MINUTE", "60"))
        except ValueError:
            rate_limit = 60

        try:
            key_rate_limit = int(os.getenv("NEUROBRIDGE_API_KEY_RATE_LIMIT_PER_MINUTE", "120"))
        except ValueError:
            key_rate_limit = 120

        try:
            max_request_size_bytes = int(os.getenv("NEUROBRIDGE_MAX_REQUEST_SIZE_BYTES", "1048576"))
        except ValueError:
            max_request_size_bytes = 1_048_576

        try:
            request_timeout_seconds = int(os.getenv("NEUROBRIDGE_REQUEST_TIMEOUT_SECONDS", "30"))
        except ValueError:
            request_timeout_seconds = 30

        return cls(
            allowed_origins=origins,
            api_prefix=os.getenv("NEUROBRIDGE_API_PREFIX", "/api/v1"),
            require_api_key=require_api_key,
            api_key=api_key,
            rate_limit_per_minute=max(1, rate_limit),
            api_key_rate_limit_per_minute=max(1, key_rate_limit),
            max_request_size_bytes=max(1, max_request_size_bytes),
            request_timeout_seconds=max(1, request_timeout_seconds),
        )
