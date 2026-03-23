"""Custom exception hierarchy for NeuroBridge."""

from __future__ import annotations


class NeuroBridgeError(Exception):
    """Base NeuroBridge exception with actionable suggestion metadata."""

    def __init__(self, message: str, suggestion: str = "") -> None:
        super().__init__(message)
        self.suggestion = suggestion


class ProfileNotSetError(NeuroBridgeError):
    def __init__(self, message: str = "Call set_profile() before using chat()") -> None:
        super().__init__(
            message,
            suggestion="Set a built-in profile via set_profile(Profile.ADHD) or run ProfileQuiz first.",
        )


class LLMClientError(NeuroBridgeError):
    def __init__(self, message: str) -> None:
        super().__init__(
            f"LLM client returned an error: {message}",
            suggestion="Verify API credentials, request schema, and network connectivity.",
        )


class TransformError(NeuroBridgeError):
    def __init__(self, module_name: str, message: str) -> None:
        super().__init__(
            f"Transform module {module_name} failed: {message}",
            suggestion="Disable the module temporarily or inspect input text and module logic.",
        )


class MemoryBackendError(NeuroBridgeError):
    def __init__(self, message: str = "Cannot connect to Redis") -> None:
        super().__init__(
            message,
            suggestion="Check memory backend configuration and service availability.",
        )
