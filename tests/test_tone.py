"""Day 3 tests for ToneRewriter and UrgencyFilter modules."""

from neurobridge.core.profile import Profile, get_profile_config
from neurobridge.core.transform import ToneRewriter, UrgencyFilter


def test_tone_rewriter_calms_anxiety_phrasing() -> None:
    profile = get_profile_config(Profile.ANXIETY)
    rewriter = ToneRewriter()
    text = "This is critical and you must fix this ASAP."
    out = rewriter.apply(text, profile)
    assert "critical" not in out.lower()
    assert "must" not in out.lower()
    assert "asap" not in out.lower()
    assert "important" in out.lower() or "consider" in out.lower()


def test_tone_rewriter_replaces_autism_idioms() -> None:
    profile = get_profile_config(Profile.AUTISM)
    rewriter = ToneRewriter()
    text = "Let's touch base and hit the ground running with a ball park figure."
    out = rewriter.apply(text, profile)
    lowered = out.lower()
    assert "touch base" not in lowered
    assert "hit the ground running" not in lowered
    assert "ball park figure" not in lowered
    assert "make contact" in lowered
    assert "start working immediately" in lowered
    assert "rough estimate" in lowered


def test_urgency_filter_high_medium_low_scoring_paths() -> None:
    profile = get_profile_config(Profile.ANXIETY)
    module = UrgencyFilter()
    high = "URGENT! You MUST FIX THIS ASAP!!!"
    medium = "Fix this urgent report now!"
    low = "When you are ready, review the notes."

    high_out = module.apply(high, profile)
    medium_out = module.apply(medium, profile)
    low_out = module.apply(low, profile)

    assert "asap" not in high_out.lower()
    assert "a calm note:" in medium_out.lower() or "soon" not in medium_out.lower()
    assert low_out == low


def test_non_target_profile_not_modified_by_tone_rewriter() -> None:
    profile = get_profile_config(Profile.DYSLEXIA)
    rewriter = ToneRewriter()
    text = "Please review the implementation details carefully."
    out = rewriter.apply(text, profile)
    assert out == text
