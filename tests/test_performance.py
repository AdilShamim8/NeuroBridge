"""Day 13 performance and resilience tests."""

from __future__ import annotations

import asyncio
from time import perf_counter

from neurobridge import Config, NeuroBridge, Profile
from neurobridge.core.memory import FeedbackRecord, RedisMemoryStore, create_feedback_record


def _build_sample_text(words: int = 1000) -> str:
    tokens = [f"word{i % 60}" for i in range(words)]
    return " ".join(tokens) + "."


def test_adapt_latency_under_target() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    text = _build_sample_text(1000)

    start = perf_counter()
    adapted = bridge.adapt(text)
    elapsed = perf_counter() - start

    assert adapted
    assert elapsed < 0.2


def test_cache_hit_rate_on_repeated_text() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ANXIETY)
    text = "This is critical. Please respond ASAP. We must complete this immediately."

    for _ in range(10):
        bridge.adapt(text)

    stats = bridge.cache_stats()
    assert stats["hits"] >= 8
    assert stats["hit_rate"] >= 0.8


def test_redis_store_graceful_degradation() -> None:
    store = RedisMemoryStore("redis://localhost:6399/0")
    record = create_feedback_record(
        user_id="u1",
        original_text="Original",
        adapted_text="Adapted",
        user_edit="Edited",
    )

    store.save_feedback(record)
    loaded = store.get_feedback("u1")
    assert len(loaded) == 1
    assert isinstance(loaded[0], FeedbackRecord)


def test_async_chat_parallel_gather() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.DYSLEXIA)

    async def _run() -> list[str]:
        calls = [bridge.achat(f"Message {idx} with a little context.") for idx in range(8)]
        responses = await asyncio.gather(*calls)
        return [resp.adapted_text for resp in responses]

    outputs = asyncio.run(_run())
    assert len(outputs) == 8
    assert all(item.strip() for item in outputs)
