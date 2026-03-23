"""Interaction tracking for profile detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from neurobridge.core.bridge import NeuroBridge
from neurobridge.core.profile import Profile
from neurobridge.ml.detector import ProfileDetectionResult, ProfileDetector

_ALLOWED_EVENT_TYPES = {
    "chunk_dwell",
    "chunk_reread",
    "tts_activated",
    "section_skipped",
    "text_copied",
    "feedback_positive",
    "feedback_negative",
    "quiz_partial",
    "text_edited",
}


@dataclass(frozen=True)
class InteractionEvent:
    """Single recorded interaction event."""

    user_id: str
    event_type: str
    metadata: Dict[str, Any]
    timestamp: str


@dataclass
class InteractionTracker:
    """Track interaction signals and auto-trigger profile detection."""

    bridge: NeuroBridge
    detector: ProfileDetector = field(default_factory=ProfileDetector)
    detect_after_events: int = 20
    update_threshold: float = 0.7
    _events_by_user: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    def record(
        self,
        user_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ProfileDetectionResult]:
        """Record event and trigger profile update when threshold is reached."""

        if event_type not in _ALLOWED_EVENT_TYPES:
            raise ValueError(f"Unsupported event_type: {event_type}")

        event = InteractionEvent(
            user_id=user_id,
            event_type=event_type,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        events = self._load_events(user_id)
        events.append(
            {
                "event_type": event.event_type,
                "metadata": dict(event.metadata),
                "timestamp": event.timestamp,
            }
        )
        self._save_events(user_id, events)

        if len(events) < self.detect_after_events:
            return None

        result = self.detector.detect(events)
        if not result.fallback_to_quiz and result.confidence >= self.update_threshold:
            self._set_profile_from_label(result.profile)
            if self.bridge.memory_store is not None:
                self.bridge.memory_store.save_profile(
                    user_id, self.bridge._profile_config
                )  # noqa: SLF001

        return result

    def _set_profile_from_label(self, label: str) -> None:
        try:
            profile = Profile(label)
        except ValueError:
            return
        self.bridge.set_profile(profile)

    def _load_events(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self._events_by_user.get(user_id, []))

    def _save_events(self, user_id: str, events: List[Dict[str, Any]]) -> None:
        self._events_by_user[user_id] = list(events)

        if self.bridge.memory_store is None:
            return
        key = f"_events:{user_id}"
        store = self.bridge.memory_store
        data = getattr(store, "_interaction_cache", None)
        if not isinstance(data, dict):
            data = {}
            setattr(store, "_interaction_cache", data)
        data[key] = list(events)
