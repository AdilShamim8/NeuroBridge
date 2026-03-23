"""Day 10 tests for streaming adaptation support."""

import asyncio
import json
from typing import Optional

from fastapi.testclient import TestClient

from neurobridge import Config, NeuroBridge, Profile
from neurobridge.core.bridge import AdaptedResponse
from neurobridge.integrations.openai import wrap as wrap_openai
from neurobridge.server.app import create_app
from neurobridge.server.config import ServerConfig


async def _collect_stream(bridge: NeuroBridge, message: str, user_id: Optional[str] = None):
    chunks = []
    final = None
    async for item in bridge.chat_stream(message, user_id=user_id):
        if isinstance(item, AdaptedResponse):
            final = item
        else:
            chunks.append(item)
    return chunks, final


def test_chat_stream_yields_chunks_in_order() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    message = "First sentence. Second sentence. Third sentence. Fourth sentence."

    chunks, final = asyncio.run(_collect_stream(bridge, message))
    assert len(chunks) == 2
    assert "First sentence." in chunks[0]
    assert "Fourth sentence." in chunks[1]
    assert isinstance(final, AdaptedResponse)


def test_sentence_buffering_for_adhd_chunk_size_three() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ADHD)
    message = "One. Two. Three. Four. Five."

    chunks, _ = asyncio.run(_collect_stream(bridge, message))
    assert len(chunks) == 2
    assert "One." in chunks[0] and "Three." in chunks[0]
    assert "Four." in chunks[1] and "Five." in chunks[1]


def test_chat_stream_anxiety_tone_rewriter_per_chunk() -> None:
    bridge = NeuroBridge(config=Config(memory_backend="none"))
    bridge.set_profile(Profile.ANXIETY)
    message = "This is critical and you must do it ASAP. Next sentence is neutral."

    chunks, _ = asyncio.run(_collect_stream(bridge, message))
    combined = " ".join(chunks).lower()
    assert "asap" not in combined
    assert "must" not in combined


def test_sse_stream_endpoint_format(tmp_path) -> None:
    app = create_app(
        config=Config(memory_backend="sqlite", memory_path=str(tmp_path / "sse.db")),
        server_config=ServerConfig(allowed_origins=["*"], rate_limit_per_minute=500),
    )
    client = TestClient(app)

    response = client.post("/api/v1/adapt/stream", json={"text": "One. Two. Three."})
    assert response.status_code == 200
    payload_lines = [line for line in response.text.splitlines() if line.startswith("data: ")]
    assert payload_lines

    decoded = [json.loads(line.replace("data: ", "", 1)) for line in payload_lines]
    assert any(item.get("done") is False for item in decoded)
    assert decoded[-1].get("done") is True
    assert "interaction_id" in decoded[-1]


class _MockOpenAICompletions:
    def create(self, *args, **kwargs):  # noqa: ANN002, ANN003
        _ = args, kwargs
        return []


class _MockOpenAIChat:
    def __init__(self) -> None:
        self.completions = _MockOpenAICompletions()


class _MockOpenAIClient:
    def __init__(self) -> None:
        self.chat = _MockOpenAIChat()


def test_openai_wrapper_stream_true_returns_streaming_chunks() -> None:
    client = _MockOpenAIClient()
    wrapped = wrap_openai(client, profile=Profile.ANXIETY, config=Config(memory_backend="none"))

    stream = wrapped.chat.completions.create(
        stream=True,
        messages=[{"role": "user", "content": "This is critical and must be fixed ASAP."}],
    )
    contents = []
    for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            contents.append(text)

    assert contents
    combined = " ".join(contents).lower()
    assert "asap" not in combined
    assert "must" not in combined
