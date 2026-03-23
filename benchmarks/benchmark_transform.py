"""Micro-benchmark for transform throughput."""

from __future__ import annotations

from time import perf_counter

from neurobridge import Config, NeuroBridge, Profile


def main() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    payload = " ".join(["This is a benchmark sentence for transform performance."] * 150)

    runs = 100
    start = perf_counter()
    for _ in range(runs):
        bridge.adapt(payload)
    total = perf_counter() - start

    print("benchmark_transform")
    print(f"runs={runs}")
    print(f"total_s={total:.4f}")
    print(f"avg_ms={(total / runs) * 1000:.2f}")
    print(f"cache={bridge.cache_stats()}")


if __name__ == "__main__":
    main()
