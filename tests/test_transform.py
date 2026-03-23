"""Day 2 tests for Chunker, SentenceSimplifier, and TransformPipeline."""

from neurobridge.core.profile import Profile, get_profile_config
from neurobridge.core.transform import Chunker, SentenceSimplifier, TransformPipeline


def test_pipeline_auto_registers_day2_modules() -> None:
    profile = get_profile_config(Profile.AUTISM)
    pipeline = TransformPipeline(profile=profile)
    names = [module.name for module in pipeline.modules]
    assert names == [
        "chunker",
        "sentence_simplifier",
        "tone_rewriter",
        "urgency_filter",
        "number_contextualiser",
        "priority_reorderer",
    ]


def test_chunker_empty_text_returns_empty() -> None:
    profile = get_profile_config(Profile.AUTISM)
    chunker = Chunker()
    assert chunker.apply("", profile) == ""


def test_chunker_single_sentence_kept() -> None:
    profile = get_profile_config(Profile.AUTISM)
    chunker = Chunker()
    text = "Only one sentence is present."
    out = chunker.apply(text, profile)
    assert "Only one sentence is present." in out


def test_chunker_adhd_bolds_anchor_words_and_chunks() -> None:
    profile = get_profile_config(Profile.ADHD)
    chunker = Chunker()
    text = (
        "Sentence one explains context. Sentence two continues the explanation. "
        "Sentence three gives a key detail. Sentence four adds implications."
    )
    out = chunker.apply(text, profile)
    assert "**" in out
    assert "\n\n" in out


def test_chunker_dyslexia_uses_extra_spacing() -> None:
    profile = get_profile_config(Profile.DYSLEXIA)
    chunker = Chunker()
    text = (
        "One short sentence. Two short sentence. Three short sentence. "
        "Four short sentence. Five short sentence."
    )
    out = chunker.apply(text, profile)
    assert "\n\n\n" in out


def test_chunker_handles_ten_sentences() -> None:
    profile = get_profile_config(Profile.AUTISM)
    chunker = Chunker()
    text = " ".join([f"Sentence {i}." for i in range(1, 11)])
    out = chunker.apply(text, profile)
    assert out.count("Sentence") == 10
    assert out.count("\n\n") >= 4


def test_chunker_preserves_markdown_numbered_list_and_code_blocks() -> None:
    profile = get_profile_config(Profile.ADHD)
    chunker = Chunker()
    text = (
        "This paragraph should be chunked. It has enough sentences to trigger behavior.\n\n"
        "1. First item in list\n"
        "2. Second item in list\n\n"
        "```python\n"
        "def hello():\n"
        "    return 'world'\n"
        "```\n\n"
        "Final sentence for adaptation."
    )
    out = chunker.apply(text, profile)
    assert "1. First item in list" in out
    assert "2. Second item in list" in out
    assert "```python" in out
    assert "return 'world'" in out


def test_sentence_simplifier_splits_long_sentence_at_conjunction() -> None:
    profile = get_profile_config(Profile.DYSLEXIA)
    simplifier = SentenceSimplifier()
    text = (
        "This sentence intentionally includes many words, and it should split at a natural "
        "conjunction because the configured sentence length is strict for this profile."
    )
    out = simplifier.apply(text, profile)
    assert ". And" in out or ". But" in out or ". Which" in out or ". That" in out


def test_sentence_simplifier_splits_at_semicolon_when_needed() -> None:
    profile = get_profile_config(Profile.DYSLEXIA)
    simplifier = SentenceSimplifier()
    text = (
        "This sentence is quite long and has no preferred clause markers to split naturally; "
        "therefore it should split using the semicolon fallback to keep it readable."
    )
    out = simplifier.apply(text, profile)
    assert ";" not in out
    assert ". Therefore" in out


def test_sentence_simplifier_leaves_short_sentence_untouched() -> None:
    profile = get_profile_config(Profile.AUTISM)
    simplifier = SentenceSimplifier()
    text = "This sentence is concise and clear."
    out = simplifier.apply(text, profile)
    assert out == text


def test_sentence_simplifier_keeps_code_blocks_unchanged() -> None:
    profile = get_profile_config(Profile.DYSLEXIA)
    simplifier = SentenceSimplifier()
    text = "```python\nif x and y and z:\n    print('ok')\n```"
    out = simplifier.apply(text, profile)
    assert out == text


def test_pipeline_tracks_execution_timing() -> None:
    profile = get_profile_config(Profile.AUTISM)
    pipeline = TransformPipeline(profile=profile)
    out = pipeline.transform("Alpha sentence. Beta sentence. Gamma sentence.")
    assert out
    assert len(pipeline.last_run) == 6
    assert all(run.duration_ms >= 0 for run in pipeline.last_run)
