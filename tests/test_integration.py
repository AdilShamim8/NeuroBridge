"""Day 7 integration tests for wrappers and persisted memory behavior."""

from dataclasses import dataclass

from neurobridge import Config, NeuroBridge, Profile
from neurobridge.integrations.openai import wrap


@dataclass
class _MockMessage:
    content: str


@dataclass
class _MockChoice:
    message: _MockMessage


@dataclass
class _MockResponse:
    choices: list[_MockChoice]


class _MockChatCompletions:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, *args, **kwargs):
        _ = args, kwargs
        return _MockResponse(choices=[_MockChoice(message=_MockMessage(content=self._text))])


class _MockChat:
    def __init__(self, text: str) -> None:
        self.completions = _MockChatCompletions(text)


class _MockOpenAIClient:
    def __init__(self, text: str) -> None:
        self.chat = _MockChat(text)


def test_openai_wrap_adapts_mocked_response_content() -> None:
    client = _MockOpenAIClient("This is critical and you must do this ASAP.")
    wrapped = wrap(client, profile=Profile.ANXIETY, config=Config(memory_backend="none"))

    response = wrapped.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": "Hi"}]
    )
    adapted = response.choices[0].message.content.lower()
    assert "asap" not in adapted
    assert "must" not in adapted


def test_memory_persists_profile_across_two_instances(tmp_path) -> None:
    db_path = tmp_path / "shared-memory.db"
    config = Config(memory_backend="sqlite", memory_path=str(db_path), auto_adjust_after=50)

    bridge_a = NeuroBridge(config=config)
    bridge_a.set_profile(Profile.DYSLEXIA)
    bridge_a.chat("First message", user_id="shared-user")

    bridge_b = NeuroBridge(config=config)
    response = bridge_b.chat("Second message", user_id="shared-user")

    assert response.profile == Profile.CUSTOM
    assert bridge_b.memory_store is not None
    loaded = bridge_b.memory_store.load_profile("shared-user")
    assert loaded is not None
    assert loaded.max_sentence_words == 12


class _AnthropicTextBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class _AnthropicContent:
    def __init__(self, text: str) -> None:
        self.content = [_AnthropicTextBlock(text)]


class _AnthropicDeltaText:
    def __init__(self, text: str) -> None:
        self.text = text


class _AnthropicStreamDelta:
    def __init__(self, text: str) -> None:
        self.delta = _AnthropicDeltaText(text)
        self.type = "content_block_delta"


class _AnthropicMockMessages:
    MODEL_TEXT = "You must act immediately! The pipeline has two stages. Then relax."

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, *args, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream") is True:
            return self._stream_fragments()
        return _AnthropicContent(self.MODEL_TEXT)

    @staticmethod
    def _stream_fragments():
        words = _AnthropicMockMessages.MODEL_TEXT.split(" ")
        for index in range(0, len(words), 2):
            yield _AnthropicStreamDelta(" ".join(words[index : index + 2]) + " ")


class _AnthropicMockClient:
    def __init__(self) -> None:
        self.messages = _AnthropicMockMessages()


def test_anthropic_wrapper_adapts_non_streaming_response() -> None:
    from neurobridge.core.bridge import Config
    from neurobridge.core.profile import Profile
    from neurobridge.integrations.anthropic import wrap as wrap_anthropic

    client = _AnthropicMockClient()
    wrapped = wrap_anthropic(client, profile=Profile.ANXIETY, config=Config(memory_backend="none"))
    response = wrapped.messages.create(
        messages=[{"role": "user", "content": "How do pipelines work?"}]
    )

    assert len(client.messages.calls) == 1
    text = response.content[0].text
    assert "immediately" not in text.lower()
    assert "two stages" in text


def test_anthropic_wrapper_streams_adapted_model_output() -> None:
    """Regression: stream=True returned Anthropic's raw Stream object, which
    has neither .content nor .text, so output passed through completely
    unadapted while appearing to work."""
    from neurobridge.core.bridge import Config
    from neurobridge.core.profile import Profile
    from neurobridge.integrations.anthropic import wrap as wrap_anthropic

    client = _AnthropicMockClient()
    wrapped = wrap_anthropic(client, profile=Profile.ANXIETY, config=Config(memory_backend="none"))

    chunks = []
    for event in wrapped.messages.create(
        stream=True,
        messages=[{"role": "user", "content": "How do pipelines work?"}],
    ):
        if event.delta.text:
            chunks.append(event.delta.text)

    assert len(client.messages.calls) == 1
    assert client.messages.calls[0]["stream"] is True
    combined = " ".join(chunks).lower()
    assert "two stages" in combined
    assert "immediately" not in combined


def test_anthropic_wrapper_without_profile_warns_not_blocks() -> None:
    """Regression: wrap() without a profile launched an interactive quiz
    (blocking input()) on the first create() call."""
    import warnings as _warnings

    from neurobridge.core.bridge import Config
    from neurobridge.integrations.anthropic import wrap as wrap_anthropic

    client = _AnthropicMockClient()
    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        wrapped = wrap_anthropic(client, config=Config(memory_backend="none"))
        wrapped.messages.create(messages=[{"role": "user", "content": "Hello."}])

    assert any("default" in str(w.message) for w in caught)
