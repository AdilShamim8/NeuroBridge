"""Day 22 expanded API tests for edge cases, limits, and concurrency."""

from __future__ import annotations

import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from neurobridge.core.bridge import Config
from neurobridge.server.app import create_app
from neurobridge.server.config import ServerConfig


def _make_client(tmp_path, rate_limit: int = 500) -> TestClient:
    app = create_app(
        config=Config(
            memory_backend="sqlite", memory_path=str(tmp_path / "api-ext.db"), auto_adjust_after=200
        ),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=rate_limit),
    )
    return TestClient(app, raise_server_exceptions=False)


def test_auth_disabled_by_default(tmp_path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_missing_fields_and_wrong_types(tmp_path) -> None:
    client = _make_client(tmp_path)

    missing_text = client.post("/api/v1/adapt", json={"profile": "adhd"})
    assert missing_text.status_code == 422

    wrong_text_type = client.post("/api/v1/adapt", json={"text": ["bad"], "profile": "adhd"})
    assert wrong_text_type.status_code == 422

    missing_user_id = client.post(
        "/api/v1/profile", json={"profile": "adhd", "custom_config": None}
    )
    assert missing_user_id.status_code == 422


def test_oversized_batch_rejected(tmp_path) -> None:
    client = _make_client(tmp_path)
    payload = {"texts": [f"item {i}" for i in range(40)], "profile": "adhd"}
    response = client.post("/api/v1/adapt/batch", json=payload)
    assert response.status_code == 422


def test_rate_limit_returns_429(tmp_path) -> None:
    client = _make_client(tmp_path, rate_limit=3)
    for _ in range(3):
        ok = client.get("/api/v1/health")
        assert ok.status_code == 200

    limited = client.get("/api/v1/health")
    assert limited.status_code == 429


@pytest.mark.anyio
async def test_concurrent_requests_asyncio_gather(tmp_path) -> None:
    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=1000),
    )
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:

        async def call_once(idx: int):
            payload = {
                "text": f"This is critical and must be done ASAP. #{idx}",
                "profile": "anxiety",
            }
            return await client.post("/api/v1/adapt", json=payload)

        responses = await asyncio.gather(*[call_once(i) for i in range(20)])

    assert all(resp.status_code == 200 for resp in responses)


def test_cors_headers_present_on_post(tmp_path) -> None:
    client = _make_client(tmp_path)
    response = client.post(
        "/api/v1/adapt",
        json={"text": "hello", "profile": "adhd"},
        headers={"Origin": "http://example.com"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in {"*", "http://example.com"}


def test_profile_custom_and_invalid_profile_paths(tmp_path) -> None:
    client = _make_client(tmp_path)

    custom_payload = {
        "user_id": "u-custom",
        "profile": "custom",
        "custom_config": {
            "chunk_size": 2,
            "tone": "calm",
            "ambiguity_resolution": "explicit",
            "number_format": "contextual",
            "leading_style": "summary_first",
            "reading_level": 6,
            "max_sentence_words": 12,
        },
    }
    custom_resp = client.post("/api/v1/profile", json=custom_payload)
    assert custom_resp.status_code == 200
    assert custom_resp.json()["profile"] == "custom"

    invalid_resp = client.post(
        "/api/v1/profile",
        json={"user_id": "u-bad", "profile": "not-a-profile", "custom_config": None},
    )
    assert invalid_resp.status_code == 422


def test_profile_export_endpoint(tmp_path) -> None:
    client = _make_client(tmp_path)
    client.post(
        "/api/v1/profile", json={"user_id": "u-export", "profile": "adhd", "custom_config": None}
    )
    client.patch(
        "/api/v1/profile/u-export/feedback",
        json={
            "original_text": "original",
            "adapted_text": "adapted",
            "user_edit": "edited",
        },
    )

    export = client.get("/api/v1/profile/u-export/export")
    assert export.status_code == 200
    body = export.json()
    assert body["user_id"] == "u-export"
    assert isinstance(body["feedback"], list)
    assert "user_edit_hash" in body["feedback"][0]


def test_security_headers_present(tmp_path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_request_size_limit_rejects_large_payload(tmp_path) -> None:
    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(
            allowed_origins=["*"],
            rate_limit_per_minute=100,
            max_request_size_bytes=64,
        ),
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/adapt",
        json={"text": "x" * 500, "profile": "adhd"},
    )
    assert response.status_code == 413


def test_bearer_api_key_authentication(tmp_path) -> None:
    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(
            allowed_origins=["*"],
            require_api_key=True,
            api_key="secret-key",
            rate_limit_per_minute=100,
        ),
    )
    client = TestClient(app)

    unauthorized = client.get("/api/v1/health")
    assert unauthorized.status_code == 401

    authorized = client.get("/api/v1/health", headers={"Authorization": "Bearer secret-key"})
    assert authorized.status_code == 200


def test_get_profile_without_memory_backend_returns_404() -> None:
    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=100),
    )
    client = TestClient(app)
    response = client.get("/api/v1/profile/missing")
    assert response.status_code == 404
