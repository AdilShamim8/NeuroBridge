"""Day 1 bridge scaffold tests."""

from neurobridge import Config, CustomProfile, NeuroBridge, Profile


def test_set_builtin_profile() -> None:
    bridge = NeuroBridge(config=Config())
    bridge.set_profile(Profile.DYSLEXIA)
    assert bridge.profile == Profile.DYSLEXIA


def test_set_custom_profile() -> None:
    bridge = NeuroBridge()
    custom = CustomProfile(
        chunk_size=2,
        tone="calm",
        ambiguity_resolution="explicit",
        number_format="contextual",
        leading_style="summary_first",
        reading_level=6,
        max_sentence_words=12,
    )
    bridge.set_profile(custom)
    assert bridge.profile == Profile.CUSTOM


def test_chat_stub_returns_response() -> None:
    bridge = NeuroBridge()
    response = bridge.chat("Explain neural networks.")
    assert response.raw_text
    assert response.adapted_text
    assert response.interaction_id
