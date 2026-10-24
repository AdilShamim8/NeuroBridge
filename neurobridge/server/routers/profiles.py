"""Profile management endpoints."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from neurobridge import CustomProfile, Profile
from neurobridge.core.profile import get_profile_config
from neurobridge.core.validators import validate_user_id
from neurobridge.server.models import FeedbackPatchRequest, ProfileGetResponse, ProfileSetRequest

router = APIRouter(tags=["profiles"])


def _validate_path_user_id(user_id: str) -> str:
    """Validate a user_id taken from the URL path.

    Without this, IDs that fail validation raise ValueError deep inside the
    bridge and surface as opaque 500s instead of 422s.
    """
    try:
        return validate_user_id(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/profile")
def set_profile(payload: ProfileSetRequest, request: Request):
    """Persist a profile configuration for a user.

    The shared bridge default is never mutated: one user's stored profile must
    not change the output of other users' requests.
    """
    bridge = request.app.state.bridge

    if payload.profile.strip().lower() == "custom":
        if not payload.custom_config:
            raise HTTPException(
                status_code=400, detail="custom_config is required for custom profile"
            )
        try:
            custom = CustomProfile(**payload.custom_config)
            custom.validate()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if bridge.memory_store is not None:
            bridge.memory_store.save_profile(payload.user_id, custom)
        profile_name = "custom"
        config_dict = asdict(custom)
    else:
        try:
            profile = Profile[payload.profile.strip().upper()]
        except KeyError as exc:
            raise HTTPException(
                status_code=400, detail=f"Unsupported profile: {payload.profile}"
            ) from exc
        profile_config = get_profile_config(profile)
        if bridge.memory_store is not None:
            bridge.memory_store.save_profile(payload.user_id, profile_config)
        profile_name = profile.value
        config_dict = asdict(profile_config)

    now = datetime.now(timezone.utc).isoformat()
    return {
        "user_id": payload.user_id,
        "profile": profile_name,
        "config": config_dict,
        "created_at": now,
        "last_used": now,
    }


@router.get("/profile/{user_id}", response_model=ProfileGetResponse)
def get_profile(user_id: str, request: Request) -> ProfileGetResponse:
    user_id = _validate_path_user_id(user_id)
    bridge = request.app.state.bridge
    if bridge.memory_store is None:
        raise HTTPException(status_code=404, detail="No memory backend configured")

    profile = bridge.memory_store.load_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    now = datetime.now(timezone.utc).isoformat()
    return ProfileGetResponse(
        user_id=user_id,
        profile="custom",
        config=asdict(profile),
        created_at=now,
        last_used=now,
    )


@router.delete("/profile/{user_id}")
def delete_profile(user_id: str, request: Request):
    user_id = _validate_path_user_id(user_id)
    bridge = request.app.state.bridge
    bridge.delete_user_data(user_id)
    return {"status": "ok", "deleted": True, "user_id": user_id}


@router.get("/profile/{user_id}/export")
def export_profile_data(user_id: str, request: Request):
    user_id = _validate_path_user_id(user_id)
    bridge = request.app.state.bridge
    return bridge.export_user_data(user_id)


@router.patch("/profile/{user_id}/feedback")
def submit_feedback(user_id: str, payload: FeedbackPatchRequest, request: Request):
    user_id = _validate_path_user_id(user_id)
    bridge = request.app.state.bridge
    bridge.submit_feedback(
        original_text=payload.original_text,
        adapted_text=payload.adapted_text,
        user_edit=payload.user_edit,
        user_id=user_id,
    )
    return {"status": "ok", "user_id": user_id}
