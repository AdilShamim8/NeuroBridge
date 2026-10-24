"""Core building blocks for NeuroBridge."""

from neurobridge.core.bridge import AdaptedResponse, Config, NeuroBridge
from neurobridge.core.format_adapter import (
    BaseFormatAdapter,
    HTMLAdapter,
    JSONAdapter,
    MarkdownAdapter,
    PlainTextAdapter,
    TTSAdapter,
)
from neurobridge.core.profile import CustomProfile, Profile, ProfileConfig
from neurobridge.core.quiz import (
    ProfileBlender,
    ProfileQuiz,
    QuizEngine,
    QuizOption,
    QuizQuestion,
    QuizResult,
)

__all__ = [
    "AdaptedResponse",
    "BaseFormatAdapter",
    "Config",
    "CustomProfile",
    "HTMLAdapter",
    "JSONAdapter",
    "MarkdownAdapter",
    "NeuroBridge",
    "PlainTextAdapter",
    "Profile",
    "ProfileBlender",
    "ProfileConfig",
    "ProfileQuiz",
    "QuizEngine",
    "QuizOption",
    "QuizQuestion",
    "QuizResult",
    "TTSAdapter",
]
