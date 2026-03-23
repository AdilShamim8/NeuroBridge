"""ProfileDetector using a lightweight RandomForest classifier."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from neurobridge.core.profile import Profile
from neurobridge.ml.features import extract_features
from neurobridge.ml.model import load_model, predict_with_confidence


@dataclass(frozen=True)
class ProfileDetectionResult:
    """Output of profile detection from interaction events."""

    profile: str
    confidence: float
    reasoning: str
    fallback_to_quiz: bool


class ProfileDetector:
    """Detect likely cognitive profile from interaction events."""

    def __init__(self, confidence_threshold: float = 0.6) -> None:
        self.confidence_threshold = confidence_threshold
        self._model = None
        self._load_error: Optional[Exception] = None
        self._try_load_model()

    def _try_load_model(self) -> None:
        try:
            self._model = load_model()
        except Exception as exc:
            self._model = None
            self._load_error = exc

    def detect(self, events: List[Dict[str, Any]]) -> ProfileDetectionResult:
        """Detect profile from interaction events with confidence and reasoning."""

        if not events:
            return ProfileDetectionResult(
                profile=Profile.ADHD.value,
                confidence=0.0,
                reasoning="No events available. Falling back to quiz.",
                fallback_to_quiz=True,
            )

        feature_vector = extract_features(events)

        if self._model is None:
            return ProfileDetectionResult(
                profile=Profile.ADHD.value,
                confidence=0.0,
                reasoning="Model unavailable. Falling back to quiz.",
                fallback_to_quiz=True,
            )

        label, confidence, ranked = predict_with_confidence(self._model, feature_vector.values)
        fallback = confidence < self.confidence_threshold

        top_hints = ", ".join([f"{name}:{prob:.2f}" for name, prob in ranked[:3]])
        reasoning = (
            f"Predicted from {len(events)} events using 15 interaction signals. "
            f"Top probabilities: {top_hints}."
        )

        return ProfileDetectionResult(
            profile=label,
            confidence=confidence,
            reasoning=reasoning,
            fallback_to_quiz=fallback,
        )
