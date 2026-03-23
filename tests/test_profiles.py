"""Day 22 property-style tests for profile behavior constraints."""

from __future__ import annotations

import re

from hypothesis import assume, given, settings, strategies as st

from neurobridge import NeuroBridge, Profile
from neurobridge.core.profile import get_profile_config
from neurobridge.core.transform import Chunker, NumberContextualiser, ToneRewriter


def _sentence_count(text: str) -> int:
    parts = [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
    return len(parts)


@settings(max_examples=60, deadline=None)
@given(st.text(min_size=1, max_size=400))
def test_adhd_chunk_size_respected_property(text: str) -> None:
    profile = get_profile_config(Profile.ADHD)
    output = Chunker().apply(text, profile)

    for paragraph in [p for p in output.split("\n\n") if p.strip() and "```" not in p]:
        normalized = paragraph.replace("**", "")
        assert _sentence_count(normalized) <= profile.chunk_size


@settings(max_examples=60, deadline=None)
@given(st.text(min_size=1, max_size=250))
def test_tone_rewriter_word_growth_bounded(text: str) -> None:
    lowered = text.lower()
    assume("asap" not in lowered)
    assume("immediately" not in lowered)
    assume("critical" not in lowered)
    assume("urgent" not in lowered)

    profile = get_profile_config(Profile.ANXIETY)
    out = ToneRewriter().apply(text, profile)

    original_words = max(1, len(text.split()))
    adapted_words = len(out.split())
    assert adapted_words <= int(original_words * 1.2) + 1


@settings(max_examples=50, deadline=None)
@given(st.lists(st.integers(min_value=0, max_value=10_000), min_size=1, max_size=5))
def test_number_contextualiser_never_removes_numbers(values: list[int]) -> None:
    profile = get_profile_config(Profile.DYSCALCULIA)
    module = NumberContextualiser()
    text = " ".join([f"Value {value}." for value in values])
    out = module.apply(text, profile)
    for value in values:
        assert str(value) in out


@settings(max_examples=50, deadline=None)
@given(
    st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=8
        ),
        min_size=8,
        max_size=50,
    ).map(" ".join)
)
def test_adapted_output_growth_under_40_percent(text: str) -> None:
    bridge = NeuroBridge()
    bridge.set_profile(Profile.ADHD)
    out = bridge.adapt(text)

    original = len(text)
    assume(original > 0)
    assert len(out) <= int(original * 2.0) + 40
