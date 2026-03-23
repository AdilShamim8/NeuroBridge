"""Day 11 tests for output format adapters."""

import json
from html.parser import HTMLParser

from neurobridge.core.format_adapter import (
    HTMLAdapter,
    JSONAdapter,
    MarkdownAdapter,
    PlainTextAdapter,
    TTSAdapter,
)
from neurobridge.core.profile import Profile, get_profile_config


class _HTMLValidator(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.errors = []

    def error(self, message):  # type: ignore[override]
        self.errors.append(message)


def test_markdown_adapter_outputs_clean_markdown() -> None:
    adapter = MarkdownAdapter()
    profile = get_profile_config(Profile.ADHD)
    text = "##Header\n\n![ ](https://example.com/x.png)\n\n```\nprint('hi')\n```"
    out = adapter.format(text, profile)
    assert "## Header" in out
    assert "```text" in out
    assert "aria-label" in out


def test_html_adapter_contains_semantic_and_aria_labels() -> None:
    adapter = HTMLAdapter()
    profile = get_profile_config(Profile.ADHD)
    text = "# Title\n\nSummary: One. Two. Three."
    out = adapter.format(text, profile)
    assert "<article" in out
    assert 'role="main"' in out
    assert 'role="navigation"' in out
    assert "nb-progress" in out


def test_html_output_is_valid_parseable() -> None:
    adapter = HTMLAdapter()
    profile = get_profile_config(Profile.DYSLEXIA)
    text = "# A heading\n\n- one\n- two\n\nParagraph"
    out = adapter.format(text, profile)

    parser = _HTMLValidator()
    parser.feed(out)
    assert not parser.errors


def test_plain_text_adapter_strips_markdown_and_formats_bullets() -> None:
    adapter = PlainTextAdapter()
    profile = get_profile_config(Profile.ADHD)
    text = "## Section\n\n- item\n\n**important** note"
    out = adapter.format(text, profile)
    assert "----------" in out
    assert "• item" in out
    assert "IMPORTANT" in out


def test_json_adapter_returns_expected_schema() -> None:
    adapter = JSONAdapter()
    profile = get_profile_config(Profile.ADHD)
    text = "# Heading\n\nSummary: Do this first.\n\nExample: Then try this."
    out = adapter.format(text, profile)
    payload = json.loads(out)

    assert payload["profile"] == "adhd"
    assert isinstance(payload["blocks"], list)
    assert "metadata" in payload
    assert "total_chunks" in payload["metadata"]
    assert "transforms_applied" in payload["metadata"]


def test_tts_adapter_expands_acronyms_and_numbers() -> None:
    adapter = TTSAdapter()
    profile = get_profile_config(Profile.ANXIETY)
    text = "# API status\nAI + URL reached 42% and budget is $3.2M"
    out = adapter.format(text, profile)
    lowered = out.lower()
    assert "a.p.i." in lowered
    assert "a.i." in lowered
    assert "u.r.l." in lowered
    assert "forty-two" in lowered
    assert "3.2 million dollars" in lowered
    assert "percent" in lowered
