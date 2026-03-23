"""Additional Day 22 bridge coverage tests for config and streaming helpers."""

from __future__ import annotations

import asyncio

import pytest

from neurobridge import Config, NeuroBridge, Profile
from neurobridge.core.bridge import AdaptedResponse
from neurobridge.core.memory import ProfileAdjustments


def test_config_from_env_parses_and_sanitizes(monkeypatch) -> None:
    monkeypatch.setenv("NEUROBRIDGE_MEMORY_BACKEND", "invalid")
    monkeypatch.setenv("NEUROBRIDGE_OUTPUT_FORMAT", "unknown")
    monkeypatch.setenv("NEUROBRIDGE_MAX_CHUNK_WORDS", "bad")
    monkeypatch.setenv("NEUROBRIDGE_AUTO_ADJUST_AFTER", "0")
    monkeypatch.setenv("NEUROBRIDGE_DEBUG", "true")

    cfg = Config.from_env()
    assert cfg.memory_backend == "sqlite"
    assert cfg.output_format == "markdown"
    assert cfg.max_chunk_words >= 1
    assert cfg.auto_adjust_after >= 1
    assert cfg.debug is True


def test_chat_raises_profile_not_set_when_not_explicit() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge._profile_explicit = False  # noqa: SLF001

    with pytest.raises(Exception):
        bridge.chat("Hello")


class _FailingClient:
    def chat(self, message: str, **kwargs):  # noqa: ANN003
        _ = message, kwargs
        raise RuntimeError("boom")


def test_chat_wraps_llm_client_errors() -> None:
    bridge = NeuroBridge(llm_client=_FailingClient(), config=Config(memory_backend="none"))
    with pytest.raises(Exception):
        bridge.chat("message")


def test_apply_adjustments_updates_profile_and_pipeline() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)

    bridge._apply_adjustments(  # noqa: SLF001
        ProfileAdjustments(
            chunk_size_delta=1,
            max_sentence_words_delta=-2,
            tone="calm",
            reason="test",
        )
    )
    assert bridge.profile == Profile.CUSTOM
    assert bridge._profile_config.tone == "calm"  # noqa: SLF001


def test_stream_helpers_extract_and_tail_detection() -> None:
    sentences, tail = NeuroBridge._extract_complete_sentences("One. Two. Three")  # noqa: SLF001
    assert len(sentences) == 2
    assert tail.strip() == "Three"

    assert NeuroBridge._has_incomplete_numeric_tail("Revenue is 3.") is True  # noqa: SLF001
    assert NeuroBridge._has_incomplete_numeric_tail("Revenue is 3. Done.") is False  # noqa: SLF001


class _StreamDelta:
    def __init__(self, content: str) -> None:
        self.content = content


class _StreamChoice:
    def __init__(self, content: str) -> None:
        self.delta = _StreamDelta(content)


class _StreamPiece:
    def __init__(self, content: str) -> None:
        self.choices = [_StreamChoice(content)]


class _StreamingClient:
    def chat_stream(self, message: str, **kwargs):  # noqa: ANN003
        _ = kwargs

        async def _gen():
            for token in ["This is critical and ", "must be fixed ASAP."]:
                yield _StreamPiece(token)

        _ = message
        return _gen()


async def _collect(bridge: NeuroBridge):
    chunks = []
    final = None
    async for part in bridge.chat_stream("ignored"):
        if isinstance(part, AdaptedResponse):
            final = part
        else:
            chunks.append(part)
    return chunks, final


def test_chat_stream_with_client_chat_stream_path() -> None:
    bridge = NeuroBridge(llm_client=_StreamingClient(), config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ANXIETY)

    chunks, final = asyncio.run(_collect(bridge))
    assert chunks
    assert isinstance(final, AdaptedResponse)
    assert "asap" not in " ".join(chunks).lower()


def test_close_and_aclose_are_safe_without_store() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.close()
    asyncio.run(bridge.aclose())


def test_adapt_validation_and_empty_behaviour() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    with pytest.raises(TypeError):
        bridge.adapt(123)  # type: ignore[arg-type]
    assert bridge.adapt("   ") == ""


def test_extract_chunk_text_variants() -> None:
    class _TextChunk:
        text = "plain"

    class _Other:
        def __str__(self) -> str:
            return "fallback"

    assert NeuroBridge._extract_chunk_text(_TextChunk()) == "plain"  # noqa: SLF001
    assert NeuroBridge._extract_chunk_text(_Other()) == "fallback"  # noqa: SLF001


class _ChatOnlyClient:
    def chat(self, message: str, **kwargs):  # noqa: ANN003
        _ = kwargs
        return f"reply:{message}"


async def _collect_source_chunks(bridge: NeuroBridge, message: str):
    output = []
    async for token in bridge._iterate_source_chunks(message):  # noqa: SLF001
        output.append(token)
    return output


def test_iterate_source_chunks_chat_fallback_path() -> None:
    bridge = NeuroBridge(llm_client=_ChatOnlyClient(), config=Config(memory_backend="none"))
    tokens = asyncio.run(_collect_source_chunks(bridge, "hello"))
    assert "reply:hello" in "".join(tokens)
