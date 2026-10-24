"""Pydantic request/response models for NeuroBridge server endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from neurobridge.core.validators import (
    MAX_TEXT_LENGTH_DEFAULT,
    validate_profile_name,
    validate_text_input,
    validate_user_id,
)


class AdaptRequest(BaseModel):
    text: str = Field(min_length=1)
    user_id: str | None = None
    profile: str | None = None
    output_format: Literal["markdown", "html", "plain", "json", "tts"] | None = None

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        # Whitespace-only text would otherwise pass min_length and later raise
        # inside bridge.chat, surfacing as an opaque 500 instead of a 422.
        if not value.strip():
            raise ValueError("text must contain at least one non-whitespace character")
        return validate_text_input(value, max_length=MAX_TEXT_LENGTH_DEFAULT)

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_user_id(value)

    @field_validator("profile")
    @classmethod
    def _validate_profile(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_profile_name(value)


class BatchAdaptRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=20)
    user_id: str | None = None
    profile: str | None = None

    @field_validator("texts")
    @classmethod
    def _validate_texts(cls, value: list[str]) -> list[str]:
        for item in value:
            if not item.strip():
                raise ValueError("each text must contain at least one non-whitespace character")
            validate_text_input(item, max_length=MAX_TEXT_LENGTH_DEFAULT)
        return value

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_user_id(value)

    @field_validator("profile")
    @classmethod
    def _validate_profile(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_profile_name(value)


class AdaptResponse(BaseModel):
    adapted_text: str
    original_text: str
    profile_used: str
    transforms_applied: list[str]
    processing_time_ms: float


class BatchAdaptResponse(BaseModel):
    results: list[AdaptResponse]


class ProfileSetRequest(BaseModel):
    user_id: str = Field(min_length=1)
    profile: str = Field(min_length=1)
    custom_config: dict[str, Any] | None = None

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, value: str) -> str:
        return validate_user_id(value)

    @field_validator("profile")
    @classmethod
    def _validate_profile(cls, value: str) -> str:
        return validate_profile_name(value)


class ProfileGetResponse(BaseModel):
    user_id: str
    profile: str
    config: dict[str, Any]
    created_at: str
    last_used: str


class FeedbackPatchRequest(BaseModel):
    original_text: str
    adapted_text: str
    user_edit: str

    @field_validator("original_text", "adapted_text", "user_edit")
    @classmethod
    def _validate_feedback_text(cls, value: str) -> str:
        return validate_text_input(value, max_length=MAX_TEXT_LENGTH_DEFAULT)


class QuizSubmitRequest(BaseModel):
    user_id: str | None = None
    answers: dict[str, str]

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_user_id(value)


class QuizResultResponse(BaseModel):
    primary_profile: str
    secondary_profile: str | None
    confidence: float
    recommended_config: dict[str, Any]


class QuizQuestionsResponse(BaseModel):
    questions: list[dict[str, Any]]
