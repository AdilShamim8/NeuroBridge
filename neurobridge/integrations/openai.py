"""OpenAI client integration for NeuroBridge adaptation."""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
from typing import Any, Optional

from neurobridge.core.bridge import Config, NeuroBridge
from neurobridge.core.profile import Profile
from neurobridge.core.quiz import ProfileQuiz


class _ChatCompletionsWrapper:
    """Wrap OpenAI chat completions endpoint and adapt returned message content."""

    def __init__(self, target: Any, bridge: NeuroBridge, parent: "_OpenAIWrappedClient") -> None:
        self.target = target
        self.bridge = bridge
        self.parent = parent

    def create(self, *args: Any, **kwargs: Any) -> Any:
        if self.parent.auto_quiz and not self.parent.quiz_done:
            quiz_profile = ProfileQuiz.run(user_id=kwargs.get("user"))
            self.bridge.set_profile(quiz_profile)
            self.parent.quiz_done = True

        if kwargs.get("stream") is True:
            message = self._extract_user_message(kwargs)
            return self._streaming_chunks(message=message, user_id=kwargs.get("user"))

        response = self.target.create(*args, **kwargs)
        return self._adapt_response(response)

    @staticmethod
    def _extract_user_message(kwargs: Any) -> str:
        messages = kwargs.get("messages")
        if isinstance(messages, list):
            for item in reversed(messages):
                if isinstance(item, dict) and item.get("role") == "user":
                    content = item.get("content")
                    if isinstance(content, str):
                        return content
        return ""

    def _streaming_chunks(self, message: str, user_id: Optional[str]):
        async_gen = self.bridge.chat_stream(message, user_id=user_id)
        return _BridgeStreamIterator(async_gen)

    def _adapt_response(self, response: Any) -> Any:
        try:
            choices = getattr(response, "choices", None)
            if not choices:
                return response
            first = choices[0]
            message = getattr(first, "message", None)
            if message is None:
                return response

            content = getattr(message, "content", None)
            if isinstance(content, str) and content.strip():
                adapted = self.bridge.adapt(content)
                setattr(message, "content", adapted)
            return response
        except Exception:
            return response


class _OpenAIChatWrapper:
    """Wrap OpenAI chat namespace while preserving unknown attributes."""

    def __init__(self, target: Any, bridge: NeuroBridge, parent: "_OpenAIWrappedClient") -> None:
        self.target = target
        self.bridge = bridge
        self.parent = parent
        self._completions_wrapper = _ChatCompletionsWrapper(
            target=self.target.completions,
            bridge=self.bridge,
            parent=self.parent,
        )

    @property
    def completions(self) -> _ChatCompletionsWrapper:
        return self._completions_wrapper

    def __getattr__(self, name: str) -> Any:
        return getattr(self.target, name)


class _OpenAIWrappedClient:
    """Thin wrapper that preserves client surface while intercepting chat completions.

    Full request interception is implemented in a later roadmap day.
    """

    def __init__(self, client: Any, bridge: NeuroBridge, auto_quiz: bool = False) -> None:
        self.client = client
        self.bridge = bridge
        self.auto_quiz = auto_quiz
        self.quiz_done = False
        self._chat_wrapper = _OpenAIChatWrapper(self.client.chat, self.bridge, self)

    @property
    def chat(self) -> _OpenAIChatWrapper:
        return self._chat_wrapper

    def __getattr__(self, name: str) -> Any:
        return getattr(self.client, name)


@dataclass
class _StreamingDelta:
    content: str


@dataclass
class _StreamingChoice:
    delta: _StreamingDelta


@dataclass
class _StreamingChunk:
    choices: list[_StreamingChoice]


class _BridgeStreamIterator:
    """Synchronous iterator wrapper around an async chat_stream generator."""

    def __init__(self, async_gen) -> None:  # type: ignore[no-untyped-def]
        self._async_gen = async_gen
        self._loop = asyncio.new_event_loop()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            item = self._loop.run_until_complete(self._async_gen.__anext__())
        except StopAsyncIteration as exc:
            self._loop.close()
            raise StopIteration from exc

        if isinstance(item, str):
            return _StreamingChunk(choices=[_StreamingChoice(delta=_StreamingDelta(content=item))])
        return _StreamingChunk(choices=[_StreamingChoice(delta=_StreamingDelta(content=""))])


def wrap(client: Any, profile: Optional[Profile] = None, config: Optional[Config] = None) -> Any:
    """Return a wrapped OpenAI-compatible client.

    If profile is not provided, the first call triggers ProfileQuiz to infer profile.
    """
    bridge = NeuroBridge(llm_client=None, config=config)
    auto_quiz = profile is None
    if profile is not None:
        bridge.set_profile(profile)
    return _OpenAIWrappedClient(client=client, bridge=bridge, auto_quiz=auto_quiz)
