"""Memory stores and feedback analysis for adaptive profile learning."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from neurobridge.core.profile import ProfileConfig
from neurobridge.core.validators import sanitize_key_token


@dataclass(slots=True)
class FeedbackRecord:
    """A single user feedback event used for adaptive tuning."""

    user_id: str
    original_hash: str
    adapted_hash: str
    user_edit_hash: str
    timestamp: str
    interaction_id: str
    delta_analysis: Dict[str, Any]


@dataclass(slots=True)
class ProfileAdjustments:
    """Computed profile deltas inferred from user feedback history."""

    chunk_size_delta: int = 0
    max_sentence_words_delta: int = 0
    tone: Optional[str] = None
    reason: str = ""


class BaseMemoryStore(ABC):
    """Abstract memory interface for storing profile state and feedback."""

    @abstractmethod
    def save_profile(self, user_id: str, profile: ProfileConfig) -> None:
        """Persist profile configuration for a user."""

    @abstractmethod
    def load_profile(self, user_id: str) -> Optional[ProfileConfig]:
        """Load profile configuration for a user."""

    @abstractmethod
    def save_feedback(self, record: FeedbackRecord) -> None:
        """Persist adaptation feedback for iterative improvements."""

    @abstractmethod
    def get_feedback(self, user_id: str) -> List[FeedbackRecord]:
        """Return feedback history for a user."""

    @abstractmethod
    def increment_interaction(self, user_id: str) -> int:
        """Increment and return interaction count for a user."""

    @abstractmethod
    def get_interaction_count(self, user_id: str) -> int:
        """Return interaction count for a user."""

    @abstractmethod
    def clear_user_data(self, user_id: str) -> None:
        """Delete all stored data for a user."""


class InMemoryStore(BaseMemoryStore):
    """Simple in-memory store for local development and tests."""

    def __init__(self) -> None:
        self._profiles: Dict[str, ProfileConfig] = {}
        self._feedback: Dict[str, List[FeedbackRecord]] = {}
        self._interactions: Dict[str, int] = {}

    def save_profile(self, user_id: str, profile: ProfileConfig) -> None:
        self._profiles[user_id] = profile

    def load_profile(self, user_id: str) -> Optional[ProfileConfig]:
        return self._profiles.get(user_id)

    def save_feedback(self, record: FeedbackRecord) -> None:
        user_id = record.user_id
        if user_id not in self._feedback:
            self._feedback[user_id] = []
        self._feedback[user_id].append(record)

    def get_feedback(self, user_id: str) -> List[FeedbackRecord]:
        return list(self._feedback.get(user_id, []))

    def increment_interaction(self, user_id: str) -> int:
        self._interactions[user_id] = self._interactions.get(user_id, 0) + 1
        return self._interactions[user_id]

    def get_interaction_count(self, user_id: str) -> int:
        return self._interactions.get(user_id, 0)

    def clear_user_data(self, user_id: str) -> None:
        self._profiles.pop(user_id, None)
        self._feedback.pop(user_id, None)
        self._interactions.pop(user_id, None)


class SQLiteMemoryStore(BaseMemoryStore):
    """SQLite-backed memory store for persistent profile and feedback learning."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        resolved = Path(db_path or "~/.neurobridge/memory.db").expanduser()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = resolved
        self._lock = Lock()
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    interaction_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    original_hash TEXT NOT NULL,
                    adapted_hash TEXT NOT NULL,
                    user_edit_hash TEXT NOT NULL,
                    delta_json TEXT NOT NULL
                )
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    user_id TEXT PRIMARY KEY,
                    count INTEGER NOT NULL
                )
                """)
            self._conn.commit()

    def save_profile(self, user_id: str, profile: ProfileConfig) -> None:
        payload = json.dumps(asdict(profile), ensure_ascii=True)
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO profiles (user_id, profile_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    profile_json=excluded.profile_json,
                    updated_at=excluded.updated_at
                """,
                (user_id, payload, now),
            )
            self._conn.commit()

    def load_profile(self, user_id: str) -> Optional[ProfileConfig]:
        with self._lock:
            cursor = self._conn.execute(
                "SELECT profile_json FROM profiles WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
        if not row:
            return None
        data = json.loads(str(row[0]))
        return ProfileConfig(**data)

    def save_feedback(self, record: FeedbackRecord) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO feedback (
                    user_id,
                    interaction_id,
                    timestamp,
                    original_hash,
                    adapted_hash,
                    user_edit_hash,
                    delta_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.user_id,
                    record.interaction_id,
                    record.timestamp,
                    record.original_hash,
                    record.adapted_hash,
                    record.user_edit_hash,
                    json.dumps(record.delta_analysis, ensure_ascii=True),
                ),
            )
            self._conn.commit()

    def get_feedback(self, user_id: str) -> List[FeedbackRecord]:
        with self._lock:
            cursor = self._conn.execute(
                """
                SELECT user_id, original_hash, adapted_hash, user_edit_hash, timestamp, interaction_id, delta_json
                FROM feedback
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
        records: List[FeedbackRecord] = []
        for row in rows:
            records.append(
                FeedbackRecord(
                    user_id=str(row[0]),
                    original_hash=str(row[1]),
                    adapted_hash=str(row[2]),
                    user_edit_hash=str(row[3]),
                    timestamp=str(row[4]),
                    interaction_id=str(row[5]),
                    delta_analysis=json.loads(str(row[6])),
                )
            )
        return records

    def increment_interaction(self, user_id: str) -> int:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO interactions (user_id, count)
                VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET count = count + 1
                """,
                (user_id,),
            )
            self._conn.commit()
            cursor = self._conn.execute(
                "SELECT count FROM interactions WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
        return int(row[0]) if row else 0

    def get_interaction_count(self, user_id: str) -> int:
        with self._lock:
            cursor = self._conn.execute(
                "SELECT count FROM interactions WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
        return int(row[0]) if row else 0

    def clear_user_data(self, user_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
            self._conn.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
            self._conn.execute("DELETE FROM interactions WHERE user_id = ?", (user_id,))
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()


class RedisMemoryStore(BaseMemoryStore):
    """Redis-backed memory store with graceful fallback to in-memory reads."""

    PROFILE_TTL_SECONDS = 90 * 24 * 60 * 60

    def __init__(self, redis_url: str, fallback_store: Optional[InMemoryStore] = None) -> None:
        self._fallback = fallback_store or InMemoryStore()
        self._redis = None
        self._pool = None
        try:
            import redis  # type: ignore

            self._pool = redis.ConnectionPool.from_url(redis_url, decode_responses=True)
            self._redis = redis.Redis(connection_pool=self._pool)
            self._redis.ping()
        except Exception:
            self._redis = None

    @staticmethod
    def _profile_key(user_id: str) -> str:
        return f"nb:profile:{sanitize_key_token(user_id)}"

    @staticmethod
    def _feedback_key(user_id: str, interaction_id: str) -> str:
        return f"nb:feedback:{sanitize_key_token(user_id)}:{sanitize_key_token(interaction_id)}"

    @staticmethod
    def _feedback_index_key(user_id: str) -> str:
        return f"nb:feedback_index:{sanitize_key_token(user_id)}"

    @staticmethod
    def _interaction_key(user_id: str) -> str:
        return f"nb:interactions:{sanitize_key_token(user_id)}"

    def _write_fallback_profile(self, user_id: str, profile: ProfileConfig) -> None:
        self._fallback.save_profile(user_id, profile)

    def save_profile(self, user_id: str, profile: ProfileConfig) -> None:
        self._write_fallback_profile(user_id, profile)
        if self._redis is None:
            return
        payload = json.dumps(asdict(profile), ensure_ascii=True)
        try:
            pipe = self._redis.pipeline(transaction=True)
            pipe.set(self._profile_key(user_id), payload, ex=self.PROFILE_TTL_SECONDS)
            pipe.execute()
        except Exception:
            return

    def load_profile(self, user_id: str) -> Optional[ProfileConfig]:
        if self._redis is None:
            return self._fallback.load_profile(user_id)
        try:
            value = self._redis.get(self._profile_key(user_id))
            if not value:
                return self._fallback.load_profile(user_id)
            return ProfileConfig(**json.loads(value))
        except Exception:
            return self._fallback.load_profile(user_id)

    def save_feedback(self, record: FeedbackRecord) -> None:
        self._fallback.save_feedback(record)
        if self._redis is None:
            return
        try:
            payload = json.dumps(asdict(record), ensure_ascii=True)
            feedback_key = self._feedback_key(record.user_id, record.interaction_id)
            index_key = self._feedback_index_key(record.user_id)
            pipe = self._redis.pipeline(transaction=True)
            pipe.set(feedback_key, payload)
            pipe.rpush(index_key, record.interaction_id)
            pipe.execute()
        except Exception:
            return

    def get_feedback(self, user_id: str) -> List[FeedbackRecord]:
        if self._redis is None:
            return self._fallback.get_feedback(user_id)

        try:
            index_key = self._feedback_index_key(user_id)
            interaction_ids = self._redis.lrange(index_key, 0, -1) or []
            if not interaction_ids:
                return self._fallback.get_feedback(user_id)

            pipe = self._redis.pipeline(transaction=False)
            for interaction_id in interaction_ids:
                pipe.get(self._feedback_key(user_id, interaction_id))
            raw_values = pipe.execute()

            records: List[FeedbackRecord] = []
            for raw in raw_values:
                if not raw:
                    continue
                data = json.loads(raw)
                records.append(FeedbackRecord(**data))
            return records or self._fallback.get_feedback(user_id)
        except Exception:
            return self._fallback.get_feedback(user_id)

    def increment_interaction(self, user_id: str) -> int:
        fallback_count = self._fallback.increment_interaction(user_id)
        if self._redis is None:
            return fallback_count
        try:
            value = self._redis.incr(self._interaction_key(user_id))
            return int(value)
        except Exception:
            return fallback_count

    def get_interaction_count(self, user_id: str) -> int:
        if self._redis is None:
            return self._fallback.get_interaction_count(user_id)
        try:
            value = self._redis.get(self._interaction_key(user_id))
            if value is None:
                return self._fallback.get_interaction_count(user_id)
            return int(value)
        except Exception:
            return self._fallback.get_interaction_count(user_id)

    def clear_user_data(self, user_id: str) -> None:
        self._fallback.clear_user_data(user_id)
        if self._redis is None:
            return
        try:
            interaction_ids = self._redis.lrange(self._feedback_index_key(user_id), 0, -1) or []
            keys = [
                self._profile_key(user_id),
                self._feedback_index_key(user_id),
                self._interaction_key(user_id),
            ]
            keys.extend(
                self._feedback_key(user_id, interaction_id) for interaction_id in interaction_ids
            )
            if keys:
                self._redis.delete(*keys)
        except Exception:
            return

    def close(self) -> None:
        if self._pool is None:
            return
        try:
            self._pool.disconnect()
        except Exception:
            return


class FeedbackAnalyser:
    """Analyse feedback deltas and propose profile adjustments."""

    def analyse_feedback(self, user_id: str, store: BaseMemoryStore) -> ProfileAdjustments:
        records = store.get_feedback(user_id)
        if not records:
            return ProfileAdjustments(reason="No feedback records available.")

        total_length_ratio = 0.0
        simplification_votes = 0
        calm_votes = 0
        samples = 0
        for record in records[-20:]:
            delta = record.delta_analysis
            if not delta:
                continue
            samples += 1
            total_length_ratio += float(delta.get("length_ratio", 1.0))
            if float(delta.get("word_delta", 0)) < -5:
                simplification_votes += 1
            if float(delta.get("urgency_delta", 0)) < 0:
                calm_votes += 1

        if samples == 0:
            return ProfileAdjustments(reason="Feedback records contained no analysable deltas.")

        avg_ratio = total_length_ratio / samples
        chunk_delta = 0
        sentence_delta = 0
        tone = None
        reason_parts: List[str] = []

        if avg_ratio < 0.9 or simplification_votes >= max(2, samples // 3):
            chunk_delta = -1
            sentence_delta = -2
            reason_parts.append(
                "Users consistently shorten outputs, suggesting simpler formatting."
            )
        elif avg_ratio > 1.1:
            chunk_delta = 1
            sentence_delta = 1
            reason_parts.append("Users tend to expand outputs, suggesting more detail is helpful.")

        if calm_votes >= max(2, samples // 3):
            tone = "calm"
            reason_parts.append("Feedback indicates preference for calmer phrasing.")

        return ProfileAdjustments(
            chunk_size_delta=chunk_delta,
            max_sentence_words_delta=sentence_delta,
            tone=tone,
            reason=" ".join(reason_parts) or "No strong adjustment signal detected.",
        )


def create_feedback_record(
    user_id: str,
    original_text: str,
    adapted_text: str,
    user_edit: str,
) -> FeedbackRecord:
    """Create a FeedbackRecord with computed text-delta statistics."""
    original_words = max(1, len(original_text.split()))
    adapted_words = max(1, len(adapted_text.split()))
    edited_words = max(1, len(user_edit.split()))

    urgency_terms = ("urgent", "asap", "immediately", "critical", "must")
    adapted_urgency = sum(adapted_text.lower().count(token) for token in urgency_terms)
    edited_urgency = sum(user_edit.lower().count(token) for token in urgency_terms)

    delta_analysis: Dict[str, Any] = {
        "word_delta": edited_words - adapted_words,
        "length_ratio": edited_words / adapted_words,
        "original_to_adapted_ratio": adapted_words / original_words,
        "urgency_delta": edited_urgency - adapted_urgency,
    }

    original_hash = hashlib.sha256(original_text.encode("utf-8")).hexdigest()
    adapted_hash = hashlib.sha256(adapted_text.encode("utf-8")).hexdigest()
    user_edit_hash = hashlib.sha256(user_edit.encode("utf-8")).hexdigest()

    return FeedbackRecord(
        user_id=user_id,
        original_hash=original_hash,
        adapted_hash=adapted_hash,
        user_edit_hash=user_edit_hash,
        timestamp=datetime.now(timezone.utc).isoformat(),
        interaction_id=str(uuid4()),
        delta_analysis=delta_analysis,
    )


MemoryStore = BaseMemoryStore
