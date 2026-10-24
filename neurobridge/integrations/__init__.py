"""LLM integration adapters for NeuroBridge."""

from neurobridge.integrations.anthropic import wrap as wrap_anthropic
from neurobridge.integrations.huggingface import NeuroBridgePipeline
from neurobridge.integrations.openai import wrap as wrap_openai

__all__ = ["NeuroBridgePipeline", "wrap_anthropic", "wrap_openai"]
