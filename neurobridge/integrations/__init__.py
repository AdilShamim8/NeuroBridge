"""LLM integration adapters for NeuroBridge."""

from neurobridge.integrations.anthropic import wrap as wrap_anthropic
from neurobridge.integrations.huggingface import (
    NeuroBridgePipeline,
    NeuroBridgeTransformersAdapter,
)
from neurobridge.integrations.langchain import (
    NeuroBridgeCallbackHandler,
    NeuroBridgeChain,
    NeuroBridgeOutputParser,
    NeuroBridgeRetriever,
)
from neurobridge.integrations.openai import wrap as wrap_openai

__all__ = [
    "NeuroBridgeCallbackHandler",
    "NeuroBridgeChain",
    "NeuroBridgeOutputParser",
    "NeuroBridgePipeline",
    "NeuroBridgeRetriever",
    "NeuroBridgeTransformersAdapter",
    "wrap_anthropic",
    "wrap_openai",
]
