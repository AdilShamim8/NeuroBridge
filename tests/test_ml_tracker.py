"""Tests for interaction tracker auto-detection behavior."""

from neurobridge import Config, NeuroBridge
from neurobridge.ml.detector import ProfileDetectionResult
from neurobridge.ml.tracker import InteractionTracker


class _StubDetector:
    def detect(self, events):
        _ = events
        return ProfileDetectionResult(
            profile="anxiety",
            confidence=0.92,
            reasoning="stub",
            fallback_to_quiz=False,
        )


class _LowConfidenceDetector:
    def detect(self, events):
        _ = events
        return ProfileDetectionResult(
            profile="anxiety",
            confidence=0.4,
            reasoning="low confidence",
            fallback_to_quiz=False,
        )


def test_tracker_records_and_triggers_after_threshold() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    tracker = InteractionTracker(bridge=bridge, detector=_StubDetector(), detect_after_events=3)

    assert tracker.record("u1", "chunk_dwell", {"dwell_ms": 300, "scroll_speed": 2.0}) is None
    assert tracker.record("u1", "chunk_reread", {"chunk_index": 0}) is None
    result = tracker.record("u1", "feedback_positive", {})

    assert result is not None
    assert result.profile == "anxiety"


def test_tracker_rejects_unknown_event_type() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    tracker = InteractionTracker(bridge=bridge, detector=_StubDetector(), detect_after_events=3)
    try:
        tracker.record("u1", "unknown_event", {})
        assert False, "Expected ValueError for unsupported event_type"
    except ValueError:
        assert True


def test_tracker_does_not_update_profile_when_confidence_is_low() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    tracker = InteractionTracker(
        bridge=bridge,
        detector=_LowConfidenceDetector(),
        detect_after_events=2,
        update_threshold=0.7,
    )

    original_profile = bridge.profile
    tracker.record("u2", "chunk_dwell", {"dwell_ms": 420, "scroll_speed": 1.1})
    result = tracker.record("u2", "chunk_reread", {"chunk_index": 1})

    assert result is not None
    assert bridge.profile == original_profile


def test_tracker_set_profile_ignores_invalid_label() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    tracker = InteractionTracker(bridge=bridge, detector=_StubDetector(), detect_after_events=1)

    original_profile = bridge.profile
    tracker._set_profile_from_label("not-a-profile")  # noqa: SLF001

    assert bridge.profile == original_profile


def test_tracker_saves_interaction_cache_on_memory_store() -> None:
    class _Store:
        def save_profile(self, user_id, profile):
            _ = (user_id, profile)

    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge._memory_store = _Store()  # type: ignore[assignment]  # noqa: SLF001
    tracker = InteractionTracker(bridge=bridge, detector=_StubDetector(), detect_after_events=99)

    tracker.record("u3", "feedback_positive", {})

    assert hasattr(bridge.memory_store, "_interaction_cache")
    cache = getattr(bridge.memory_store, "_interaction_cache")
    assert "_events:u3" in cache
    assert len(cache["_events:u3"]) == 1
