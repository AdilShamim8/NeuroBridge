"""NeuroBridge package public API."""

import os

from neurobridge.core.bridge import Config, NeuroBridge
from neurobridge.core.profile import CustomProfile, Profile
from neurobridge.core.quiz import ProfileQuiz
from neurobridge.exceptions import (
    LLMClientError,
    MemoryBackendError,
    NeuroBridgeError,
    ProfileNotSetError,
    TransformError,
)


def set_debug(enabled: bool) -> None:
    """Package-level convenience for enabling debug mode via environment variable."""
    os.environ["NEUROBRIDGE_DEBUG"] = "true" if enabled else "false"


__all__ = [
    "NeuroBridge",
    "Profile",
    "CustomProfile",
    "Config",
    "ProfileQuiz",
    "set_debug",
    "NeuroBridgeError",
    "ProfileNotSetError",
    "LLMClientError",
    "TransformError",
    "MemoryBackendError",
]
