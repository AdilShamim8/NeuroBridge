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

    def create(self, *args, **kwargs):  # noqa: ANN002, ANN003
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
