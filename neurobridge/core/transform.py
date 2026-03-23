"""Transform pipeline and core Day 2 text adaptation modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from bisect import bisect_left
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from functools import lru_cache
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Any, Callable, Dict, List, Optional, Sequence
import warnings

from neurobridge.exceptions import TransformError

try:
    from nltk.tokenize import sent_tokenize as _nltk_sent_tokenize
except ImportError:  # pragma: no cover - exercised only without nltk installed
    _nltk_sent_tokenize = None

from neurobridge.core.profile import DEFAULT_PROFILE_CONFIGS, Profile, ProfileConfig

_FENCED_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_NUMBERED_LIST_BLOCK_RE = re.compile(r"(?:^|\n)(?:\s*\d+\.\s.+(?:\n|$))+", re.MULTILINE)
_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
_CONJUNCTION_DELIMITERS: Sequence[str] = (", and", ", but", ", which", ", that")
_SENTENCE_FALLBACK_RE = re.compile(r"[^.!?]+[.!?]?", re.UNICODE)
_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load_json_data(file_name: str, default: object) -> Any:
    file_path = _DATA_DIR / file_name
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


_URGENCY_WORDS = [
    str(word).strip().lower()
    for word in _load_json_data("urgency_words.json", [])
    if str(word).strip()
]
_IDIOMS_DICTIONARY = {
    str(key): str(value)
    for key, value in dict(_load_json_data("idioms.json", {})).items()
    if str(key).strip() and str(value).strip()
}
_IDIOM_RE = (
    re.compile(
        r"\b("
        + "|".join(re.escape(key) for key in sorted(_IDIOMS_DICTIONARY, key=len, reverse=True))
        + r")\b",
        re.IGNORECASE,
    )
    if _IDIOMS_DICTIONARY
    else re.compile(r"^$", re.IGNORECASE)
)

_FILLER_REPLACEMENTS: Dict[re.Pattern[str], str] = {
    re.compile(r"\bIt is worth noting that\b", re.IGNORECASE): "",
    re.compile(r"\bAs you may know\b", re.IGNORECASE): "",
    re.compile(r"\bIt goes without saying\b", re.IGNORECASE): "",
    re.compile(r"\bNeedless to say\b", re.IGNORECASE): "",
    re.compile(r"\bTo be honest\b", re.IGNORECASE): "",
    re.compile(r"\bAt the end of the day\b", re.IGNORECASE): "",
}

_ANXIETY_REPLACEMENTS: Dict[re.Pattern[str], str] = {
    re.compile(r"\bASAP\b", re.IGNORECASE): "when you have time",
    re.compile(r"\bimmediately\b", re.IGNORECASE): "when ready",
    re.compile(r"\bcritical\b", re.IGNORECASE): "important",
    re.compile(r"\burgent\b", re.IGNORECASE): "worth noting",
    re.compile(r"\bmust\b", re.IGNORECASE): "consider",
    re.compile(r"\bdeadline\b", re.IGNORECASE): "target date",
    re.compile(r"\bfailure\b", re.IGNORECASE): "setback",
    re.compile(r"\bproblem\b", re.IGNORECASE): "situation",
    re.compile(r"\berror\b", re.IGNORECASE): "issue to address",
}

_CATASTROPHIC_REPLACEMENTS: Dict[re.Pattern[str], str] = {
    re.compile(r"\bthis will break\b", re.IGNORECASE): "this might need attention",
    re.compile(r"\byou must fix\b", re.IGNORECASE): "it is worth looking at",
    re.compile(r"\bthis is wrong\b", re.IGNORECASE): "this could be improved",
}

_VAGUE_QUALIFIER_REPLACEMENTS: Dict[re.Pattern[str], str] = {
    re.compile(r"\bsome\b", re.IGNORECASE): "a few",
    re.compile(r"\bmany\b", re.IGNORECASE): "several",
    re.compile(r"\bsoon\b", re.IGNORECASE): "within a clear timeframe",
    re.compile(r"\blater\b", re.IGNORECASE): "at a later time",
    re.compile(r"\ba lot\b", re.IGNORECASE): "many",
}

_SARCASM_REPLACEMENTS: Dict[re.Pattern[str], str] = {
    re.compile(r"\bOh great\b", re.IGNORECASE): "This is difficult",
    re.compile(r"\bJust what I needed\b", re.IGNORECASE): "This is not ideal",
    re.compile(r"\bWonderful\b", re.IGNORECASE): "Not ideal",
}

_NEGATIVE_WORDS_RE = re.compile(
    r"\b(concern|risk|issue|problem|setback|error|fail|failure|difficult|hard|complicated)\b",
    re.IGNORECASE,
)
_CAPS_WORD_RE = re.compile(r"\b[A-Z]{3,}\b")
_EXCLAMATION_RE = re.compile(r"!+")
_NEGATIVE_EMOTION_RE = re.compile(
    r"\b(critical|panic|danger|catastrophic|severe|failure|broken|wrong)\b", re.IGNORECASE
)
_IMPERATIVE_START_RE = re.compile(
    r"^\s*(fix|do|send|finish|complete|respond|submit|update|review|act|resolve)\b",
    re.IGNORECASE,
)
_URGENCY_WORD_RE = (
    re.compile(
        r"\b("
        + "|".join(re.escape(word) for word in sorted(set(_URGENCY_WORDS), key=len, reverse=True))
        + r")\b",
        re.IGNORECASE,
    )
    if _URGENCY_WORDS
    else re.compile(r"^$", re.IGNORECASE)
)

_PERCENT_RE = re.compile(r"(?<!\w)(\d+(?:\.\d+)?)%(?!\w)")
_CURRENCY_RE = re.compile(
    r"(?<!\w)([$£€]\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|m|b|million|billion|trillion))?)(?!\w)",
    re.IGNORECASE,
)
_LARGE_NUMBER_RE = re.compile(
    r"(?<!\()\b(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?\s?(?:million|billion|trillion))\b",
    re.IGNORECASE,
)
_SMALL_DECIMAL_RE = re.compile(r"(?<!\w)(0\.\d+)(?!\w)")
_DURATION_RANGE_RE = re.compile(
    r"(?<!\w)(\d+)\s*-\s*(\d+)\s*(years?|months?|weeks?|days?)(?!\w)", re.IGNORECASE
)
_DATA_SIZE_RE = re.compile(r"(?<!\w)(\d+(?:\.\d+)?)\s*(mb|gb|tb)(?!\w)", re.IGNORECASE)
_NUMBER_TOKEN_RE = re.compile(r"\d")

_CONCLUSION_HINTS: Sequence[str] = (
    "therefore",
    "in summary",
    "the result is",
    "this means",
    "ultimately",
    "the answer is",
)
_EXAMPLE_HINTS: Sequence[str] = ("for example", "such as", "consider", "for instance")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")

_DOLLAR_CONTEXTS: Sequence[tuple[float, str]] = (
    (50, "roughly the cost of a weekly grocery run"),
    (200, "roughly the cost of a utility bill"),
    (1000, "roughly the cost of a budget laptop"),
    (10000, "roughly the cost of a used car"),
    (100000, "roughly the cost of a house deposit"),
    (1000000, "roughly the annual salary of 20 average workers"),
    (10000000, "roughly the annual salary of 200 average workers"),
    (100000000, "roughly the budget of a small city department"),
)
_DOLLAR_THRESHOLDS = [threshold for threshold, _ in _DOLLAR_CONTEXTS]
_DOLLAR_DESCRIPTIONS = [description for _, description in _DOLLAR_CONTEXTS]
_PEOPLE_CONTEXTS: Sequence[tuple[float, str]] = (
    (1000, "about the size of a small school"),
    (10000, "about the size of a town neighborhood"),
    (100000, "about the size of a medium town"),
    (1000000, "about the population of a large city district"),
    (5000000, "about the population of a large metro area"),
    (10000000, "about the population of a major world city"),
)
_PEOPLE_THRESHOLDS = [threshold for threshold, _ in _PEOPLE_CONTEXTS]
_PEOPLE_DESCRIPTIONS = [description for _, description in _PEOPLE_CONTEXTS]
_TIME_CONTEXTS: Dict[str, str] = {
    "days": "a short planning cycle",
    "weeks": "a typical project sprint",
    "months": "a full quarter of work",
    "years": "a long-term planning window",
}
_DATA_CONTEXTS: Dict[str, str] = {
    "mb": "roughly a few high-resolution photos",
    "gb": "roughly a short HD video",
    "tb": "roughly a large enterprise backup",
}


def _safe_sent_tokenize(text: str) -> List[str]:
    """Tokenize sentences using NLTK with a regex fallback if punkt is unavailable."""
    if not text.strip():
        return []
    if _nltk_sent_tokenize is None:
        return [
            segment.strip() for segment in _SENTENCE_FALLBACK_RE.findall(text) if segment.strip()
        ]
    try:
        return [segment.strip() for segment in _nltk_sent_tokenize(text) if segment.strip()]
    except LookupError:
        return [
            segment.strip() for segment in _SENTENCE_FALLBACK_RE.findall(text) if segment.strip()
        ]


def _sentence_word_count(sentence: str) -> int:
    return len(_WORD_RE.findall(sentence))


def _detect_profile(profile: ProfileConfig) -> Optional[Profile]:
    """Best-effort detection for built-in profile-specific transforms."""
    for name, config in DEFAULT_PROFILE_CONFIGS.items():
        if profile == config:
            return name
    return None


def _protect_regions(text: str) -> List[tuple[str, bool]]:
    """Split text into transformable and protected regions.

    Protected regions include fenced code blocks and numbered list blocks.
    """
    protected_spans: List[tuple[int, int]] = []
    for pattern in (_FENCED_BLOCK_RE, _NUMBERED_LIST_BLOCK_RE):
        for match in pattern.finditer(text):
            protected_spans.append((match.start(), match.end()))

    if not protected_spans:
        return [(text, False)]

    protected_spans.sort()
    merged: List[tuple[int, int]] = []
    for start, end in protected_spans:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))

    segments: List[tuple[str, bool]] = []
    cursor = 0
    for start, end in merged:
        if start > cursor:
            segments.append((text[cursor:start], False))
        segments.append((text[start:end], True))
        cursor = end
    if cursor < len(text):
        segments.append((text[cursor:], False))
    return segments


def _chunk_sentences(sentences: Sequence[str], chunk_size: int) -> List[str]:
    if chunk_size <= 0:
        chunk_size = 1
    chunks: List[str] = []
    for index in range(0, len(sentences), chunk_size):
        chunks.append(" ".join(sentences[index : index + chunk_size]).strip())
    return [chunk for chunk in chunks if chunk]


def _bold_anchor_words(chunk: str, word_count: int = 5) -> str:
    """Bold the first 4-6 words (default 5) to create an attention anchor."""
    words = chunk.split()
    if not words:
        return chunk
    anchor_count = min(max(4, word_count), 6, len(words))
    anchored = " ".join(words[:anchor_count])
    remainder = " ".join(words[anchor_count:])
    if remainder:
        return f"**{anchored}** {remainder}"
    return f"**{anchored}**"


class BaseTransformModule(ABC):
    """Base class for transform modules in the adaptation pipeline."""

    name: str = "base"

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    @abstractmethod
    def apply(self, text: str, profile: ProfileConfig) -> str:
        """Apply a transformation and return transformed text."""


class Chunker(BaseTransformModule):
    """Split text into readable sentence chunks without touching protected markdown regions."""

    name = "chunker"

    def apply(self, text: str, profile: ProfileConfig) -> str:
        if not text.strip():
            return ""

        detected = _detect_profile(profile)
        chunk_size = max(1, profile.chunk_size)
        separator = "\n\n"
        if detected == Profile.DYSLEXIA:
            chunk_size = min(chunk_size, 3)
            separator = "\n\n\n"

        output_regions: List[str] = []
        for region, is_protected in _protect_regions(text):
            if is_protected:
                output_regions.append(region)
                continue

            sentences = _safe_sent_tokenize(region)
            if not sentences:
                output_regions.append(region)
                continue

            chunks = _chunk_sentences(sentences, chunk_size)
            if detected == Profile.ADHD:
                chunks = [_bold_anchor_words(chunk) for chunk in chunks]
            output_regions.append(separator.join(chunks))

        return "".join(output_regions).strip()


class SentenceSimplifier(BaseTransformModule):
    """Split long sentences at natural clause boundaries."""

    name = "sentence_simplifier"

    def apply(self, text: str, profile: ProfileConfig) -> str:
        if not text.strip():
            return ""

        transformed_regions: List[str] = []
        for region, is_protected in _protect_regions(text):
            if is_protected:
                transformed_regions.append(region)
                continue

            sentences = _safe_sent_tokenize(region)
            if not sentences:
                transformed_regions.append(region)
                continue

            rebuilt: List[str] = []
            for sentence in sentences:
                rebuilt.extend(self._simplify_sentence(sentence, profile.max_sentence_words))
            transformed_regions.append(" ".join(part for part in rebuilt if part))

        return "".join(transformed_regions).strip()

    def _simplify_sentence(self, sentence: str, max_words: int) -> List[str]:
        if _sentence_word_count(sentence) <= max_words:
            return [sentence]

        pending = [sentence]
        result: List[str] = []
        iterations = 0
        while pending and iterations < 8:
            current = pending.pop(0).strip()
            iterations += 1
            if _sentence_word_count(current) <= max_words:
                result.append(current)
                continue

            split_parts = self._split_once(current)
            if len(split_parts) == 1:
                result.append(current)
                continue

            pending = split_parts + pending

        if pending:
            result.extend(pending)
        return result

    def _split_once(self, sentence: str) -> List[str]:
        for delimiter in _CONJUNCTION_DELIMITERS:
            parts = self._split_by_delimiter(sentence, delimiter)
            if parts:
                return parts

        if ";" in sentence:
            left, right = sentence.split(";", 1)
            left_part = self._ensure_terminal_punctuation(left.strip())
            right_part = self._normalize_sentence_start(right.strip())
            if left_part and right_part:
                return [left_part, right_part]
        return [sentence]

    def _split_by_delimiter(self, sentence: str, delimiter: str) -> Optional[List[str]]:
        lower = sentence.lower()
        position = lower.find(delimiter)
        if position == -1:
            return None

        left = sentence[:position].strip()
        right = sentence[position + len(delimiter) :].strip()
        if not left or not right:
            return None

        conjunction = delimiter.replace(",", "").strip()
        right = f"{conjunction} {right}" if not right.lower().startswith(conjunction) else right

        left_part = self._ensure_terminal_punctuation(left)
        right_part = self._normalize_sentence_start(right)
        if not left_part or not right_part:
            return None
        return [left_part, right_part]

    @staticmethod
    def _ensure_terminal_punctuation(text: str) -> str:
        if not text:
            return text
        if text[-1] in ".!?":
            return text
        return f"{text}."

    @staticmethod
    def _normalize_sentence_start(text: str) -> str:
        if not text:
            return text
        return text[0].upper() + text[1:]


class ToneRewriter(BaseTransformModule):
    """Rewrite tone for anxiety/autism needs and remove filler phrases globally."""

    name = "tone_rewriter"

    def apply(self, text: str, profile: ProfileConfig) -> str:
        if not text.strip():
            return ""

        detected = _detect_profile(profile)
        transformed_regions: List[str] = []
        for region, is_protected in _protect_regions(text):
            if is_protected:
                transformed_regions.append(region)
                continue

            updated = self._strip_fillers(region)
            if detected == Profile.ANXIETY:
                updated = self._rewrite_anxiety(updated)
            elif detected == Profile.AUTISM:
                updated = self._rewrite_autism(updated)

            transformed_regions.append(updated)

        return "".join(transformed_regions).strip()

    def _strip_fillers(self, text: str) -> str:
        updated = text
        for pattern, replacement in _FILLER_REPLACEMENTS.items():
            updated = pattern.sub(replacement, updated)
        return re.sub(r"\s{2,}", " ", updated)

    def _rewrite_anxiety(self, text: str) -> str:
        updated = text
        for pattern, replacement in _ANXIETY_REPLACEMENTS.items():
            updated = pattern.sub(replacement, updated)
        for pattern, replacement in _CATASTROPHIC_REPLACEMENTS.items():
            updated = pattern.sub(replacement, updated)

        paragraphs = updated.split("\n\n")
        rewritten: List[str] = []
        for index, paragraph in enumerate(paragraphs):
            clean = paragraph.strip()
            if not clean:
                rewritten.append(paragraph)
                continue
            if _NEGATIVE_WORDS_RE.search(clean):
                prefix = "Here is some context: " if index % 2 == 0 else "Good news first - "
                rewritten.append(prefix + clean)
            else:
                rewritten.append(paragraph)
        return "\n\n".join(rewritten)

    def _rewrite_autism(self, text: str) -> str:
        updated = text
        if _IDIOMS_DICTIONARY:
            updated = _IDIOM_RE.sub(
                lambda match: _IDIOMS_DICTIONARY.get(match.group(0).lower(), match.group(0)),
                updated,
            )
        for pattern, replacement in _VAGUE_QUALIFIER_REPLACEMENTS.items():
            updated = pattern.sub(replacement, updated)
        for pattern, replacement in _SARCASM_REPLACEMENTS.items():
            updated = pattern.sub(replacement, updated)
        return updated


class UrgencyFilter(BaseTransformModule):
    """Reduce urgency signals for anxiety profile while preserving information."""

    name = "urgency_filter"

    def apply(self, text: str, profile: ProfileConfig) -> str:
        if not text.strip():
            return ""
        if _detect_profile(profile) != Profile.ANXIETY:
            return text

        transformed_regions: List[str] = []
        for region, is_protected in _protect_regions(text):
            if is_protected:
                transformed_regions.append(region)
                continue

            sentences = _safe_sent_tokenize(region)
            if not sentences:
                transformed_regions.append(region)
                continue

            rewritten = [self._rewrite_sentence(sentence) for sentence in sentences]
            transformed_regions.append(" ".join(rewritten))

        return "".join(transformed_regions).strip()

    def _rewrite_sentence(self, sentence: str) -> str:
        score = self._score_sentence(sentence)
        if score >= 7:
            return self._remove_urgency(sentence)
        if score >= 4:
            softened = self._remove_urgency(sentence)
            return f"A calm note: {softened}"
        return sentence

    def _score_sentence(self, sentence: str) -> int:
        score = 0
        score += min(2, len(_CAPS_WORD_RE.findall(sentence)))
        score += min(2, len(_EXCLAMATION_RE.findall(sentence)))
        score += min(3, len(_URGENCY_WORD_RE.findall(sentence)))
        score += min(2, len(_NEGATIVE_EMOTION_RE.findall(sentence)))
        if _IMPERATIVE_START_RE.search(sentence):
            score += 2
        return min(score, 10)

    def _remove_urgency(self, sentence: str) -> str:
        softened = sentence
        for pattern, replacement in _ANXIETY_REPLACEMENTS.items():
            softened = pattern.sub(replacement, softened)
        softened = _URGENCY_WORD_RE.sub("important", softened)
        softened = _EXCLAMATION_RE.sub(".", softened)
        softened = _CAPS_WORD_RE.sub(lambda m: m.group(0).capitalize(), softened)
        softened = re.sub(r"\s{2,}", " ", softened).strip()
        if softened and softened[-1] not in ".!?":
            softened += "."
        return softened


class NumberContextualiser(BaseTransformModule):
    """Add relatable context to numbers for dyscalculia profile without removing original values."""

    name = "number_contextualiser"

    def apply(self, text: str, profile: ProfileConfig) -> str:
        if not text.strip():
            return ""
        if _detect_profile(profile) != Profile.DYSCALCULIA:
            return text

        transformed_regions: List[str] = []
        for region, is_protected in _protect_regions(text):
            if is_protected:
                transformed_regions.append(region)
                continue

            updated = region
            updated = _DURATION_RANGE_RE.sub(self._contextualise_duration, updated)
            updated = _DATA_SIZE_RE.sub(self._contextualise_data_size, updated)
            updated = _PERCENT_RE.sub(self._contextualise_percentage, updated)
            updated = _CURRENCY_RE.sub(self._contextualise_currency, updated)
            updated = _LARGE_NUMBER_RE.sub(self._contextualise_large_number, updated)
            updated = _SMALL_DECIMAL_RE.sub(self._contextualise_small_decimal, updated)
            transformed_regions.append(updated)

        return "".join(transformed_regions).strip()

    @staticmethod
    def _has_context(match: re.Match[str]) -> bool:
        suffix = match.string[match.end() :]
        return bool(suffix.lstrip().startswith("("))

    def _contextualise_percentage(self, match: re.Match[str]) -> str:
        if self._has_context(match):
            return match.group(0)
        number = float(match.group(1))
        if number == 10:
            context = "1 in every 10"
        elif number == 25:
            context = "1 in 4"
        elif number == 50:
            context = "about half"
        elif number == 75:
            context = "3 in 4"
        elif number == 1:
            context = "1 in 100"
        else:
            fraction = Fraction(number / 100).limit_denominator(20)
            if fraction.numerator == 1:
                context = f"1 in every {fraction.denominator}"
            else:
                context = f"{fraction.numerator} in every {fraction.denominator}"
        return f"{match.group(0)} ({context})"

    def _contextualise_currency(self, match: re.Match[str]) -> str:
        if self._has_context(match):
            return match.group(0)
        token = match.group(1)
        value = self._parse_scaled_number(token)
        if value is None:
            return token
        context = self._lookup_context(value, _DOLLAR_CONTEXTS)
        return f"{token} ({context})"

    def _contextualise_large_number(self, match: re.Match[str]) -> str:
        token = match.group(0)
        if self._has_context(match):
            return token
        value = self._parse_scaled_number(token)
        if value is None or value < 1000:
            return token
        context = self._lookup_context(value, _PEOPLE_CONTEXTS)
        return f"{token} ({context})"

    def _contextualise_small_decimal(self, match: re.Match[str]) -> str:
        if self._has_context(match):
            return match.group(0)
        token = match.group(1)
        value = float(token)
        if value >= 0.1:
            return token
        denominator = max(10, round(1 / value)) if value > 0 else 1000
        context = f"a very small amount - about 1 in every {denominator:,}"
        return f"{token} ({context})"

    def _contextualise_duration(self, match: re.Match[str]) -> str:
        if self._has_context(match):
            return match.group(0)
        start = int(match.group(1))
        end = int(match.group(2))
        unit = match.group(3).lower()
        unit_key = unit.rstrip("s") + "s"
        context = _TIME_CONTEXTS.get(unit_key, "a meaningful time window")
        return f"{start}-{end} {unit} ({context})"

    def _contextualise_data_size(self, match: re.Match[str]) -> str:
        if self._has_context(match):
            return match.group(0)
        amount = match.group(1)
        unit = match.group(2).lower()
        context = _DATA_CONTEXTS.get(unit, "a common storage amount")
        return f"{amount} {unit.upper()} ({context})"

    @staticmethod
    def _lookup_context(value: float, contexts: Sequence[tuple[float, str]]) -> str:
        if contexts is _DOLLAR_CONTEXTS:
            index = bisect_left(_DOLLAR_THRESHOLDS, value)
            if index >= len(_DOLLAR_DESCRIPTIONS):
                return _DOLLAR_DESCRIPTIONS[-1]
            return _DOLLAR_DESCRIPTIONS[index]
        if contexts is _PEOPLE_CONTEXTS:
            index = bisect_left(_PEOPLE_THRESHOLDS, value)
            if index >= len(_PEOPLE_DESCRIPTIONS):
                return _PEOPLE_DESCRIPTIONS[-1]
            return _PEOPLE_DESCRIPTIONS[index]

        for threshold, description in contexts:
            if value <= threshold:
                return description
        return contexts[-1][1]

    @staticmethod
    def _parse_scaled_number(token: str) -> Optional[float]:
        cleaned = token.lower().replace("$", "").replace("£", "").replace("€", "").replace(",", "")
        cleaned = cleaned.strip()
        multiplier = 1.0
        if cleaned.endswith("k"):
            multiplier = 1_000.0
            cleaned = cleaned[:-1]
        elif cleaned.endswith("m"):
            multiplier = 1_000_000.0
            cleaned = cleaned[:-1]
        elif cleaned.endswith("b"):
            multiplier = 1_000_000_000.0
            cleaned = cleaned[:-1]
        elif cleaned.endswith(" million"):
            multiplier = 1_000_000.0
            cleaned = cleaned.replace(" million", "")
        elif cleaned.endswith(" billion"):
            multiplier = 1_000_000_000.0
            cleaned = cleaned.replace(" billion", "")
        elif cleaned.endswith(" trillion"):
            multiplier = 1_000_000_000_000.0
            cleaned = cleaned.replace(" trillion", "")
        try:
            return float(cleaned) * multiplier
        except ValueError:
            return None


class PriorityReorderer(BaseTransformModule):
    """Reorder paragraphs into an inverted-pyramid structure for ADHD profile."""

    name = "priority_reorderer"

    def apply(self, text: str, profile: ProfileConfig) -> str:
        if not text.strip():
            return ""
        if _detect_profile(profile) != Profile.ADHD:
            return text

        paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(text.strip()) if p.strip()]
        if not paragraphs:
            return text
        if len(paragraphs) == 1:
            sentence_units = [s.strip() for s in _safe_sent_tokenize(paragraphs[0]) if s.strip()]
            if len(sentence_units) > 1:
                paragraphs = sentence_units

        conclusions: List[str] = []
        backgrounds: List[str] = []
        examples: List[str] = []

        for paragraph in paragraphs:
            kind = self._classify_paragraph(paragraph)
            if kind == "conclusion":
                conclusions.append(f"Summary: {paragraph}")
            elif kind == "example":
                examples.append(f"Example: {paragraph}")
            else:
                backgrounds.append(f"Background: {paragraph}")

        result: List[str] = []
        if conclusions:
            result.extend(conclusions)
        else:
            summary_sentence = self._extract_summary_sentence(paragraphs[-1])
            result.append(f"**Bottom line: {summary_sentence}**")
        result.extend(backgrounds)
        result.extend(examples)
        return "\n\n".join(result).strip()

    @staticmethod
    def _classify_paragraph(paragraph: str) -> str:
        lower = paragraph.lower()
        if any(hint in lower for hint in _CONCLUSION_HINTS):
            return "conclusion"
        if any(hint in lower for hint in _EXAMPLE_HINTS):
            return "example"
        return "background"

    @staticmethod
    def _extract_summary_sentence(paragraph: str) -> str:
        sentences = _safe_sent_tokenize(paragraph)
        if sentences:
            return sentences[0]
        trimmed = paragraph.strip()
        return (
            trimmed
            if _NUMBER_TOKEN_RE.search(trimmed) or trimmed
            else "Key details are provided below."
        )


@dataclass(slots=True)
class TransformRun:
    """Execution details for a single module run."""

    module: str
    duration_ms: float
    changed: bool = True
    skipped: bool = False
    error: Optional[str] = None


@dataclass(slots=True)
class TransformPipeline:
    """Run registered transform modules in sequence for a specific profile configuration."""

    profile: ProfileConfig
    modules: List[BaseTransformModule] = field(default_factory=list)
    last_run: List[TransformRun] = field(default_factory=list)
    debug: bool = False
    debug_callback: Optional[Callable[[str], None]] = None
    enable_cache: bool = True
    cache_size: int = 256
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    _cached_transform: Optional[Callable[[str, str, str], str]] = field(
        default=None, init=False, repr=False
    )
    _profile_name: str = field(default="custom", init=False, repr=False)
    _profile_hash: str = field(default="", init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.modules:
            self.register(Chunker())
            self.register(SentenceSimplifier())
            self.register(ToneRewriter())
            self.register(UrgencyFilter())
            self.register(NumberContextualiser())
            self.register(PriorityReorderer())

        detected = _detect_profile(self.profile)
        self._profile_name = detected.value if detected is not None else "custom"
        self._profile_hash = json.dumps(asdict(self.profile), sort_keys=True, ensure_ascii=True)
        self._cached_transform = self._build_cached_transform()

    def register(self, module: BaseTransformModule) -> None:
        """Register a new transform module."""
        if not isinstance(module, BaseTransformModule):
            raise TypeError("module must inherit BaseTransformModule")
        self.modules.append(module)

    def _build_cached_transform(self) -> Callable[[str, str, str], str]:
        @lru_cache(maxsize=max(1, self.cache_size))
        def _runner(text: str, profile_name: str, profile_hash: str) -> str:
            # profile_name/profile_hash are explicit cache-key components.
            _ = (profile_name, profile_hash)
            return self._transform_uncached(text)

        return _runner

    def cache_stats(self) -> Dict[str, float]:
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total) if total else 0.0
        return {
            "hits": float(self.cache_hits),
            "misses": float(self.cache_misses),
            "evictions": float(self.cache_evictions),
            "hit_rate": hit_rate,
        }

    def _transform_uncached(self, text: str) -> str:
        output = text
        self.last_run.clear()
        for module in self.modules:
            if not module.enabled:
                continue
            start = perf_counter()
            before = output
            try:
                output = module.apply(output, self.profile)
                duration_ms = (perf_counter() - start) * 1000
                changed = output != before
                if not changed:
                    warnings.warn(
                        f"Transform module '{module.name}' produced no changes.",
                        UserWarning,
                        stacklevel=2,
                    )
                run = TransformRun(
                    module=module.name,
                    duration_ms=duration_ms,
                    changed=changed,
                    skipped=False,
                    error=None,
                )
                self.last_run.append(run)
                if self.debug and self.debug_callback is not None:
                    verb = "changed" if changed else "no-op"
                    self.debug_callback(
                        f"✓ {module.name}: {len(_WORD_RE.findall(before))} words -> "
                        f"{len(_WORD_RE.findall(output))} words ({duration_ms:.1f}ms, {verb})"
                    )
            except Exception as exc:
                duration_ms = (perf_counter() - start) * 1000
                error = TransformError(module.name, str(exc))
                warnings.warn(str(error), UserWarning, stacklevel=2)
                run = TransformRun(
                    module=module.name,
                    duration_ms=duration_ms,
                    changed=False,
                    skipped=True,
                    error=str(error),
                )
                self.last_run.append(run)
                if self.debug and self.debug_callback is not None:
                    self.debug_callback(f"✗ {module.name}: skipped ({duration_ms:.1f}ms) - {error}")
        return output

    def transform(self, text: str) -> str:
        """Run all enabled modules sequentially."""
        if text is None:
            raise ValueError("text cannot be None")

        if not self.enable_cache or len(text) > 5000 or self._cached_transform is None:
            self.cache_misses += 1
            return self._transform_uncached(text)

        before = self._cached_transform.cache_info()  # type: ignore[attr-defined]
        was_full = before.currsize >= max(1, self.cache_size)
        output = self._cached_transform(text, self._profile_name, self._profile_hash)
        after = self._cached_transform.cache_info()  # type: ignore[attr-defined]

        delta_hits = after.hits - before.hits
        delta_misses = after.misses - before.misses
        self.cache_hits += max(0, delta_hits)
        self.cache_misses += max(0, delta_misses)
        if was_full and delta_misses > 0 and after.currsize == max(1, self.cache_size):
            self.cache_evictions += delta_misses
        return output
