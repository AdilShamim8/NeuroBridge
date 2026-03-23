"""Profile management endpoints."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from neurobridge import CustomProfile, Profile
from neurobridge.server.models import FeedbackPatchRequest, ProfileGetResponse, ProfileSetRequest

router = APIRouter(tags=["profiles"])


@router.post("/profile")
def set_profile(payload: ProfileSetRequest, request: Request):
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
        bridge.set_profile(custom)
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
        bridge.set_profile(profile)
        if bridge.memory_store is not None:
            bridge.memory_store.save_profile(
                payload.user_id, bridge._profile_config
            )  # noqa: SLF001
        profile_name = profile.value
        config_dict = asdict(bridge._profile_config)  # noqa: SLF001

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
    bridge = request.app.state.bridge
    bridge.delete_user_data(user_id)
    return {"status": "ok", "deleted": True, "user_id": user_id}


@router.get("/profile/{user_id}/export")
def export_profile_data(user_id: str, request: Request):
    bridge = request.app.state.bridge
    return bridge.export_user_data(user_id)


@router.patch("/profile/{user_id}/feedback")
def submit_feedback(user_id: str, payload: FeedbackPatchRequest, request: Request):
    bridge = request.app.state.bridge
    bridge.submit_feedback(
        original_text=payload.original_text,
        adapted_text=payload.adapted_text,
        user_edit=payload.user_edit,
        user_id=user_id,
    )
    return {"status": "ok", "user_id": user_id}
