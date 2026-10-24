"""Day 2 tests for Chunker, SentenceSimplifier, and TransformPipeline."""

from neurobridge.core.bridge import Config, NeuroBridge
from neurobridge.core.profile import Profile, get_profile_config
from neurobridge.core.transform import Chunker, SentenceSimplifier, TransformPipeline


def test_pipeline_auto_registers_day2_modules() -> None:
    profile = get_profile_config(Profile.AUTISM)
    pipeline = TransformPipeline(profile=profile)
    names = [module.name for module in pipeline.modules]
    assert names == [
        "chunker",
        "sentence_simplifier",
        "urgency_filter",
        "tone_rewriter",
        "number_contextualiser",
        "priority_reorderer",
    ]


def test_anxiety_pipeline_softens_urgency_end_to_end() -> None:
    """Regression: tone_rewriter used to neutralize urgency words before the
    urgency filter could score them, so raw urgency signals like "NOW!" and
    "must" survived the full anxiety pipeline untouched."""
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ANXIETY)
    adapted = bridge.adapt(
        "You must fix this NOW! It is urgent and critical to submit immediately."
    )

    assert "NOW!" not in adapted
    assert "must fix" not in adapted.lower()
    # The urgency vocabulary has to be rewritten, not merely re-scored.
    assert "urgent" not in adapted.lower() or "worth noting" in adapted.lower()
    # Calm-note softening should engage for clearly urgent sentences.
    assert "calm note" in adapted.lower()


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


def test_tone_rewriter_preserves_paragraph_breaks() -> None:
    """Regression: _strip_fillers collapsed paragraph breaks to single spaces
    for every profile, flattening multi-paragraph documents into one slab."""
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    adapted = bridge.adapt("Para one here.\n\nPara two here.\n\nPara three here.")

    assert adapted.count("\n\n") >= 2
    assert "Para one here." in adapted
    assert "Para three here." in adapted


def test_urgency_filter_preserves_paragraph_breaks() -> None:
    """Regression: urgency_filter joined all sentences of a region with single
    spaces, destroying the paragraph/chunk structure produced by the chunker."""
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ANXIETY)
    adapted = bridge.adapt(
        "The service is now available.\n\nPlease review the notes.\n\nThanks for reading."
    )

    assert adapted.count("\n\n") >= 2


def test_adhd_pipeline_does_not_duplicate_summary_paragraph() -> None:
    """Regression: PriorityReorderer extracted the 'Bottom line' from the last
    paragraph but also kept that paragraph in the body, emitting its content
    twice for every ADHD adaptation without a conclusion-classified paragraph."""
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    adapted = bridge.adapt(
        "First paragraph explains the background.\n\nSecond paragraph holds the closing thought."
    )

    # The last paragraph's first sentence becomes the bottom line, and the rest
    # of the document appears exactly once.
    assert "Bottom line" in adapted
    assert adapted.count("Second paragraph holds the closing thought.") <= 1


def test_adhd_pipeline_emits_balanced_bold_markers() -> None:
    """Regression: the chunker bolds anchor words, and the reorderer wrapped the
    (already bolded) summary sentence in another '**...**', producing nested and
    unbalanced markup like '**Bottom line: **Second paragraph** text here.****'."""
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    adapted = bridge.adapt(
        "First paragraph text.\n\nSecond paragraph text here with more words to say."
    )

    assert adapted.count("**") % 2 == 0
    assert "****" not in adapted


def test_number_contextualiser_small_percentages_are_mathematically_true() -> None:
    """Regression: Fraction(...).limit_denominator(20) rounds percentages below
    2.5% to 0/1, and the module emitted '(0 in every 1)' - a false statement
    from the one module whose job is numeric clarity for dyscalculia users."""
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.DYSCALCULIA)
    adapted = bridge.adapt("Only 2% failed the check.")

    assert "0 in every 1" not in adapted
    assert "less than 1 in every 20" in adapted

    adapted2 = bridge.adapt("About 0.7% of users are affected.")
    assert "0 in every 1" not in adapted2


def test_pipeline_does_not_warn_on_expected_no_ops() -> None:
    """Regression: every transform emitted up to five UserWarnings because
    profile-specific modules report no-ops for all other profiles. Library
    users saw warning spam on stderr for each adapt() call."""
    import warnings as _warnings

    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        bridge.adapt("A plain sentence. Another one follows it. A third sentence here.")
    noop_warnings = [w for w in caught if "produced no changes" in str(w.message)]
    assert noop_warnings == []


def test_sentence_tokenizer_keeps_markup_fragments_attached() -> None:
    """Regression: the fallback tokenizer split '**Bold text.**' into
    ['**Bold text.', '**'], which later modules rejoined with spaces,
    producing '**Bold text. **' with the closing marker detached."""
    from neurobridge.core.transform import _safe_sent_tokenize

    sentences = _safe_sent_tokenize("**Bold intro.** Plain second sentence.")
    assert any(s.startswith("**") and s.endswith("**") for s in sentences)
    for sentence in sentences:
        assert sentence.strip() != "**"


def test_adhd_pipeline_keeps_code_fences_at_line_start() -> None:
    """Regression: PriorityReorderer prefixed 'Background: ' onto paragraphs
    that are code fences; a fence not at the start of a line is not a fence
    in CommonMark, so the code block stopped rendering."""
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    adapted = bridge.adapt("Intro paragraph.\n\n```python\nprint(1)\n```\n\nAfter the code block.")

    assert adapted.count("**") % 2 == 0
    assert "****" not in adapted
    for line in adapted.splitlines():
        if "```" in line:
            # Every fence must sit at the start of its line (labels go on the
            # line above), and closing fences must not carry an info string.
            assert line.lstrip().startswith("```")
            assert "Background: ```" not in line
