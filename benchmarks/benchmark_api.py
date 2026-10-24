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

    warmup = 10
    runs = 100
    # Unique payloads defeat the transform cache; the in-process ASGI transport
    # measures app overhead without network/uvicorn.
    for index in range(warmup):
        client.post("/api/v1/adapt", json={"text": f"warmup {index} " + "sample sentence " * 120})

    samples: list[float] = []
    for index in range(runs):
        payload = {"text": f"run {index} " + "This is a sample API benchmark sentence. " * 120}
        start = perf_counter()
        response = client.post("/api/v1/adapt", json=payload)
        elapsed = (perf_counter() - start) * 1000
        if response.status_code != 200:
            raise SystemExit(f"unexpected status {response.status_code}")
        samples.append(elapsed)

    samples.sort()

    def pct(fraction: float) -> float:
        pos = min(len(samples) - 1, int(round(fraction * (len(samples) - 1))))
        return samples[pos]

    print("benchmark_api (in-process ASGI transport, no network/uvicorn)")
    print(f"runs={runs} warmup={warmup} unique_payloads=yes")
    print(f"avg_ms={sum(samples) / runs:.2f}")
    print(f"p50_ms={pct(0.50):.2f}")
    print(f"p95_ms={pct(0.95):.2f}")
    print(f"p99_ms={pct(0.99):.2f}")


if __name__ == "__main__":
    main()
