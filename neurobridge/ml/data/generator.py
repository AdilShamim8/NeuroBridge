"""Synthetic training data generator for profile detection."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Dict, List, Tuple

from neurobridge.core.profile import Profile


@dataclass(frozen=True)
class SyntheticSample:
    """Single synthetic sample with features and profile label."""

    features: List[float]
    label: str


def _bounded(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _rand_uniform(rng: random.Random, low: float, high: float) -> float:
    # Synthetic ML training data does not require cryptographic randomness.
    return rng.uniform(low, high)  # nosec B311


def _base_noise(rng: random.Random) -> Dict[str, float]:
    return {
        "event_count": _rand_uniform(rng, 20, 60),
        "avg_chunk_dwell_ms": _rand_uniform(rng, 600, 2600),
        "avg_scroll_speed": _rand_uniform(rng, 0.2, 3.5),
        "chunk_reread_rate": _rand_uniform(rng, 0.02, 0.4),
        "tts_activation_rate": _rand_uniform(rng, 0.0, 0.3),
        "section_skipped_rate": _rand_uniform(rng, 0.02, 0.35),
        "text_copied_rate": _rand_uniform(rng, 0.0, 0.2),
        "feedback_positive_rate": _rand_uniform(rng, 0.0, 0.4),
        "feedback_negative_rate": _rand_uniform(rng, 0.0, 0.25),
        "urgency_section_skip_rate": _rand_uniform(rng, 0.0, 0.6),
        "calming_section_reread_rate": _rand_uniform(rng, 0.0, 0.6),
        "long_word_pause_ms": _rand_uniform(rng, 0, 900),
        "first_chunk_reread_rate": _rand_uniform(rng, 0.0, 0.7),
        "partial_quiz_signal": _rand_uniform(rng, 0.0, 1.0),
        "edit_distance_rate": _rand_uniform(rng, 0.0, 0.6),
    }


def _profile_adjustments(profile: Profile, f: Dict[str, float]) -> Dict[str, float]:
    if profile == Profile.ADHD:
        f["avg_chunk_dwell_ms"] *= 0.55
        f["avg_scroll_speed"] *= 1.8
        f["first_chunk_reread_rate"] = _bounded(f["first_chunk_reread_rate"] + 0.25)
        f["chunk_reread_rate"] = _bounded(f["chunk_reread_rate"] + 0.1)
    elif profile == Profile.DYSLEXIA:
        f["avg_chunk_dwell_ms"] *= 1.45
        f["long_word_pause_ms"] *= 1.8
        f["tts_activation_rate"] = _bounded(f["tts_activation_rate"] + 0.35)
        f["avg_scroll_speed"] *= 0.7
    elif profile == Profile.ANXIETY:
        f["urgency_section_skip_rate"] = _bounded(f["urgency_section_skip_rate"] + 0.35)
        f["calming_section_reread_rate"] = _bounded(f["calming_section_reread_rate"] + 0.25)
        f["feedback_negative_rate"] = _bounded(f["feedback_negative_rate"] + 0.12)
    elif profile == Profile.AUTISM:
        f["chunk_reread_rate"] = _bounded(f["chunk_reread_rate"] + 0.25)
        f["text_copied_rate"] = _bounded(f["text_copied_rate"] + 0.15)
        f["avg_scroll_speed"] *= 0.8
    elif profile == Profile.DYSCALCULIA:
        f["avg_chunk_dwell_ms"] *= 1.2
        f["edit_distance_rate"] = _bounded(f["edit_distance_rate"] + 0.22)
        f["chunk_reread_rate"] = _bounded(f["chunk_reread_rate"] + 0.12)

    return f


def generate_synthetic_samples(per_profile: int = 1000, seed: int = 42) -> List[SyntheticSample]:
    """Generate synthetic profile-labeled training data."""

    rng = random.Random(seed)  # nosec B311
    samples: List[SyntheticSample] = []

    profiles = [
        Profile.ADHD,
        Profile.AUTISM,
        Profile.DYSLEXIA,
        Profile.ANXIETY,
        Profile.DYSCALCULIA,
    ]

    for profile in profiles:
        for _ in range(per_profile):
            feature_map = _profile_adjustments(profile, _base_noise(rng))
            ordered = [
                feature_map["event_count"],
                feature_map["avg_chunk_dwell_ms"],
                feature_map["avg_scroll_speed"],
                feature_map["chunk_reread_rate"],
                feature_map["tts_activation_rate"],
                feature_map["section_skipped_rate"],
                feature_map["text_copied_rate"],
                feature_map["feedback_positive_rate"],
                feature_map["feedback_negative_rate"],
                feature_map["urgency_section_skip_rate"],
                feature_map["calming_section_reread_rate"],
                feature_map["long_word_pause_ms"],
                feature_map["first_chunk_reread_rate"],
                feature_map["partial_quiz_signal"],
                feature_map["edit_distance_rate"],
            ]
            samples.append(SyntheticSample(features=ordered, label=profile.value))

    return samples


def to_training_matrices(samples: List[SyntheticSample]) -> Tuple[List[List[float]], List[str]]:
    """Convert synthetic sample objects to model-training matrices."""

    features = [sample.features for sample in samples]
    labels = [sample.label for sample in samples]
    return features, labels
