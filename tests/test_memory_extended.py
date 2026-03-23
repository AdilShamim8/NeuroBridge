"""Additional Day 22 memory-store tests for redis fallback and analyser branches."""

from __future__ import annotations

from neurobridge.core.memory import (
    FeedbackAnalyser,
    InMemoryStore,
    RedisMemoryStore,
    create_feedback_record,
)
from neurobridge.core.profile import Profile, get_profile_config


def test_redis_store_fallback_paths_without_redis() -> None:
    store = RedisMemoryStore("redis://localhost:1")
    profile = get_profile_config(Profile.ADHD)
    store.save_profile("u-fallback", profile)

    loaded = store.load_profile("u-fallback")
    assert loaded is not None
    assert loaded.chunk_size == profile.chunk_size

    record = create_feedback_record(
        user_id="u-fallback",
        original_text="This is critical.",
        adapted_text="This is important.",
        user_edit="This is important and calm.",
    )
    store.save_feedback(record)
    history = store.get_feedback("u-fallback")
    assert history

    count = store.increment_interaction("u-fallback")
    assert count == 1
    assert store.get_interaction_count("u-fallback") == 1

    store.clear_user_data("u-fallback")
    assert store.load_profile("u-fallback") is None


def test_feedback_analyser_no_records_and_no_deltas() -> None:
    analyser = FeedbackAnalyser()
    store = InMemoryStore()

    none_result = analyser.analyse_feedback("missing", store)
    assert "No feedback records" in none_result.reason

    record = create_feedback_record("u1", "a", "a", "a")
    record.delta_analysis = {}
    store.save_feedback(record)
    empty_result = analyser.analyse_feedback("u1", store)
    assert "no analysable deltas" in empty_result.reason.lower()


def test_feedback_analyser_detects_expansion_signal() -> None:
    analyser = FeedbackAnalyser()
    store = InMemoryStore()

    for index in range(6):
        record = create_feedback_record(
            user_id="u2",
            original_text=f"short {index}",
            adapted_text="compact output",
            user_edit="compact output with more detail and explanation",
        )
        store.save_feedback(record)

    result = analyser.analyse_feedback("u2", store)
    assert result.chunk_size_delta >= 0
    assert "detail" in result.reason.lower() or "expand" in result.reason.lower()
