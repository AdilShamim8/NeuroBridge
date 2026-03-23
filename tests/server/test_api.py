"""Day 9 API tests using FastAPI TestClient."""

from fastapi.testclient import TestClient

from neurobridge.core.bridge import Config
from neurobridge.server.app import create_app
from neurobridge.server.config import ServerConfig


def make_client(tmp_path) -> TestClient:
    app = create_app(
        config=Config(
            memory_backend="sqlite", memory_path=str(tmp_path / "server.db"), auto_adjust_after=100
        ),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=500),
    )
    return TestClient(app)


def test_health_endpoint(tmp_path) -> None:
    client = make_client(tmp_path)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["memory_backend"] == "sqlite"


def test_adapt_endpoint_happy_and_error(tmp_path) -> None:
    client = make_client(tmp_path)

    ok = client.post(
        "/api/v1/adapt",
        json={"text": "This is critical and must be fixed ASAP.", "profile": "anxiety"},
    )
    assert ok.status_code == 200
    assert "adapted_text" in ok.json()

    bad = client.post("/api/v1/adapt", json={"text": "", "profile": "anxiety"})
    assert bad.status_code == 422


def test_adapt_batch_max_20(tmp_path) -> None:
    client = make_client(tmp_path)
    payload = {
        "texts": [f"Item {i} must be done ASAP." for i in range(20)],
        "profile": "anxiety",
    }
    response = client.post("/api/v1/adapt/batch", json=payload)
    assert response.status_code == 200
    assert len(response.json()["results"]) == 20

    too_many = {
        "texts": [f"Item {i}" for i in range(21)],
        "profile": "adhd",
    }
    bad = client.post("/api/v1/adapt/batch", json=too_many)
    assert bad.status_code == 422


def test_stream_endpoint_returns_sse(tmp_path) -> None:
    client = make_client(tmp_path)
    response = client.post("/api/v1/adapt/stream", json={"text": "Sentence one. Sentence two."})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"done": true' in response.text.lower()


def test_profile_set_get_feedback_delete_gdpr(tmp_path) -> None:
    client = make_client(tmp_path)

    set_resp = client.post(
        "/api/v1/profile",
        json={"user_id": "u1", "profile": "dyslexia", "custom_config": None},
    )
    assert set_resp.status_code == 200

    get_resp = client.get("/api/v1/profile/u1")
    assert get_resp.status_code == 200
    assert get_resp.json()["user_id"] == "u1"

    feedback = client.patch(
        "/api/v1/profile/u1/feedback",
        json={
            "original_text": "original",
            "adapted_text": "adapted",
            "user_edit": "edited",
        },
    )
    assert feedback.status_code == 200

    delete_resp = client.delete("/api/v1/profile/u1")
    assert delete_resp.status_code == 200

    not_found = client.get("/api/v1/profile/u1")
    assert not_found.status_code == 404


def test_quiz_questions_and_submit(tmp_path) -> None:
    client = make_client(tmp_path)

    questions = client.get("/api/v1/quiz/questions")
    assert questions.status_code == 200
    payload = questions.json()
    assert len(payload["questions"]) == 15

    answers = {item["id"]: "0" for item in payload["questions"]}
    submit = client.post("/api/v1/quiz/submit", json={"user_id": "quiz-u", "answers": answers})
    assert submit.status_code == 200
    body = submit.json()
    assert "primary_profile" in body
    assert "recommended_config" in body


def test_cors_headers_present(tmp_path) -> None:
    client = make_client(tmp_path)
    response = client.options(
        "/api/v1/adapt",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code in {200, 204}
    assert "access-control-allow-origin" in response.headers
