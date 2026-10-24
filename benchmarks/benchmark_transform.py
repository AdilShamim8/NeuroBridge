"""Micro-benchmark for transform throughput.

Methodology:
- unique payloads per run (repeating one payload measures the pipeline's LRU
  cache, not the transform)
- warmup runs before measurement
- p50/p95/p99 from the per-run latency distribution
"""

from __future__ import annotations

from time import perf_counter

from neurobridge import Config, NeuroBridge, Profile

WARMUP_RUNS = 10
RUNS = 100


def _percentile(sorted_samples: list[float], fraction: float) -> float:
    if not sorted_samples:
        return 0.0
    index = min(len(sorted_samples) - 1, int(round(fraction * (len(sorted_samples) - 1))))
    return sorted_samples[index]


def main() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)

    # Unique payloads defeat the transform cache so every run does real work.
    payloads = [
        " ".join([f"This is benchmark sentence {run} for transform performance."] * 150)
        for run in range(WARMUP_RUNS + RUNS)
    ]

    for payload in payloads[:WARMUP_RUNS]:
        bridge.adapt(payload)

    samples: list[float] = []
    for payload in payloads[WARMUP_RUNS:]:
        start = perf_counter()
        bridge.adapt(payload)
        samples.append((perf_counter() - start) * 1000)

    samples.sort()
    total = sum(samples)

    print("benchmark_transform")
    print(f"runs={RUNS} warmup={WARMUP_RUNS} unique_payloads=yes")
    print(f"total_s={total / 1000:.4f}")
    print(f"avg_ms={total / RUNS:.2f}")
    print(f"p50_ms={_percentile(samples, 0.50):.2f}")
    print(f"p95_ms={_percentile(samples, 0.95):.2f}")
    print(f"p99_ms={_percentile(samples, 0.99):.2f}")
    print(f"cache={bridge.cache_stats()}")


if __name__ == "__main__":
    main()
