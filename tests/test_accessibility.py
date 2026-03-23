"""Day 22 accessibility-focused adaptation tests."""

from __future__ import annotations

import re

from neurobridge import NeuroBridge, Profile
from neurobridge.core.profile import get_profile_config


def _words(sentence: str) -> int:
    return len([w for w in sentence.split() if w.strip()])


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def test_dyslexia_average_sentence_length_under_15() -> None:
    bridge = NeuroBridge()
    bridge.set_profile(Profile.DYSLEXIA)
    text = (
        "This sentence contains a long explanatory clause, and it should split at natural conjunction points for readability. "
        "This second sentence includes dense phrasing, which should also be simplified for easier processing."
    )
    out = bridge.adapt(text)
    sentences = _sentences(out)
    avg = sum(_words(s) for s in sentences) / max(1, len(sentences))
    assert avg < 15


def test_adhd_paragraph_sentences_respect_chunk_size() -> None:
    bridge = NeuroBridge()
    bridge.set_profile(Profile.ADHD)
    profile = get_profile_config(Profile.ADHD)
    text = " ".join([f"Sentence {i} about deployment planning." for i in range(1, 18)])
    out = bridge.adapt(text)
    paragraphs = [p for p in out.split("\n\n") if p.strip()]

    for paragraph in paragraphs:
        normalized = paragraph.replace("**", "")
        assert len(_sentences(normalized)) <= profile.chunk_size


def test_anxiety_urgency_words_decrease() -> None:
    bridge = NeuroBridge()
    bridge.set_profile(Profile.ANXIETY)
    text = "URGENT! This is critical. You must complete this immediately and respond ASAP."
    out = bridge.adapt(text)

    urgency_words = ["urgent", "critical", "must", "immediately", "asap"]
    before = sum(text.lower().count(token) for token in urgency_words)
    after = sum(out.lower().count(token) for token in urgency_words)
    assert after < before


def test_autism_idiom_replaced_when_present() -> None:
    bridge = NeuroBridge()
    bridge.set_profile(Profile.AUTISM)
    text = "We should touch base tomorrow and hit the ground running."
    out = bridge.adapt(text).lower()
    assert "touch base" not in out
    assert "hit the ground running" not in out


def test_dyscalculia_numbers_gain_parenthetical_context() -> None:
    bridge = NeuroBridge()
    bridge.set_profile(Profile.DYSCALCULIA)
    text = "Revenue reached 1,500,000 and conversion was 25%."
    out = bridge.adapt(text)
    assert "1,500,000 (" in out
    assert "25% (" in out
