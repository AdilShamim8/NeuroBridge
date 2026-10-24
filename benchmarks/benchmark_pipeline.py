"""Benchmark end-to-end chat pipeline latency.

Methodology:
- unique prompts per call (repeating three prompts measures the transform
  cache after the first iteration)
- warmup calls before measurement
- p50/p95/p99 from the per-call latency distribution
"""

from __future__ import annotations

from time import perf_counter

from neurobridge import Config, NeuroBridge, Profile

WARMUP_CALLS = 10
CALLS = 100


def _percentile(sorted_samples: list[float], fraction: float) -> float:
    if not sorted_samples:
        return 0.0
    index = min(len(sorted_samples) - 1, int(round(fraction * (len(sorted_samples) - 1))))
    return sorted_samples[index]


def _prompt(index: int) -> str:
    bases = [
        "This is critical and must be done {i}.",
        "Review these numbers: 25%, 100000, and $12000 - case {i}.",
        "Summarise this plan {i} and include one example.",
    ]
    return bases[index % len(bases)].format(i=index)


def main() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ANXIETY)

    for index in range(WARMUP_CALLS):
        bridge.chat(_prompt(-index - 1))

    samples: list[float] = []
    for index in range(CALLS):
        start = perf_counter()
        bridge.chat(_prompt(index))
        samples.append((perf_counter() - start) * 1000)

    samples.sort()
    total = sum(samples)

    print("benchmark_pipeline")
    print(f"calls={CALLS} warmup={WARMUP_CALLS} unique_prompts=yes")
    print(f"total_s={total / 1000:.4f}")
    print(f"avg_ms={total / CALLS:.2f}")
    print(f"p50_ms={_percentile(samples, 0.50):.2f}")
    print(f"p95_ms={_percentile(samples, 0.95):.2f}")
    print(f"p99_ms={_percentile(samples, 0.99):.2f}")
    print(f"cache={bridge.cache_stats()}")


if __name__ == "__main__":
    main()
