"""Anthropic client integration for NeuroBridge adaptation."""

from __future__ import annotations

from typing import Any, Optional

from neurobridge.core.bridge import Config, NeuroBridge
from neurobridge.core.profile import Profile
from neurobridge.core.quiz import ProfileQuiz


class _AnthropicMessagesWrapper:
    def __init__(self, target: Any, bridge: NeuroBridge, parent: "_AnthropicWrappedClient") -> None:
        self.target = target
        self.bridge = bridge
        self.parent = parent

    def create(self, *args: Any, **kwargs: Any) -> Any:
        if self.parent.auto_quiz and not self.parent.quiz_done:
            quiz_profile = ProfileQuiz.run(user_id=kwargs.get("user_id"))
            self.bridge.set_profile(quiz_profile)
            self.parent.quiz_done = True

        response = self.target.create(*args, **kwargs)
        return self._adapt_response(response)

    def _adapt_response(self, response: Any) -> Any:
        content = getattr(response, "content", None)
        if isinstance(content, list) and content:
            first = content[0]
            text = getattr(first, "text", None)
            if isinstance(text, str) and text.strip():
                first.text = self.bridge.adapt(text)
            return response

        text_attr = getattr(response, "text", None)
        if isinstance(text_attr, str) and text_attr.strip():
            response.text = self.bridge.adapt(text_attr)
        return response


class _AnthropicWrappedClient:
    def __init__(self, client: Any, bridge: NeuroBridge, auto_quiz: bool = False) -> None:
        self.client = client
        self.bridge = bridge
        self.auto_quiz = auto_quiz
        self.quiz_done = False
        self._messages_wrapper = _AnthropicMessagesWrapper(
            target=self.client.messages,
            bridge=self.bridge,
            parent=self,
        )

    @property
    def messages(self) -> _AnthropicMessagesWrapper:
        return self._messages_wrapper

    def __getattr__(self, name: str) -> Any:
        return getattr(self.client, name)


def wrap(client: Any, profile: Optional[Profile] = None, config: Optional[Config] = None) -> Any:
    """Wrap an Anthropic client and adapt text in messages.create() responses."""
    bridge = NeuroBridge(llm_client=None, config=config)
    auto_quiz = profile is None
    if profile is not None:
        bridge.set_profile(profile)
    return _AnthropicWrappedClient(client=client, bridge=bridge, auto_quiz=auto_quiz)
