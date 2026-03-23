"""Benchmark end-to-end chat pipeline latency."""

from __future__ import annotations

from time import perf_counter

from neurobridge import Config, NeuroBridge, Profile


def main() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ANXIETY)

    prompts = [
        "This is critical and must be done ASAP.",
        "Review these numbers: 25%, 100000, and $12000.",
        "Summarise this plan and include one example.",
    ]

    start = perf_counter()
    results = [bridge.chat(prompt) for prompt in prompts * 50]
    total = perf_counter() - start

    print("benchmark_pipeline")
    print(f"calls={len(results)}")
    print(f"total_s={total:.4f}")
    print(f"p50_est_ms={(total / len(results)) * 1000:.2f}")
    print(f"cache={bridge.cache_stats()}")


if __name__ == "__main__":
    main()
