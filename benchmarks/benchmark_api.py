"""Benchmark API adapt endpoint with FastAPI test client."""

from __future__ import annotations

from time import perf_counter

from fastapi.testclient import TestClient

from neurobridge import Config
from neurobridge.server.app import create_app
from neurobridge.server.config import ServerConfig


def main() -> None:
    app = create_app(
        config=Config(memory_backend="none"),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=10_000),
    )
    client = TestClient(app)
    payload = {"text": " ".join(["This is a sample API benchmark sentence."] * 120)}

    runs = 200
    start = perf_counter()
    success = 0
    for _ in range(runs):
        response = client.post("/api/v1/adapt", json=payload)
        if response.status_code == 200:
            success += 1
    elapsed = perf_counter() - start

    print("benchmark_api")
    print(f"runs={runs}")
    print(f"success={success}")
    print(f"total_s={elapsed:.4f}")
    print(f"avg_ms={(elapsed / runs) * 1000:.2f}")


if __name__ == "__main__":
    main()
