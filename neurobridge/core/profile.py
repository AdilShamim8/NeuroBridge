"""Profile types and defaults for cognitive adaptation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from neurobridge.core.validators import validate_profile_config_ranges


class Profile(str, Enum):
    """Built-in cognitive profiles supported by NeuroBridge."""

    ADHD = "adhd"
    AUTISM = "autism"
    DYSLEXIA = "dyslexia"
    ANXIETY = "anxiety"
    DYSCALCULIA = "dyscalculia"
    CUSTOM = "custom"


@dataclass(slots=True)
class ProfileConfig:
    """Configuration that controls text adaptation behavior."""

    chunk_size: int
    tone: str
    ambiguity_resolution: str
    number_format: str
    leading_style: str
    reading_level: int
    max_sentence_words: int

    def validate(self) -> None:
        """Validate user-provided configuration values."""
        validate_profile_config_ranges(
            chunk_size=self.chunk_size,
            reading_level=self.reading_level,
            max_sentence_words=self.max_sentence_words,
        )


@dataclass(slots=True)
class CustomProfile(ProfileConfig):
    """User-defined profile for bespoke adaptation behavior."""


DEFAULT_PROFILE_CONFIGS: Dict[Profile, ProfileConfig] = {
    Profile.ADHD: ProfileConfig(
        chunk_size=3,
        tone="clear",
        ambiguity_resolution="balanced",
        number_format="contextual",
        leading_style="summary_first",
        reading_level=7,
        max_sentence_words=16,
    ),
    Profile.AUTISM: ProfileConfig(
        chunk_size=2,
        tone="neutral",
        ambiguity_resolution="explicit",
        number_format="raw",
        leading_style="detail_first",
        reading_level=8,
        max_sentence_words=18,
    ),
    Profile.DYSLEXIA: ProfileConfig(
        chunk_size=2,
        tone="calm",
        ambiguity_resolution="explicit",
        number_format="contextual",
        leading_style="summary_first",
        reading_level=5,
        max_sentence_words=12,
    ),
    Profile.ANXIETY: ProfileConfig(
        chunk_size=3,
        tone="calm",
        ambiguity_resolution="explicit",
        number_format="contextual",
        leading_style="reassure_first",
        reading_level=6,
        max_sentence_words=14,
    ),
    Profile.DYSCALCULIA: ProfileConfig(
        chunk_size=3,
        tone="clear",
        ambiguity_resolution="balanced",
        number_format="contextual",
        leading_style="stepwise",
        reading_level=6,
        max_sentence_words=15,
    ),
    Profile.CUSTOM: ProfileConfig(
        chunk_size=3,
        tone="neutral",
        ambiguity_resolution="balanced",
        number_format="raw",
        leading_style="detail_first",
        reading_level=8,
        max_sentence_words=18,
    ),
}


def get_profile_config(profile: Profile) -> ProfileConfig:
    """Get a validated copy of defaults for a built-in profile."""
    config = DEFAULT_PROFILE_CONFIGS[profile]
    result = ProfileConfig(
        chunk_size=config.chunk_size,
        tone=config.tone,
        ambiguity_resolution=config.ambiguity_resolution,
        number_format=config.number_format,
        leading_style=config.leading_style,
        reading_level=config.reading_level,
        max_sentence_words=config.max_sentence_words,
    )
    result.validate()
    return result
