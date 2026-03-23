"""Day 22 cassette-backed integration tests for wrappers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests
import vcr

from neurobridge import Config, Profile
from neurobridge.integrations.anthropic import wrap as wrap_anthropic
from neurobridge.integrations.openai import wrap as wrap_openai

CASSETTE_DIR = Path(__file__).resolve().parents[1] / "cassettes"

VCR = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="none",
    match_on=["method", "scheme", "host", "port", "path", "query"],
)


@dataclass
class _Message:
    content: str


@dataclass
class _Choice:
    message: _Message


@dataclass
class _OpenAIResponse:
    choices: list[_Choice]


class _MockOpenAICompletions:
    def create(self, *args, **kwargs):  # noqa: ANN002, ANN003
        _ = args, kwargs
        with VCR.use_cassette("openai_chat.yaml"):
            payload = requests.get("https://api.openai.mock/v1/chat/completions", timeout=3).json()
        content = payload["choices"][0]["message"]["content"]
        return _OpenAIResponse(choices=[_Choice(message=_Message(content=content))])


class _MockOpenAIChat:
    def __init__(self) -> None:
        self.completions = _MockOpenAICompletions()


class _MockOpenAIClient:
    def __init__(self) -> None:
        self.chat = _MockOpenAIChat()


@dataclass
class _AnthropicContentBlock:
    text: str


@dataclass
class _AnthropicResponse:
    content: list[_AnthropicContentBlock]


class _MockAnthropicMessages:
    def create(self, *args, **kwargs):  # noqa: ANN002, ANN003
        _ = args, kwargs
        with VCR.use_cassette("anthropic_messages.yaml"):
            payload = requests.get("https://api.anthropic.mock/v1/messages", timeout=3).json()
        text = payload["content"][0]["text"]
        return _AnthropicResponse(content=[_AnthropicContentBlock(text=text)])


class _MockAnthropicClient:
    def __init__(self) -> None:
        self.messages = _MockAnthropicMessages()


def test_openai_wrapper_with_vcr_cassette() -> None:
    wrapped = wrap_openai(
        _MockOpenAIClient(), profile=Profile.ANXIETY, config=Config(memory_backend="none")
    )
    result = wrapped.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": "hello"}]
    )
    text = result.choices[0].message.content.lower()
    assert "asap" not in text
    assert "critical" not in text


def test_anthropic_wrapper_with_vcr_cassette() -> None:
    wrapped = wrap_anthropic(
        _MockAnthropicClient(), profile=Profile.ANXIETY, config=Config(memory_backend="none")
    )
    result = wrapped.messages.create(
        model="claude-3", messages=[{"role": "user", "content": "hello"}]
    )
    text = result.content[0].text.lower()
    assert "urgent" not in text
    assert "immediately" not in text


def test_cassette_payload_shape_matches_realistic_format() -> None:
    with VCR.use_cassette("openai_chat.yaml"):
        payload = requests.get("https://api.openai.mock/v1/chat/completions", timeout=3).json()
    assert "choices" in payload
