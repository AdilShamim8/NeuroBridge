"""Day 8 LangChain integration examples for NeuroBridge."""

from dataclasses import dataclass

from neurobridge import Config, Profile
from neurobridge.integrations.langchain import (
    NeuroBridgeCallbackHandler,
    NeuroBridgeChain,
    NeuroBridgeOutputParser,
    NeuroBridgeRetriever,
)


class DemoLLM:
    """Simple stand-in LLM used for local example execution."""

    def invoke(self, prompt: str) -> str:
        return f"Model output: {prompt} It is critical and you must act ASAP."


@dataclass
class DemoDocument:
    page_content: str


class DemoRetriever:
    def get_relevant_documents(self, query: str):
        return [DemoDocument(page_content=f"Retrieved for {query}: urgent migration guidance.")]


def basic_output_parser_example() -> None:
    parser = NeuroBridgeOutputParser(profile=Profile.ANXIETY, config=Config(memory_backend="none"))
    adapted = parser.parse("This is critical and you must fix it ASAP.")
    print("[parser]", adapted)


def callback_handler_example() -> None:
    handler = NeuroBridgeCallbackHandler(profile=Profile.ANXIETY, config=Config(memory_backend="none"))

    class _Result:
        def __init__(self) -> None:
            self.generations = [[type("Gen", (), {"text": "URGENT! MUST act ASAP!"})()]]

    result = _Result()
    handler.on_llm_end(result)
    print("[callback]", result.generations[0][0].text)


def convenience_chain_example() -> None:
    chain = NeuroBridgeChain(
        llm=DemoLLM(),
        prompt="Answer this clearly: {query}",
        profile=Profile.ANXIETY,
        config=Config(memory_backend="none"),
    )
    print("[chain]", chain.run("How should I deploy safely?"))


def rag_retriever_example() -> None:
    retriever = NeuroBridgeRetriever(
        retriever=DemoRetriever(),
        profile=Profile.ANXIETY,
        config=Config(memory_backend="none"),
    )
    docs = retriever.get_relevant_documents("rollback")
    print("[retriever]", docs[0].page_content)


if __name__ == "__main__":
    basic_output_parser_example()
    callback_handler_example()
    convenience_chain_example()
    rag_retriever_example()
