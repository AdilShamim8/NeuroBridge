"""Benchmark memory backends with graceful Redis fallback."""

from __future__ import annotations

from time import perf_counter

from neurobridge.core.memory import InMemoryStore, RedisMemoryStore, create_feedback_record
from neurobridge.core.profile import DEFAULT_PROFILE_CONFIGS, Profile


def _run_store(name: str, store, loops: int = 1000) -> None:
    profile = DEFAULT_PROFILE_CONFIGS[Profile.ADHD]
    user_id = f"{name}-user"

    start = perf_counter()
    for idx in range(loops):
        store.save_profile(user_id, profile)
        store.increment_interaction(user_id)
        store.save_feedback(
            create_feedback_record(
                user_id=user_id,
                original_text="Original text",
                adapted_text="Adapted text",
                user_edit=f"Edit {idx}",
            )
        )
    elapsed = perf_counter() - start

    print(f"{name}: loops={loops} total_s={elapsed:.4f} avg_ms={(elapsed / loops) * 1000:.3f}")


def main() -> None:
    print("benchmark_memory")
    _run_store("inmemory", InMemoryStore())
    store = RedisMemoryStore("redis://localhost:6399/0")
    # The constructor warns and falls back when no Redis is listening; report
    # which backend the numbers actually measured instead of implying Redis.
    backend = "redis" if store._redis is not None else "in-memory fallback (no redis server)"
    _run_store(f"redis-store [{backend}]", store)


if __name__ == "__main__":
    main()
