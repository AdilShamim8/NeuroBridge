"""Targeted tests for core validators module coverage."""

from __future__ import annotations

import pytest

from neurobridge.core.validators import (
    MAX_USER_ID_LENGTH,
    contains_any_token,
    sanitize_key_token,
    validate_profile_config_ranges,
    validate_profile_name,
    validate_text_input,
    validate_user_id,
)


def test_validate_text_input_accepts_valid_text() -> None:
    assert validate_text_input("hello") == "hello"


def test_validate_text_input_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        validate_text_input(123)  # type: ignore[arg-type]


def test_validate_text_input_rejects_too_long() -> None:
    with pytest.raises(ValueError):
        validate_text_input("abcd", max_length=3, field="message")


def test_validate_user_id_happy_path() -> None:
    assert validate_user_id("user_123-abc") == "user_123-abc"


def test_validate_user_id_rejects_non_string_and_empty() -> None:
    with pytest.raises(TypeError):
        validate_user_id(1)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate_user_id("  ")


def test_validate_user_id_rejects_length_and_characters() -> None:
    with pytest.raises(ValueError):
        validate_user_id("x" * (MAX_USER_ID_LENGTH + 1))
    with pytest.raises(ValueError):
        validate_user_id("bad user id")


def test_validate_profile_name_normalizes_and_validates() -> None:
    assert validate_profile_name(" ADHD ") == "adhd"
    with pytest.raises(TypeError):
        validate_profile_name(1)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate_profile_name("unsupported")


def test_validate_profile_config_ranges() -> None:
    validate_profile_config_ranges(chunk_size=10, reading_level=6, max_sentence_words=20)

    with pytest.raises(ValueError):
        validate_profile_config_ranges(chunk_size=0, reading_level=6, max_sentence_words=20)
    with pytest.raises(ValueError):
        validate_profile_config_ranges(chunk_size=10, reading_level=13, max_sentence_words=20)
    with pytest.raises(ValueError):
        validate_profile_config_ranges(chunk_size=10, reading_level=6, max_sentence_words=4)


def test_sanitize_key_token_and_contains_any_token() -> None:
    token = sanitize_key_token("user:with spaces/and#chars")
    assert " " not in token
    assert ":" not in token

    assert contains_any_token("This has Critical priority", ["critical", "none"])
    assert not contains_any_token("safe text", ["critical", "urgent"])
