"""Additional branch tests for bridge release-readiness coverage."""

from __future__ import annotations

import asyncio
import builtins

import pytest

from neurobridge import Config, NeuroBridge, Profile
from neurobridge.core.bridge import AdaptedResponse
from neurobridge.core.memory import InMemoryStore, ProfileAdjustments, create_feedback_record
from neurobridge.core.profile import get_profile_config


class _SyncStreamingClient:
    def chat_stream(self, message: str, **kwargs):  # noqa: ANN003
        _ = message, kwargs
        return ["Hello ", "world."]


class _BadStreamingClient:
    def chat_stream(self, message: str, **kwargs):  # noqa: ANN003
        _ = message, kwargs
        raise RuntimeError("stream failed")


class _NoMethodClient:
    pass


async def _collect_stream_parts(bridge: NeuroBridge, message: str, user_id: str | None = None):
    chunks = []
    final = None
    async for item in bridge.chat_stream(message, user_id=user_id):
        if isinstance(item, AdaptedResponse):
            final = item
        else:
            chunks.append(item)
    return chunks, final


def test_set_debug_updates_pipeline_flags() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_debug(True)
    assert bridge.config.debug is True
    assert bridge._pipeline.debug is True  # noqa: SLF001

    bridge.set_debug(False)
    assert bridge._pipeline.debug is False  # noqa: SLF001
    assert bridge._pipeline.debug_callback is None  # noqa: SLF001


def test_build_memory_store_invalid_backend_raises() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))

    class _BadConfig:
        memory_backend = "invalid"
        memory_path = "ignored"
        redis_url = "redis://localhost:6379/0"

    with pytest.raises(ValueError):
        bridge._build_memory_store(_BadConfig())  # type: ignore[arg-type]  # noqa: SLF001


def test_export_and_delete_user_data_with_none_store() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    exported = bridge.export_user_data("user1")
    assert exported["memory_backend"] == "none"
    assert exported["profile"] is None
    bridge.delete_user_data("user1")


def test_export_delete_and_feedback_with_inmemory_store() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    store = InMemoryStore()
    bridge._memory_store = store  # noqa: SLF001

    profile = get_profile_config(Profile.ADHD)
    store.save_profile("u1", profile)
    store.save_feedback(create_feedback_record("u1", "original", "adapted", "edited"))
    store.increment_interaction("u1")

    exported = bridge.export_user_data("u1")
    assert exported["profile"] is not None
    assert exported["feedback"]
    assert exported["interaction_count"] == 1

    bridge.delete_user_data("u1")
    assert store.load_profile("u1") is None


def test_submit_feedback_no_store_is_noop() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.submit_feedback("a", "b", "c", "u1")


def test_chat_stream_with_sync_chat_stream_client_branch() -> None:
    bridge = NeuroBridge(llm_client=_SyncStreamingClient(), config=Config(memory_backend="none"))
    chunks, final = asyncio.run(_collect_stream_parts(bridge, "ignored"))
    assert "Hello" in "".join(chunks)
    assert isinstance(final, AdaptedResponse)


def test_chat_stream_wraps_chat_stream_errors() -> None:
    bridge = NeuroBridge(llm_client=_BadStreamingClient(), config=Config(memory_backend="none"))

    async def _run() -> None:
        async for _ in bridge.chat_stream("message"):
            pass

    with pytest.raises(Exception):
        asyncio.run(_run())


def test_tokenize_stream_input_edge_cases() -> None:
    assert list(NeuroBridge._tokenize_stream_input("word one"))  # noqa: SLF001
    assert list(NeuroBridge._tokenize_stream_input("")) == []  # noqa: SLF001


def test_aenter_aexit_and_close_with_store() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge._memory_store = InMemoryStore()  # noqa: SLF001

    async def _ctx_run() -> None:
        async with bridge as entered:
            assert entered is bridge

    asyncio.run(_ctx_run())
    bridge.close()


def test_apply_adjustments_keeps_minimum_bounds() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    bridge._apply_adjustments(  # noqa: SLF001
        ProfileAdjustments(chunk_size_delta=-100, max_sentence_words_delta=-100, tone=None)
    )
    assert bridge._profile_config.chunk_size >= 1  # noqa: SLF001
    assert bridge._profile_config.max_sentence_words >= 6  # noqa: SLF001


def test_iterate_source_chunks_falls_back_for_client_without_chat_methods() -> None:
    bridge = NeuroBridge(llm_client=_NoMethodClient(), config=Config(memory_backend="none"))

    async def _run() -> list[str]:
        items = []
        async for token in bridge._iterate_source_chunks("alpha beta"):  # noqa: SLF001
            items.append(token)
        return items

    out = asyncio.run(_run())
    assert "".join(out).strip() == "alpha beta"


def test_config_from_env_uses_defaults_for_unknown_bool_values(monkeypatch) -> None:
    monkeypatch.setenv("NEUROBRIDGE_CACHE_PROFILES", "maybe")
    monkeypatch.setenv("NEUROBRIDGE_FEEDBACK_LEARNING", "maybe")
    monkeypatch.delenv("NEUROBRIDGE_MAX_TEXT_LENGTH", raising=False)

    cfg = Config.from_env()
    assert cfg.cache_profiles is True
    assert cfg.feedback_learning is True
    assert cfg.max_text_length == 50_000


def test_debug_log_falls_back_to_print_if_rich_is_unavailable(monkeypatch, capsys) -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none", debug=True))

    original_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name.startswith("rich"):
            raise ImportError("rich missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    bridge._debug_log("fallback message")  # noqa: SLF001

    output = capsys.readouterr().out
    assert "fallback message" in output


def test_debug_log_uses_rich_when_available() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none", debug=True))
    # Smoke-test rich branch in _debug_log; this should not raise.
    bridge._debug_log("rich message")  # noqa: SLF001


def test_extract_chunk_text_from_choices_and_text_object() -> None:
    class _Delta:
        content = "from-delta"

    class _Choice:
        delta = _Delta()

    class _WithChoices:
        choices = [_Choice()]

    class _WithText:
        text = "from-text"

    assert NeuroBridge._extract_chunk_text(_WithChoices()) == "from-delta"  # noqa: SLF001
    assert NeuroBridge._extract_chunk_text(_WithText()) == "from-text"  # noqa: SLF001
