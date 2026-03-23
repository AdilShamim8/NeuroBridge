"""Tests for profile detector behavior."""

from neurobridge.ml.detector import ProfileDetector


def test_detector_falls_back_with_no_events() -> None:
    detector = ProfileDetector()
    result = detector.detect([])
    assert result.fallback_to_quiz is True
    assert result.confidence == 0.0


def test_detector_returns_reasoning_for_minimal_events() -> None:
    detector = ProfileDetector()
    events = [
        {"event_type": "chunk_dwell", "metadata": {"dwell_ms": 650, "scroll_speed": 2.8}},
        {"event_type": "chunk_reread", "metadata": {"chunk_index": 0, "is_calming": False}},
        {"event_type": "section_skipped", "metadata": {"contains_urgency": True}},
        {"event_type": "text_edited", "metadata": {"edit_ratio": 0.22}},
    ]
    result = detector.detect(events)
    assert isinstance(result.profile, str)
    assert "Top probabilities" in result.reasoning or "Falling back to quiz" in result.reasoning


def test_detector_falls_back_when_model_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "neurobridge.ml.detector.load_model", lambda: (_ for _ in ()).throw(RuntimeError("missing"))
    )
    detector = ProfileDetector()

    events = [{"event_type": "chunk_dwell", "metadata": {"dwell_ms": 400, "scroll_speed": 1.3}}]
    result = detector.detect(events)

    assert result.fallback_to_quiz is True
    assert result.confidence == 0.0
    assert "Model unavailable" in result.reasoning
