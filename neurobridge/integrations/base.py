"""Base integration interfaces for external LLM clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMAdapter(ABC):
    """Abstract adapter for wrapping third-party LLM clients."""

    @abstractmethod
    def chat(self, message: str, **kwargs: Any) -> Any:
        """Send a chat message and return raw model output."""
