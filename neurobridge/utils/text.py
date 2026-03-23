"""Text utility helpers used by adaptation modules."""

from __future__ import annotations

import re
from typing import Iterable

_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace while preserving newlines."""
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(lines).strip()


def count_words(text: str) -> int:
    """Count words in unicode-aware text."""
    return len(_WORD_RE.findall(text))


def safe_join(parts: Iterable[str], sep: str = "\n") -> str:
    """Join non-empty string parts with a separator."""
    return sep.join(part for part in parts if part)
