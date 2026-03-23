"""Pydantic request/response models for NeuroBridge server endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from neurobridge.core.validators import (
    MAX_TEXT_LENGTH_DEFAULT,
    validate_profile_name,
    validate_text_input,
    validate_user_id,
)


class AdaptRequest(BaseModel):
    text: str = Field(min_length=1)
    user_id: Optional[str] = None
    profile: Optional[str] = None

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        return validate_text_input(value, max_length=MAX_TEXT_LENGTH_DEFAULT)

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_user_id(value)

    @field_validator("profile")
    @classmethod
    def _validate_profile(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_profile_name(value)


class BatchAdaptRequest(BaseModel):
    texts: List[str] = Field(min_length=1, max_length=20)
    user_id: Optional[str] = None
    profile: Optional[str] = None

    @field_validator("texts")
    @classmethod
    def _validate_texts(cls, value: List[str]) -> List[str]:
        for item in value:
            validate_text_input(item, max_length=MAX_TEXT_LENGTH_DEFAULT)
        return value

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_user_id(value)

    @field_validator("profile")
    @classmethod
    def _validate_profile(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_profile_name(value)


class AdaptResponse(BaseModel):
    adapted_text: str
    original_text: str
    profile_used: str
    transforms_applied: List[str]
    processing_time_ms: float


class BatchAdaptResponse(BaseModel):
    results: List[AdaptResponse]


class ProfileSetRequest(BaseModel):
    user_id: str = Field(min_length=1)
    profile: str = Field(min_length=1)
    custom_config: Optional[Dict[str, Any]] = None

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
    config: Dict[str, Any]
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
    user_id: Optional[str] = None
    answers: Dict[str, str]

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_user_id(value)


class QuizResultResponse(BaseModel):
    primary_profile: str
    secondary_profile: Optional[str]
    confidence: float
    recommended_config: Dict[str, Any]


class QuizQuestionsResponse(BaseModel):
    questions: List[Dict[str, Any]]
