"""Day 10 tests for streaming adaptation support."""

import asyncio
import json

from fastapi.testclient import TestClient

from neurobridge import Config, NeuroBridge, Profile
from neurobridge.core.bridge import AdaptedResponse
from neurobridge.integrations.openai import wrap as wrap_openai
from neurobridge.server.app import create_app
from neurobridge.server.config import ServerConfig


async def _collect_stream(bridge: NeuroBridge, message: str, user_id: str | None = None):
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


class _FakeDelta:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.delta = _FakeDelta(content)


class _FakeChunk:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeResponseChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeResponseChoice(content)]


class _MockOpenAICompletions:
    """Streams or returns a canned model response, like the real API."""

    MODEL_TEXT = "You must fix this ASAP! The deploy takes two steps. Retry afterwards."

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, *args, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream") is True:
            words = self.MODEL_TEXT.split(" ")
            for index in range(0, len(words), 2):
                yield _FakeChunk(" ".join(words[index : index + 2]) + " ")
        else:
            return _FakeResponse(self.MODEL_TEXT)


class _MockOpenAIChat:
    def __init__(self) -> None:
        self.completions = _MockOpenAICompletions()


class _MockOpenAIClient:
    def __init__(self) -> None:
        self.chat = _MockOpenAIChat()


def test_openai_wrapper_stream_calls_real_client_and_adapts() -> None:
    """Regression: with stream=True the wrapper never called the target client
    at all and streamed the adapted user prompt back instead of model output."""
    client = _MockOpenAIClient()
    wrapped = wrap_openai(client, profile=Profile.ANXIETY, config=Config(memory_backend="none"))

    user_message = "How do I deploy the service?"
    stream = wrapped.chat.completions.create(
        stream=True,
        messages=[{"role": "user", "content": user_message}],
    )
    contents = []
    for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            contents.append(text)

    # The real client must have been called exactly once, with the original
    # request arguments intact.
    assert len(client.chat.completions.calls) == 1
    assert client.chat.completions.calls[0]["stream"] is True

    assert contents
    combined = " ".join(contents).lower()
    # The adapted output reflects the MODEL's text, not the user prompt.
    assert "deploy takes" in combined
    assert "two steps" in combined
    assert user_message.lower() not in combined
    # Anxiety profile softening applied to the model output.
    assert "asap" not in combined
    assert "must" not in combined


def test_openai_wrapper_without_profile_warns_instead_of_blocking() -> None:
    """Regression: wrap() without a profile used to launch an interactive quiz
    on the first create() call, which hung any non-TTY caller on input()."""
    import warnings as _warnings

    client = _MockOpenAIClient()
    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        wrapped = wrap_openai(client, config=Config(memory_backend="none"))
        result = wrapped.chat.completions.create(messages=[{"role": "user", "content": "Hello."}])

    assert any("default" in str(w.message) for w in caught)
    # Non-streaming path still adapts the model response.
    assert result is not None
