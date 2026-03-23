"""Central validation helpers for security and privacy constraints."""

from __future__ import annotations

import re
from typing import Iterable

MAX_TEXT_LENGTH_DEFAULT = 50_000
MAX_USER_ID_LENGTH = 128
USER_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

_ALLOWED_PROFILES = {"adhd", "autism", "dyslexia", "anxiety", "dyscalculia", "custom"}


def validate_text_input(
    text: str, *, max_length: int = MAX_TEXT_LENGTH_DEFAULT, field: str = "text"
) -> str:
    if not isinstance(text, str):
        raise TypeError(f"{field} must be a string")
    if len(text) > max_length:
        raise ValueError(f"{field} exceeds maximum length of {max_length} characters")
    return text


def validate_user_id(user_id: str) -> str:
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string")
    if not user_id.strip():
        raise ValueError("user_id must be non-empty")
    if len(user_id) > MAX_USER_ID_LENGTH:
        raise ValueError(f"user_id exceeds max length of {MAX_USER_ID_LENGTH}")
    if not USER_ID_RE.fullmatch(user_id):
        raise ValueError("user_id may contain only letters, numbers, dash, and underscore")
    return user_id


def validate_profile_name(profile_name: str) -> str:
    if not isinstance(profile_name, str):
        raise TypeError("profile must be a string")
    normalized = profile_name.strip().lower()
    if normalized not in _ALLOWED_PROFILES:
        raise ValueError(f"Unsupported profile: {profile_name}")
    return normalized


def validate_profile_config_ranges(
    *,
    chunk_size: int,
    reading_level: int,
    max_sentence_words: int,
) -> None:
    if not 1 <= chunk_size <= 20:
        raise ValueError("chunk_size must be between 1 and 20")
    if not 1 <= reading_level <= 12:
        raise ValueError("reading_level must be between 1 and 12")
    if not 5 <= max_sentence_words <= 40:
        raise ValueError("max_sentence_words must be between 5 and 40")


def sanitize_key_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_-]", "_", value)
    return token[:MAX_USER_ID_LENGTH]


def contains_any_token(text: str, tokens: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens)
