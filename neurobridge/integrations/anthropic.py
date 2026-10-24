"""Anthropic client integration for NeuroBridge adaptation."""

from __future__ import annotations

import warnings
from typing import Any

from neurobridge.core.bridge import Config, NeuroBridge
from neurobridge.core.profile import Profile


class _AnthropicMessagesWrapper:
    def __init__(self, target: Any, bridge: NeuroBridge) -> None:
        self.target = target
        self.bridge = bridge

    def create(self, *args: Any, **kwargs: Any) -> Any:
        response = self.target.create(*args, **kwargs)
        if kwargs.get("stream") is True:
            return _AnthropicAdaptingStream(response, self.bridge)
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


class _AnthropicAdaptingStream:
    """Iterate an Anthropic stream and adapt completed text blocks.

    Anthropic streams deliver events; text arrives as content_block_delta
    chunks whose delta carries a text field. Completed sentences are buffered
    and adapted in groups, mirroring the OpenAI streaming wrapper.
    """

    def __init__(self, stream_obj: Any, bridge: NeuroBridge) -> None:
        self._stream = iter(stream_obj)
        self._bridge = bridge
        self._sentence_buffer = ""
        self._pending: list[str] = []

    def __iter__(self):
        return self

    def __next__(self) -> Any:
        while not self._pending:
            try:
                event = next(self._stream)
            except StopIteration as exc:
                self._flush_remainder()
                if not self._pending:
                    raise StopIteration from exc
                break
            text = self._extract_event_text(event)
            if not text:
                continue
            self._sentence_buffer += text
            self._harvest_complete_sentences()

        adapted_text = self._pending.pop(0)

        # Re-emit the event shape consumers expect, with the adapted text.
        return _AdaptedDeltaEvent(adapted_text)

    @staticmethod
    def _extract_event_text(event: Any) -> str:
        if isinstance(event, str):
            return event
        delta = getattr(event, "delta", None)
        if delta is not None:
            text = getattr(delta, "text", None)
            if isinstance(text, str):
                return text
        text = getattr(event, "text", None)
        if isinstance(text, str):
            return text
        return ""

    def _harvest_complete_sentences(self) -> None:
        import re

        parts = re.split(r"([.!?])", self._sentence_buffer)
        complete: list[str] = []
        current = ""
        for index, part in enumerate(parts):
            if index % 2 == 0:
                current += part
            else:
                current += part
                sentence = current.strip()
                if sentence:
                    complete.append(sentence)
                current = ""
        self._sentence_buffer = current
        if not complete:
            return
        adapted = self._bridge.adapt_stream_chunk(complete)
        if adapted:
            self._pending.append(adapted)

    def _flush_remainder(self) -> None:
        tail = self._sentence_buffer.strip()
        self._sentence_buffer = ""
        if not tail:
            return
        adapted = self._bridge.adapt_stream_chunk([tail])
        if adapted:
            self._pending.append(adapted)


class _AdaptedDeltaEvent:
    """Minimal Anthropic-like delta event carrying adapted text."""

    def __init__(self, text: str) -> None:
        delta = type("Delta", (), {})()
        delta.text = text
        self.delta = delta
        self.type = "content_block_delta"


class _AnthropicWrappedClient:
    def __init__(self, client: Any, bridge: NeuroBridge) -> None:
        self.client = client
        self.bridge = bridge
        self._messages_wrapper = _AnthropicMessagesWrapper(
            target=self.client.messages,
            bridge=self.bridge,
        )

    @property
    def messages(self) -> _AnthropicMessagesWrapper:
        return self._messages_wrapper

    def __getattr__(self, name: str) -> Any:
        return getattr(self.client, name)


def wrap(client: Any, profile: Profile | None = None, config: Config | None = None) -> Any:
    """Wrap an Anthropic client and adapt text in messages.create() responses.

    Both streaming and non-streaming calls go to the real client first;
    NeuroBridge adapts the returned content afterwards. Note that Anthropic's
    API carries user identifiers under ``metadata.user_id`` (there is no
    top-level ``user_id`` parameter).

    When ``profile`` is omitted the bridge default (ADHD) is used. Earlier
    versions launched an interactive quiz on the first call, which blocked
    non-TTY callers on input(); profile selection is explicit by design.
    """
    bridge = NeuroBridge(llm_client=None, config=config)
    if profile is None:
        warnings.warn(
            "NeuroBridge wrap() called without a profile: using the default (ADHD). "
            "Pass profile=Profile.X to choose one, or run 'neurobridge quiz'.",
            UserWarning,
            stacklevel=2,
        )
    else:
        bridge.set_profile(profile)
    return _AnthropicWrappedClient(client=client, bridge=bridge)
