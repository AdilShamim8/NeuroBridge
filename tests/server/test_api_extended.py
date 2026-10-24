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


def test_cors_preflight_succeeds_with_api_key_enabled() -> None:
    """Regression: CORSMiddleware was the innermost layer while ApiKeyMiddleware
    was outermost, so browser preflight OPTIONS requests (which never carry
    Authorization) got a bare 401 without CORS headers - browser clients could
    not use the API at all when auth was on."""
    from neurobridge.server.app import create_app
    from neurobridge.server.config import ServerConfig

    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(
            allowed_origins=["https://example.com"],
            require_api_key=True,
            api_key="secret-key-123",
        ),
    )
    client = TestClient(app)

    response = client.options(
        "/api/v1/adapt",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://example.com"


def test_auth_rejections_carry_cors_headers() -> None:
    """Even real 401s must be readable by browsers, so CORS headers have to be
    attached to middleware-generated rejections."""
    from neurobridge.server.app import create_app
    from neurobridge.server.config import ServerConfig

    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(
            allowed_origins=["https://example.com"],
            require_api_key=True,
            api_key="secret-key-123",
        ),
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/adapt",
        json={"text": "hello"},
        headers={"Origin": "https://example.com"},
    )
    assert response.status_code == 401
    assert response.headers.get("access-control-allow-origin") == "https://example.com"


def test_api_key_identity_is_a_digest_not_the_secret() -> None:
    """Regression: the middleware stored the first 12 characters of the API key
    as the rate-limit identity, keeping a slice of the secret in request state."""
    from neurobridge.server.middleware import ApiKeyMiddleware

    async def run() -> str:
        seen = {}

        async def call_next(request):
            seen["api_key_id"] = getattr(request.state, "api_key_id", None)
            from starlette.responses import PlainTextResponse

            return PlainTextResponse("ok")

        middleware = ApiKeyMiddleware(
            app=None, api_key="super-secret-value-do-not-leak", enabled=True
        )

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [
                (b"authorization", b"Bearer super-secret-value-do-not-leak"),
            ],
            "query_string": b"",
        }

        from starlette.datastructures import State
        from starlette.requests import Request

        request = Request(scope)
        request._state = State()
        await middleware.dispatch(request, call_next)
        return seen["api_key_id"] or ""

    import asyncio

    identity = asyncio.run(run())
    assert identity
    assert "super-secret" not in identity
    assert len(identity) == 16


def test_request_profile_does_not_bleed_into_later_requests() -> None:
    """Regression: the adapt router called bridge.set_profile() on the single
    shared bridge instance, so one request's 'profile' parameter changed the
    output of every subsequent profile-less request (and raced under
    concurrency). Profiles are now resolved per request."""
    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=1000),
    )
    client = TestClient(app)

    first = client.post(
        "/api/v1/adapt", json={"text": "Hello there friend.", "profile": "dyslexia"}
    )
    assert first.status_code == 200
    assert first.json()["profile_used"] == "dyslexia"

    # A follow-up request without a profile must fall back to the bridge
    # default (adhd), not inherit dyslexia from the previous request.
    second = client.post("/api/v1/adapt", json={"text": "Hello there friend."})
    assert second.status_code == 200
    assert second.json()["profile_used"] == "adhd"


def test_profile_used_is_serialized_as_wire_name() -> None:
    """Regression: str(Profile.DYSLEXIA) produced 'Profile.DYSLEXIA' in API
    responses while the quiz endpoint returned 'dyslexia'."""
    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=1000),
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/adapt", json={"text": "Some content here.", "profile": "dyslexia"}
    )
    assert response.status_code == 200
    assert response.json()["profile_used"] == "dyslexia"
    assert "Profile." not in response.json()["profile_used"]


def test_whitespace_only_text_returns_422_not_500() -> None:
    """Regression: pydantic min_length=1 let '   ' through and bridge.chat
    raised ValueError, surfacing as an opaque 500."""
    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=1000),
    )
    client = TestClient(app)

    response = client.post("/api/v1/adapt", json={"text": "   "})
    assert response.status_code == 422

    batch = client.post("/api/v1/adapt/batch", json={"texts": ["ok text", "   "]})
    assert batch.status_code == 422


def test_quiz_out_of_range_answer_returns_400_not_500() -> None:
    """Regression: '99' and '-1' parsed as ints and crashed score_answers with
    an unhandled ValueError (500)."""
    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=1000),
    )
    client = TestClient(app)

    questions = client.get("/api/v1/quiz/questions").json()["questions"]
    valid = {q["id"]: "0" for q in questions}
    valid["q1"] = "99"
    response = client.post("/api/v1/quiz/submit", json={"answers": valid, "user_id": "quiz-user"})
    assert response.status_code == 400

    valid["q1"] = "-1"
    response = client.post("/api/v1/quiz/submit", json={"answers": valid, "user_id": "quiz-user"})
    assert response.status_code == 400


def test_invalid_path_user_id_returns_422_not_500(tmp_path) -> None:
    """Regression: DELETE /profile/bad id and the export endpoint propagated
    ValueError from the bridge as 500s."""
    app = create_app(
        config=Config(memory_backend="sqlite", memory_path=str(tmp_path / "m.db")),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=1000),
    )
    client = TestClient(app)

    deleted = client.delete("/api/v1/profile/bad%20id")
    assert deleted.status_code == 422

    exported = client.get("/api/v1/profile/bad%20id/export")
    assert exported.status_code == 422

    got = client.get("/api/v1/profile/bad%20id")
    assert got.status_code == 422


def test_chunked_body_size_limit_is_enforced() -> None:
    """Regression: RequestSizeLimitMiddleware only inspected Content-Length, so
    chunked transfer-encoding bypassed the cap entirely."""
    import httpx

    from neurobridge.server.app import create_app
    from neurobridge.server.config import ServerConfig

    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(
            allowed_origins=["*"], rate_limit_per_minute=1000, max_request_size_bytes=64
        ),
    )

    async def run() -> int:
        import json as _json

        payload = _json.dumps({"text": "x" * 200}).encode()

        async def chunked():
            yield payload[:64]
            yield payload[64:]

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # A generator body forces chunked transfer-encoding: no
            # Content-Length header is ever sent.
            response = await client.post(
                "/api/v1/adapt",
                content=chunked(),
                headers={"content-type": "application/json"},
            )
            return response.status_code

    assert asyncio.run(run()) == 413


def test_rate_limiter_evicts_stale_identities() -> None:
    """The limiter's identity tables must stay bounded: every unique client IP
    kept a deque forever, so a scan of spoofed source addresses grew memory
    without bound."""
    from datetime import datetime, timedelta, timezone

    from neurobridge.server.middleware import RateLimitMiddleware

    limiter = RateLimitMiddleware(app=None, per_ip_per_minute=5, per_key_per_minute=5)
    now = datetime.now(timezone.utc)
    # Simulate many identities whose only traffic is far outside the window.
    for index in range(limiter.MAX_TRACKED_IDENTITIES + 50):
        identity = f"10.0.{index // 256}.{index % 256}"
        limiter._ip_requests[identity].append(now - timedelta(minutes=10))

    limiter._prune_stale(limiter._ip_requests, now - timedelta(minutes=1))
    assert len(limiter._ip_requests) <= limiter.MAX_TRACKED_IDENTITIES
