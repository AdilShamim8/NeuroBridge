"""LangChain integration adapters for NeuroBridge.

Designed to work across langchain>=0.1.0 and >=0.2.0 import paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from neurobridge.core.bridge import Config, NeuroBridge
from neurobridge.core.profile import Profile

try:  # langchain>=0.2
    from langchain_core.output_parsers import BaseOutputParser  # type: ignore
except Exception:  # pragma: no cover
    try:  # langchain>=0.1
        from langchain.schema import BaseOutputParser  # type: ignore
    except Exception:  # pragma: no cover

        class BaseOutputParser:  # type: ignore
            def parse(self, text: str) -> str:
                return text


try:
    from langchain_core.callbacks.base import BaseCallbackHandler  # type: ignore
except Exception:  # pragma: no cover
    try:
        from langchain.callbacks.base import BaseCallbackHandler  # type: ignore
    except Exception:  # pragma: no cover

        class BaseCallbackHandler:  # type: ignore
            pass


try:
    from langchain.chains.base import Chain  # type: ignore
except Exception:  # pragma: no cover

    class Chain:  # type: ignore
        @property
        def input_keys(self) -> List[str]:
            return ["query"]

        @property
        def output_keys(self) -> List[str]:
            return ["text"]

        def __call__(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            return self._call(inputs)

        def _call(self, inputs: Dict[str, Any], run_manager: Any = None) -> Dict[str, Any]:
            raise NotImplementedError


class NeuroBridgeOutputParser(BaseOutputParser):
    """Adapt LLM output text with NeuroBridge before returning parsed output."""

    def __init__(self, profile: Profile = Profile.ADHD, config: Optional[Config] = None) -> None:
        bridge = NeuroBridge(config=config)
        bridge.set_profile(profile)
        object.__setattr__(self, "_bridge", bridge)

    @property
    def bridge(self) -> NeuroBridge:
        return object.__getattribute__(self, "_bridge")

    def parse(self, text: str) -> str:
        return self.bridge.adapt(text)

    def get_format_instructions(self) -> str:
        return "Return plain natural language text without tool annotations or non-text artifacts."


class NeuroBridgeCallbackHandler(BaseCallbackHandler):
    """Intercept LLM end events and adapt generated text in-place when possible."""

    def __init__(
        self,
        profile: Profile = Profile.ADHD,
        config: Optional[Config] = None,
        user_id: Optional[str] = None,
    ) -> None:
        self.bridge = NeuroBridge(config=config)
        self.bridge.set_profile(profile)
        self.user_id = user_id
        self.last_adapted_text: Optional[str] = None

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        _ = kwargs
        extracted = self._extract_text(response)
        if not extracted:
            return
        adapted = self.bridge.adapt(extracted)
        self.last_adapted_text = adapted
        self._inject_text(response, adapted)

    @staticmethod
    def _extract_text(response: Any) -> str:
        generations = getattr(response, "generations", None)
        if not generations:
            return ""
        first_group = generations[0] if isinstance(generations, Sequence) and generations else None
        if not first_group:
            return ""
        first_gen = first_group[0] if isinstance(first_group, Sequence) and first_group else None
        if first_gen is None:
            return ""
        text = getattr(first_gen, "text", None)
        return text if isinstance(text, str) else ""

    @staticmethod
    def _inject_text(response: Any, adapted_text: str) -> None:
        generations = getattr(response, "generations", None)
        if not generations:
            return
        try:
            generations[0][0].text = adapted_text
        except Exception:
            return


class NeuroBridgeChain(Chain):
    """Prebuilt prompt -> llm -> NeuroBridge parser chain."""

    def __init__(
        self,
        llm: Any,
        prompt: Optional[Any] = None,
        profile: Profile = Profile.ADHD,
        config: Optional[Config] = None,
    ) -> None:
        object.__setattr__(self, "_llm", llm)
        object.__setattr__(self, "_prompt", prompt)
        object.__setattr__(self, "_parser", NeuroBridgeOutputParser(profile=profile, config=config))

    @property
    def llm(self) -> Any:
        return object.__getattribute__(self, "_llm")

    @property
    def prompt(self) -> Optional[Any]:
        return object.__getattribute__(self, "_prompt")

    @property
    def parser(self) -> NeuroBridgeOutputParser:
        return object.__getattribute__(self, "_parser")

    @property
    def input_keys(self) -> List[str]:
        return ["query"]

    @property
    def output_keys(self) -> List[str]:
        return ["text"]

    def _call(self, inputs: Dict[str, Any], run_manager: Any = None) -> Dict[str, Any]:
        _ = run_manager
        query = str(inputs.get("query", ""))
        text = self.run(query)
        return {"text": text}

    def run(self, query: str, user_id: Optional[str] = None) -> str:
        rendered = self._render_prompt(query)
        raw = self._invoke_llm(rendered)
        return self.parser.parse(raw if user_id is None else raw)

    def _render_prompt(self, query: str) -> str:
        if self.prompt is None:
            return query
        if hasattr(self.prompt, "format"):
            try:
                return str(self.prompt.format(query=query))
            except Exception:
                return str(self.prompt.format(input=query))
        if callable(self.prompt):
            return str(self.prompt(query))
        return f"{self.prompt}\n{query}"

    def _invoke_llm(self, text: str) -> str:
        if hasattr(self.llm, "invoke"):
            result = self.llm.invoke(text)
            return self._extract_text(result)
        if callable(self.llm):
            result = self.llm(text)
            return self._extract_text(result)
        raise TypeError("llm must be callable or expose invoke()")

    @staticmethod
    def _extract_text(result: Any) -> str:
        if isinstance(result, str):
            return result
        content = getattr(result, "content", None)
        if isinstance(content, str):
            return content
        text = getattr(result, "text", None)
        if isinstance(text, str):
            return text
        return str(result)


@dataclass
class NeuroBridgeRetriever:
    """Wrap a retriever and adapt each document's text before returning."""

    retriever: Any
    profile: Profile = Profile.ADHD
    config: Optional[Config] = None

    def __post_init__(self) -> None:
        self.bridge = NeuroBridge(config=self.config)
        self.bridge.set_profile(self.profile)

    def get_relevant_documents(self, query: str) -> List[Any]:
        docs = self.retriever.get_relevant_documents(query)
        return self._adapt_documents(docs)

    async def aget_relevant_documents(self, query: str) -> List[Any]:
        if hasattr(self.retriever, "aget_relevant_documents"):
            docs = await self.retriever.aget_relevant_documents(query)
        else:
            docs = self.retriever.get_relevant_documents(query)
        return self._adapt_documents(docs)

    def _adapt_documents(self, docs: Sequence[Any]) -> List[Any]:
        adapted_docs: List[Any] = []
        for doc in docs:
            content = getattr(doc, "page_content", None)
            if isinstance(content, str):
                try:
                    doc.page_content = self.bridge.adapt(content)
                except Exception:
                    adapted_docs.append(doc)
                    continue
            adapted_docs.append(doc)
        return adapted_docs
