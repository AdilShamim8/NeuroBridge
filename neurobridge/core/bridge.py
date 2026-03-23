"""Main NeuroBridge orchestration class."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
import os
import re
from time import perf_counter
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterator,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Union,
    cast,
)
from uuid import uuid4

from neurobridge.exceptions import LLMClientError, MemoryBackendError, ProfileNotSetError
from neurobridge.core.memory import (
    BaseMemoryStore,
    FeedbackAnalyser,
    ProfileAdjustments,
    RedisMemoryStore,
    SQLiteMemoryStore,
    create_feedback_record,
)
from neurobridge.core.profile import CustomProfile, Profile, ProfileConfig, get_profile_config
from neurobridge.core.quiz import QuizResult
from neurobridge.core.transform import TransformPipeline
from neurobridge.core.validators import validate_text_input, validate_user_id

_SENTENCE_END_RE = re.compile(r"([.!?])")
_INCOMPLETE_NUMBER_TAIL_RE = re.compile(r"(?:\$|£|€)?\d[\d,]*\.?$")


@dataclass(slots=True)
class Config:
    """Runtime configuration for NeuroBridge."""

    memory_backend: Literal["sqlite", "redis", "none"] = "sqlite"
    memory_path: str = "~/.neurobridge/memory.db"
    cache_profiles: bool = True
    feedback_learning: bool = True
    output_format: Literal["markdown", "html", "plain", "json", "tts"] = "markdown"
    max_chunk_words: int = 80
    debug: bool = False
    auto_adjust_after: int = 10
    redis_url: str = "redis://localhost:6379/0"
    max_text_length: int = 50_000

    @classmethod
    def from_env(cls) -> "Config":
        """Build runtime configuration from NEUROBRIDGE_* environment variables."""

        def to_bool(raw: str, default: bool) -> bool:
            value = (raw or "").strip().lower()
            if value in {"1", "true", "yes", "on"}:
                return True
            if value in {"0", "false", "no", "off"}:
                return False
            return default

        memory_backend = os.getenv("NEUROBRIDGE_MEMORY_BACKEND", "sqlite").strip().lower()
        if memory_backend not in {"sqlite", "redis", "none"}:
            memory_backend = "sqlite"

        output_format = os.getenv("NEUROBRIDGE_OUTPUT_FORMAT", "markdown").strip().lower()
        if output_format not in {"markdown", "html", "plain", "json", "tts"}:
            output_format = "markdown"

        def int_from_env(name: str, default: int) -> int:
            raw = os.getenv(name)
            if raw is None:
                return default
            try:
                return int(raw)
            except ValueError:
                return default

        return cls(
            memory_backend=cast(Literal["sqlite", "redis", "none"], memory_backend),
            memory_path=os.getenv("NEUROBRIDGE_MEMORY_PATH", "~/.neurobridge/memory.db"),
            cache_profiles=to_bool(os.getenv("NEUROBRIDGE_CACHE_PROFILES", "true"), True),
            feedback_learning=to_bool(os.getenv("NEUROBRIDGE_FEEDBACK_LEARNING", "true"), True),
            output_format=cast(
                Literal["markdown", "html", "plain", "json", "tts"],
                output_format,
            ),
            max_chunk_words=max(1, int_from_env("NEUROBRIDGE_MAX_CHUNK_WORDS", 80)),
            debug=to_bool(os.getenv("NEUROBRIDGE_DEBUG", "false"), False),
            auto_adjust_after=max(1, int_from_env("NEUROBRIDGE_AUTO_ADJUST_AFTER", 10)),
            redis_url=os.getenv("NEUROBRIDGE_REDIS_URL", "redis://localhost:6379/0"),
            max_text_length=max(1, int_from_env("NEUROBRIDGE_MAX_TEXT_LENGTH", 50_000)),
        )


@dataclass(slots=True)
class AdaptedResponse:
    """Container for raw and adapted model output."""

    raw_text: str
    adapted_text: str
    profile: Union[Profile, str]
    interaction_id: str
    modules_run: List[str]
    processing_ms: float
    metadata: Dict[str, Any]


class NeuroBridge:
    """Adapts LLM output to fit cognitive profile preferences."""

    def __init__(self, llm_client: Any = None, config: Optional[Config] = None) -> None:
        self.llm_client = llm_client
        self.config = config or Config.from_env()
        self._active_profile: Union[Profile, str] = Profile.ADHD
        self._profile_config: ProfileConfig = get_profile_config(Profile.ADHD)
        self._profile_explicit = True
        self._pipeline = TransformPipeline(
            profile=self._profile_config,
            debug=self.config.debug,
            debug_callback=self._debug_log,
        )
        self._memory_store = self._build_memory_store(self.config)
        self._feedback_analyser = FeedbackAnalyser()

    def _debug_log(self, message: str) -> None:
        if not self.config.debug:
            return
        try:
            from rich.console import Console
            from rich.panel import Panel

            console = Console()
            console.print(Panel(message, border_style="cyan", title="NeuroBridge Debug"))
        except Exception:
            print(f"[NeuroBridge debug] {message}")

    @property
    def memory_store(self) -> Optional[BaseMemoryStore]:
        """Return configured memory backend, if available."""
        return self._memory_store

    def set_debug(self, enabled: bool) -> None:
        """Enable or disable debug logging at runtime."""
        self.config.debug = bool(enabled)
        self._pipeline.debug = self.config.debug
        self._pipeline.debug_callback = self._debug_log if self.config.debug else None

    def _build_memory_store(self, config: Config) -> Optional[BaseMemoryStore]:
        if config.memory_backend == "none":
            return None
        if config.memory_backend == "sqlite":
            return SQLiteMemoryStore(config.memory_path)
        if config.memory_backend == "redis":
            try:
                return RedisMemoryStore(config.redis_url)
            except Exception as exc:
                raise MemoryBackendError(f"Cannot connect to Redis: {exc}") from exc
        raise ValueError(f"Unsupported memory backend: {config.memory_backend}")

    @property
    def profile(self) -> Union[Profile, str]:
        """Return the active profile identifier."""
        return self._active_profile

    def set_profile(self, profile: Union[Profile, CustomProfile, QuizResult]) -> None:
        """Set active profile from built-in or custom configuration."""
        if isinstance(profile, QuizResult):
            self._active_profile = profile.primary_profile
            self._profile_config = profile.recommended_config
            self._profile_explicit = True
        elif isinstance(profile, Profile):
            self._active_profile = profile
            self._profile_config = get_profile_config(profile)
            self._profile_explicit = True
        elif isinstance(profile, CustomProfile):
            profile.validate()
            self._active_profile = Profile.CUSTOM
            self._profile_config = profile
            self._profile_explicit = True
        else:
            raise TypeError("profile must be a Profile, CustomProfile, or QuizResult")

        self._pipeline = TransformPipeline(
            profile=self._profile_config,
            debug=self.config.debug,
            debug_callback=self._debug_log,
        )

    def adapt(self, text: str) -> str:
        """Run the transform pipeline over plain text."""
        validate_text_input(text, max_length=self.config.max_text_length)
        if not text.strip():
            return ""
        return self._pipeline.transform(text)

    async def aadapt(self, text: str) -> str:
        """Async wrapper for adapt() to support concurrent adaptation workloads."""
        return await asyncio.to_thread(self.adapt, text)

    def cache_stats(self) -> Dict[str, float]:
        """Expose pipeline cache statistics for observability and tuning."""
        return self._pipeline.cache_stats()

    def chat(self, message: str, user_id: Optional[str] = None, **kwargs: Any) -> AdaptedResponse:
        """Return an adapted response.

        Day 1 uses a safe scaffold implementation:
        - With no client, input message is used as raw text.
        - With a client implementing chat(message=...), that result is used.
        - Otherwise, input is echoed and adapted.
        """
        validate_text_input(message, max_length=self.config.max_text_length, field="message")
        if not message.strip():
            raise ValueError("message must be a non-empty string")
        if user_id is not None:
            validate_user_id(user_id)
        if not self._profile_explicit and not user_id:
            raise ProfileNotSetError()

        if self.config.debug:
            self._debug_log(f"Profile config: {self._profile_config}")
            cache = self.cache_stats()
            self._debug_log(
                "Cache stats: "
                f"hits={int(cache['hits'])}, misses={int(cache['misses'])}, "
                f"evictions={int(cache['evictions'])}, hit_rate={cache['hit_rate']:.2%}"
            )

        if user_id and self._memory_store is not None:
            stored_profile = self._memory_store.load_profile(user_id)
            if stored_profile is not None:
                self._profile_config = stored_profile
                self._active_profile = Profile.CUSTOM
                self._pipeline = TransformPipeline(
                    profile=self._profile_config,
                    debug=self.config.debug,
                    debug_callback=self._debug_log,
                )

        raw_text = message
        if self.llm_client is not None and hasattr(self.llm_client, "chat"):
            try:
                response = self.llm_client.chat(message=message, **kwargs)
                raw_text = str(response)
            except Exception as exc:
                raise LLMClientError(str(exc)) from exc

        start = perf_counter()
        adapted_text = self.adapt(raw_text)
        processing_ms = (perf_counter() - start) * 1000
        if user_id and self._memory_store is not None:
            self._memory_store.save_profile(user_id, self._profile_config)
            interaction_count = self._memory_store.increment_interaction(user_id)
            if (
                self.config.feedback_learning
                and self.config.auto_adjust_after > 0
                and interaction_count % self.config.auto_adjust_after == 0
            ):
                adjustments = self._feedback_analyser.analyse_feedback(user_id, self._memory_store)
                self._apply_adjustments(adjustments)
                self._memory_store.save_profile(user_id, self._profile_config)

        return AdaptedResponse(
            raw_text=raw_text,
            adapted_text=adapted_text,
            profile=self._active_profile,
            interaction_id=str(uuid4()),
            modules_run=[entry.module for entry in self._pipeline.last_run],
            processing_ms=processing_ms,
            metadata={
                "memory_backend": self.config.memory_backend,
                "output_format": self.config.output_format,
                "cache": self.cache_stats(),
            },
        )

    async def achat(
        self,
        message: str,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> AdaptedResponse:
        """Async wrapper for chat() enabling parallel request handling."""
        return await asyncio.to_thread(self.chat, message, user_id=user_id, **kwargs)

    def submit_feedback(
        self,
        original_text: str,
        adapted_text: str,
        user_edit: str,
        user_id: str,
    ) -> None:
        """Persist explicit user feedback for adaptive profile tuning."""
        if self._memory_store is None:
            return
        validate_user_id(user_id)
        validate_text_input(
            original_text, max_length=self.config.max_text_length, field="original_text"
        )
        validate_text_input(
            adapted_text, max_length=self.config.max_text_length, field="adapted_text"
        )
        validate_text_input(user_edit, max_length=self.config.max_text_length, field="user_edit")
        record = create_feedback_record(
            user_id=user_id,
            original_text=original_text,
            adapted_text=adapted_text,
            user_edit=user_edit,
        )
        self._memory_store.save_feedback(record)

    def delete_user_data(self, user_id: str) -> None:
        """Delete all persisted data for a user from configured memory backend."""
        validate_user_id(user_id)
        if self._memory_store is None:
            return
        self._memory_store.clear_user_data(user_id)

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all stored profile and feedback data for a user."""
        validate_user_id(user_id)
        if self._memory_store is None:
            return {"user_id": user_id, "memory_backend": "none", "profile": None, "feedback": []}

        profile = self._memory_store.load_profile(user_id)
        feedback = self._memory_store.get_feedback(user_id)
        interactions = self._memory_store.get_interaction_count(user_id)
        return {
            "user_id": user_id,
            "memory_backend": self.config.memory_backend,
            "profile": asdict(profile) if profile is not None else None,
            "feedback": [asdict(record) for record in feedback],
            "interaction_count": interactions,
        }

    def _apply_adjustments(self, adjustments: ProfileAdjustments) -> None:
        updated = ProfileConfig(
            chunk_size=max(1, self._profile_config.chunk_size + adjustments.chunk_size_delta),
            tone=adjustments.tone or self._profile_config.tone,
            ambiguity_resolution=self._profile_config.ambiguity_resolution,
            number_format=self._profile_config.number_format,
            leading_style=self._profile_config.leading_style,
            reading_level=max(1, self._profile_config.reading_level),
            max_sentence_words=max(
                6, self._profile_config.max_sentence_words + adjustments.max_sentence_words_delta
            ),
        )
        updated.validate()
        self._profile_config = updated
        self._active_profile = Profile.CUSTOM
        self._pipeline = TransformPipeline(
            profile=self._profile_config,
            debug=self.config.debug,
            debug_callback=self._debug_log,
        )

    async def chat_stream(
        self,
        message: str,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Union[str, AdaptedResponse], None]:
        """Yield adapted chunks as sentence boundaries are reached, then final response."""
        validate_text_input(message, max_length=self.config.max_text_length, field="message")
        if not message.strip():
            raise ValueError("message must be a non-empty string")
        if user_id is not None:
            validate_user_id(user_id)

        if user_id and self._memory_store is not None:
            stored_profile = self._memory_store.load_profile(user_id)
            if stored_profile is not None:
                self._profile_config = stored_profile
                self._active_profile = Profile.CUSTOM
                self._pipeline = TransformPipeline(
                    profile=self._profile_config,
                    debug=self.config.debug,
                    debug_callback=self._debug_log,
                )

        raw_collected: List[str] = []
        adapted_collected: List[str] = []
        sentence_buffer = ""
        chunk_sentences: List[str] = []
        start = perf_counter()

        async for incoming in self._iterate_source_chunks(message=message, **kwargs):
            if not incoming:
                continue
            raw_collected.append(incoming)
            sentence_buffer += incoming

            complete, sentence_buffer = self._extract_complete_sentences(sentence_buffer)
            for sentence in complete:
                if self._has_incomplete_numeric_tail(sentence):
                    sentence_buffer = sentence + sentence_buffer
                    continue

                chunk_sentences.append(sentence)
                if len(chunk_sentences) >= max(1, self._profile_config.chunk_size):
                    adapted_chunk = self._adapt_stream_chunk(chunk_sentences)
                    if adapted_chunk:
                        adapted_collected.append(adapted_chunk)
                        yield adapted_chunk
                    chunk_sentences = []

        if sentence_buffer.strip():
            chunk_sentences.append(sentence_buffer.strip())
        if chunk_sentences:
            adapted_chunk = self._adapt_stream_chunk(chunk_sentences)
            if adapted_chunk:
                adapted_collected.append(adapted_chunk)
                yield adapted_chunk

        raw_text = "".join(raw_collected).strip() or message
        adapted_text = "\n\n".join([part for part in adapted_collected if part.strip()]).strip()
        if not adapted_text:
            adapted_text = self.adapt(raw_text)

        processing_ms = (perf_counter() - start) * 1000
        if user_id and self._memory_store is not None:
            self._memory_store.save_profile(user_id, self._profile_config)
            interaction_count = self._memory_store.increment_interaction(user_id)
            if (
                self.config.feedback_learning
                and self.config.auto_adjust_after > 0
                and interaction_count % self.config.auto_adjust_after == 0
            ):
                adjustments = self._feedback_analyser.analyse_feedback(user_id, self._memory_store)
                self._apply_adjustments(adjustments)
                self._memory_store.save_profile(user_id, self._profile_config)

        yield AdaptedResponse(
            raw_text=raw_text,
            adapted_text=adapted_text,
            profile=self._active_profile,
            interaction_id=str(uuid4()),
            modules_run=self._stream_modules_run(),
            processing_ms=processing_ms,
            metadata={
                "memory_backend": self.config.memory_backend,
                "output_format": self.config.output_format,
                "streaming": True,
                "cache": self.cache_stats(),
            },
        )

    def close(self) -> None:
        """Release memory backend resources when supported."""
        store = self._memory_store
        if store is None:
            return
        close = getattr(store, "close", None)
        if callable(close):
            close()

    async def aclose(self) -> None:
        """Async wrapper for close()."""
        await asyncio.to_thread(self.close)

    async def __aenter__(self) -> "NeuroBridge":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.aclose()

    async def _iterate_source_chunks(self, message: str, **kwargs: Any) -> AsyncIterator[str]:
        if self.llm_client is None:
            for token in self._tokenize_stream_input(message):
                yield token
            return

        if hasattr(self.llm_client, "chat_stream"):
            try:
                stream_obj = self.llm_client.chat_stream(message=message, **kwargs)
            except Exception as exc:
                raise LLMClientError(str(exc)) from exc
            if hasattr(stream_obj, "__aiter__"):
                async for piece in stream_obj:
                    yield self._extract_chunk_text(piece)
            else:
                for piece in stream_obj:
                    yield self._extract_chunk_text(piece)
            return

        if hasattr(self.llm_client, "chat"):
            try:
                response = self.llm_client.chat(message=message, **kwargs)
            except Exception as exc:
                raise LLMClientError(str(exc)) from exc
            text = str(response)
            for token in self._tokenize_stream_input(text):
                yield token
            return

        for token in self._tokenize_stream_input(message):
            yield token

    @staticmethod
    def _extract_chunk_text(piece: Any) -> str:
        if isinstance(piece, str):
            return piece
        choices = getattr(piece, "choices", None)
        if choices:
            first = choices[0]
            delta = getattr(first, "delta", None)
            if delta is not None:
                content = getattr(delta, "content", None)
                if isinstance(content, str):
                    return content
        text = getattr(piece, "text", None)
        if isinstance(text, str):
            return text
        return str(piece)

    @staticmethod
    def _tokenize_stream_input(text: str) -> Iterable[str]:
        # Preserve spaces by streaming words plus trailing space where present.
        tokens = re.findall(r"\S+\s*", text)
        if not tokens and text:
            return [text]
        return tokens

    @staticmethod
    def _extract_complete_sentences(buffer: str) -> tuple[List[str], str]:
        parts = _SENTENCE_END_RE.split(buffer)
        sentences: List[str] = []
        current = ""
        for index, part in enumerate(parts):
            if index % 2 == 0:
                current += part
            else:
                current += part
                sentence = current.strip()
                if sentence:
                    sentences.append(sentence)
                current = ""
        return sentences, current

    @staticmethod
    def _has_incomplete_numeric_tail(sentence: str) -> bool:
        return bool(_INCOMPLETE_NUMBER_TAIL_RE.search(sentence.strip()))

    def _adapt_stream_chunk(self, sentences: List[str]) -> str:
        text = " ".join(s.strip() for s in sentences if s.strip())
        if not text:
            return ""

        output = text
        for module in self._pipeline.modules:
            if not getattr(module, "enabled", True):
                continue
            if getattr(module, "name", "") == "priority_reorderer":
                continue
            output = module.apply(output, self._profile_config)
        return output.strip()

    def _stream_modules_run(self) -> List[str]:
        names: List[str] = []
        for module in self._pipeline.modules:
            if not getattr(module, "enabled", True):
                continue
            if getattr(module, "name", "") == "priority_reorderer":
                continue
            names.append(module.name)
        return names
