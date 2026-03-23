"""Feature extraction from interaction events for profile detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class FeatureVector:
    """Normalized feature vector used by the ML classifier."""

    values: List[float]
    names: List[str]


FEATURE_NAMES = [
    "event_count",
    "avg_chunk_dwell_ms",
    "avg_scroll_speed",
    "chunk_reread_rate",
    "tts_activation_rate",
    "section_skipped_rate",
    "text_copied_rate",
    "feedback_positive_rate",
    "feedback_negative_rate",
    "urgency_section_skip_rate",
    "calming_section_reread_rate",
    "long_word_pause_ms",
    "first_chunk_reread_rate",
    "partial_quiz_signal",
    "edit_distance_rate",
]


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def extract_features(events: Iterable[Dict[str, Any]]) -> FeatureVector:
    """Extract 15 profile-detection signals from interaction events."""

    items = list(events)
    total = float(len(items))

    chunk_dwell_values = [
        float(event.get("metadata", {}).get("dwell_ms", 0.0))
        for event in items
        if event.get("event_type") == "chunk_dwell"
    ]
    scroll_speed_values = [
        float(event.get("metadata", {}).get("scroll_speed", 0.0))
        for event in items
        if event.get("event_type") == "chunk_dwell"
    ]
    long_word_pauses = [
        float(event.get("metadata", {}).get("long_word_pause_ms", 0.0))
        for event in items
        if event.get("event_type") == "chunk_dwell"
    ]

    def count_type(name: str) -> float:
        return float(sum(1 for event in items if event.get("event_type") == name))

    chunk_reread = count_type("chunk_reread")
    tts_activated = count_type("tts_activated")
    section_skipped = count_type("section_skipped")
    text_copied = count_type("text_copied")
    feedback_positive = count_type("feedback_positive")
    feedback_negative = count_type("feedback_negative")

    urgency_skips = float(
        sum(
            1
            for event in items
            if event.get("event_type") == "section_skipped"
            and bool(event.get("metadata", {}).get("contains_urgency", False))
        )
    )
    calming_rereads = float(
        sum(
            1
            for event in items
            if event.get("event_type") == "chunk_reread"
            and bool(event.get("metadata", {}).get("is_calming", False))
        )
    )
    first_chunk_rereads = float(
        sum(
            1
            for event in items
            if event.get("event_type") == "chunk_reread"
            and int(event.get("metadata", {}).get("chunk_index", -1)) == 0
        )
    )

    partial_quiz_signal = float(
        sum(
            1
            for event in items
            if event.get("event_type") == "quiz_partial"
            and bool(event.get("metadata", {}).get("provided", False))
        )
    )

    edit_rate_values = [
        float(event.get("metadata", {}).get("edit_ratio", 0.0))
        for event in items
        if event.get("event_type") == "text_edited"
    ]

    avg_dwell = sum(chunk_dwell_values) / len(chunk_dwell_values) if chunk_dwell_values else 0.0
    avg_scroll_speed = (
        sum(scroll_speed_values) / len(scroll_speed_values) if scroll_speed_values else 0.0
    )
    avg_long_word_pause = sum(long_word_pauses) / len(long_word_pauses) if long_word_pauses else 0.0
    avg_edit_rate = sum(edit_rate_values) / len(edit_rate_values) if edit_rate_values else 0.0

    values = [
        total,
        avg_dwell,
        avg_scroll_speed,
        _safe_div(chunk_reread, total),
        _safe_div(tts_activated, total),
        _safe_div(section_skipped, total),
        _safe_div(text_copied, total),
        _safe_div(feedback_positive, total),
        _safe_div(feedback_negative, total),
        _safe_div(urgency_skips, max(1.0, section_skipped)),
        _safe_div(calming_rereads, max(1.0, chunk_reread)),
        avg_long_word_pause,
        _safe_div(first_chunk_rereads, max(1.0, chunk_reread)),
        _safe_div(partial_quiz_signal, total),
        avg_edit_rate,
    ]

    return FeatureVector(values=values, names=list(FEATURE_NAMES))
