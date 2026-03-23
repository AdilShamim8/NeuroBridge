"""Day 8 tests for LangChain integration layer."""

from dataclasses import dataclass

from neurobridge import Config, Profile
from neurobridge.integrations.langchain import (
    NeuroBridgeCallbackHandler,
    NeuroBridgeChain,
    NeuroBridgeOutputParser,
    NeuroBridgeRetriever,
)


def test_output_parser_adapts_text() -> None:
    parser = NeuroBridgeOutputParser(profile=Profile.ANXIETY, config=Config(memory_backend="none"))
    out = parser.parse("This is critical and you must fix it ASAP.")
    lowered = out.lower()
    assert "critical" not in lowered
    assert "must" not in lowered
    assert "asap" not in lowered


@dataclass
class _MockGeneration:
    text: str


@dataclass
class _MockLLMResult:
    generations: list[list[_MockGeneration]]


def test_callback_handler_intercepts_and_rewrites_response() -> None:
    handler = NeuroBridgeCallbackHandler(
        profile=Profile.ANXIETY, config=Config(memory_backend="none")
    )
    response = _MockLLMResult(
        generations=[[_MockGeneration(text="URGENT! You MUST do this ASAP!")]]
    )
    handler.on_llm_end(response)
    assert handler.last_adapted_text is not None
    assert "asap" not in response.generations[0][0].text.lower()


class _MockLLM:
    def invoke(self, prompt: str) -> str:
        _ = prompt
        return "This is critical and you must update the deployment ASAP."


def test_neurobridge_chain_end_to_end_with_mocked_llm() -> None:
    chain = NeuroBridgeChain(
        llm=_MockLLM(),
        prompt="Answer clearly:\n{query}",
        profile=Profile.ANXIETY,
        config=Config(memory_backend="none"),
    )
    output = chain.run("How should we deploy this safely?")
    lowered = output.lower()
    assert "asap" not in lowered
    assert "must" not in lowered


@dataclass
class _Doc:
    page_content: str


class _MockRetriever:
    def get_relevant_documents(self, query: str):
        _ = query
        return [_Doc(page_content="This is critical and must be done ASAP.")]


def test_retriever_wraps_and_adapts_documents() -> None:
    retriever = NeuroBridgeRetriever(
        retriever=_MockRetriever(),
        profile=Profile.ANXIETY,
        config=Config(memory_backend="none"),
    )
    docs = retriever.get_relevant_documents("deploy")
    assert docs
    assert "asap" not in docs[0].page_content.lower()
