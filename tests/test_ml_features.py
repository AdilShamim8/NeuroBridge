"""Tests for ML feature extraction."""

from neurobridge.ml.features import FEATURE_NAMES, extract_features


def test_extract_features_returns_15_signals() -> None:
    events = [
        {
            "event_type": "chunk_dwell",
            "metadata": {"dwell_ms": 800, "scroll_speed": 1.2, "long_word_pause_ms": 120},
        },
        {
            "event_type": "chunk_reread",
            "metadata": {"chunk_index": 0, "is_calming": True},
        },
        {"event_type": "tts_activated", "metadata": {}},
        {"event_type": "feedback_positive", "metadata": {}},
    ]

    vector = extract_features(events)
    assert vector.names == FEATURE_NAMES
    assert len(vector.values) == 15
    assert vector.values[0] == 4.0
    assert vector.values[1] > 0
