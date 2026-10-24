"""Adaptation endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from neurobridge import Profile
from neurobridge.core.bridge import AdaptedResponse
from neurobridge.core.format_adapter import get_format_adapter
from neurobridge.core.profile import get_profile_config
from neurobridge.server.models import (
    AdaptRequest,
    AdaptResponse,
    BatchAdaptRequest,
    BatchAdaptResponse,
)

router = APIRouter(tags=["adapt"])


def _resolve_profile_param(profile_name: str | None) -> Profile | None:
    """Translate the request profile name into a Profile for a single call.

    The resolved profile is passed per request; the shared bridge instance is
    never reconfigured, so concurrent requests cannot leak profiles into each
    other.
    """
    if not profile_name:
        return None
    normalized = profile_name.strip().upper()
    try:
        return Profile[normalized]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unsupported profile: {profile_name}") from exc


def _profile_value(profile: Profile | str) -> str:
    """Serialize a profile identifier as its wire name ('dyslexia', not 'Profile.DYSLEXIA')."""
    return profile.value if isinstance(profile, Profile) else str(profile)


def _apply_output_format(text: str, output_format: str | None, profile) -> str:
    """Render the adapted text in the requested wire format.

    None keeps the pipeline's native markdown-like output (previous behavior).
    """
    if output_format is None:
        return text
    adapter = get_format_adapter(output_format)
    if adapter is None:
        return text
    return adapter.format(text, profile)


@router.post("/adapt", response_model=AdaptResponse)
def adapt_text(payload: AdaptRequest, request: Request) -> AdaptResponse:
    bridge = request.app.state.bridge
    profile = _resolve_profile_param(payload.profile)
    response = bridge.chat(payload.text, user_id=payload.user_id, profile=profile)
    effective_config = (
        bridge.memory_store.load_profile(payload.user_id)
        if (payload.user_id and bridge.memory_store)
        else None
    )
    profile_config = effective_config or get_profile_config(
        profile if profile is not None else Profile.ADHD
    )
    return AdaptResponse(
        adapted_text=_apply_output_format(
            response.adapted_text, payload.output_format, profile_config
        ),
        original_text=response.raw_text,
        profile_used=_profile_value(response.profile),
        transforms_applied=response.modules_run,
        processing_time_ms=response.processing_ms,
    )


@router.post("/adapt/batch", response_model=BatchAdaptResponse)
def adapt_batch(payload: BatchAdaptRequest, request: Request) -> BatchAdaptResponse:
    if len(payload.texts) > 20:
        raise HTTPException(status_code=400, detail="Maximum batch size is 20")

    bridge = request.app.state.bridge
    profile = _resolve_profile_param(payload.profile)
    results = []
    for item in payload.texts:
        result = bridge.chat(item, user_id=payload.user_id, profile=profile)
        results.append(
            AdaptResponse(
                adapted_text=result.adapted_text,
                original_text=result.raw_text,
                profile_used=_profile_value(result.profile),
                transforms_applied=result.modules_run,
                processing_time_ms=result.processing_ms,
            )
        )
    return BatchAdaptResponse(results=results)


@router.post("/adapt/stream")
async def adapt_stream(payload: AdaptRequest, request: Request) -> StreamingResponse:
    bridge = request.app.state.bridge
    profile = _resolve_profile_param(payload.profile)
    stream = bridge.chat_stream(payload.text, user_id=payload.user_id, profile=profile)

    async def event_stream():
        async for item in stream:
            if isinstance(item, AdaptedResponse):
                done_payload = {
                    "chunk": "",
                    "done": True,
                    "interaction_id": item.interaction_id,
                }
                yield "data: " + json.dumps(done_payload, ensure_ascii=True) + "\n\n"
            else:
                chunk_payload = {
                    "chunk": item,
                    "done": False,
                }
                yield "data: " + json.dumps(chunk_payload, ensure_ascii=True) + "\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
