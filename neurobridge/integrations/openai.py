"""OpenAI client integration for NeuroBridge adaptation."""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from typing import Any

from neurobridge.core.bridge import Config, NeuroBridge
from neurobridge.core.profile import Profile

_SENTENCE_END_RE = re.compile(r"([.!?])")


class _ChatCompletionsWrapper:
    """Wrap OpenAI chat completions endpoint and adapt returned message content."""

    def __init__(self, target: Any, bridge: NeuroBridge, parent: _OpenAIWrappedClient) -> None:
        self.target = target
        self.bridge = bridge
        self.parent = parent

    def create(self, *args: Any, **kwargs: Any) -> Any:
        # Call the real client first in both modes: adaptation must never
        # replace the model call, only post-process its output.
        if kwargs.get("stream") is True:
            stream_obj = self.target.create(*args, **kwargs)
            return _AdaptingStreamIterator(stream_obj, self.bridge)

        response = self.target.create(*args, **kwargs)
        return self._adapt_response(response)

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
                message.content = adapted
            return response
        except Exception as exc:  # noqa: BLE001 - client call must survive adaptation bugs
            # Adaptation must never break the client call, but failing silently hides
            # real problems from users, so surface it as a warning.
            warnings.warn(
                f"NeuroBridge adaptation failed, returning unadapted response: {exc}",
                UserWarning,
                stacklevel=2,
            )
            return response


class _OpenAIChatWrapper:
    """Wrap OpenAI chat namespace while preserving unknown attributes."""

    def __init__(self, target: Any, bridge: NeuroBridge, parent: _OpenAIWrappedClient) -> None:
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
    """Thin wrapper that preserves client surface while intercepting chat completions."""

    def __init__(self, client: Any, bridge: NeuroBridge) -> None:
        self.client = client
        self.bridge = bridge
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


def _extract_delta_text(piece: Any) -> str:
    """Extract the text delta from an OpenAI-shaped streaming chunk."""
    if isinstance(piece, str):
        return piece
    choices = getattr(piece, "choices", None)
    if choices:
        delta = getattr(choices[0], "delta", None)
        if delta is not None:
            content = getattr(delta, "content", None)
            if isinstance(content, str):
                return content
    text = getattr(piece, "text", None)
    if isinstance(text, str):
        return text
    return ""


class _AdaptingStreamIterator:
    """Iterate a real model stream and yield adapted chunks at sentence boundaries.

    The underlying client stream is consumed as-is; completed sentences are
    buffered and adapted in groups, so consumers receive the same adaptation
    quality as the non-streaming path without waiting for the full response.
    """

    def __init__(self, stream_obj: Any, bridge: NeuroBridge) -> None:
        self._stream = iter(stream_obj)
        self._bridge = bridge
        self._sentence_buffer = ""
        self._pending: list[str] = []

    def __iter__(self):
        return self

    def __next__(self) -> _StreamingChunk:
        while not self._pending:
            try:
                piece = next(self._stream)
            except StopIteration as exc:
                self._flush_remainder()
                if not self._pending:
                    raise StopIteration from exc
                break
            self._sentence_buffer += _extract_delta_text(piece)
            self._harvest_complete_sentences()

        text = self._pending.pop(0)
        return _StreamingChunk(choices=[_StreamingChoice(delta=_StreamingDelta(content=text))])

    def _harvest_complete_sentences(self) -> None:
        parts = _SENTENCE_END_RE.split(self._sentence_buffer)
        complete: list[str] = []
        remainder = ""
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
        remainder = current
        if not complete:
            return
        self._sentence_buffer = remainder
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


def wrap(client: Any, profile: Profile | None = None, config: Config | None = None) -> Any:
    """Return a wrapped OpenAI-compatible client.

    Both streaming and non-streaming ``chat.completions.create`` calls go to the
    real client first; NeuroBridge adapts the returned content afterwards.

    When ``profile`` is omitted the bridge default (ADHD) is used. Profile
    selection is explicit by design: earlier versions launched an interactive
    quiz on the first call, which blocked non-TTY callers such as servers,
    notebooks, and cron jobs on ``input()``. Run ``neurobridge quiz`` on the
    command line to pick a profile interactively.
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
    return _OpenAIWrappedClient(client=client, bridge=bridge)
