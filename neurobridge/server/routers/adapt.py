"""Adaptation endpoints."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from neurobridge import Profile
from neurobridge.core.bridge import AdaptedResponse
from neurobridge.server.models import (
    AdaptRequest,
    AdaptResponse,
    BatchAdaptRequest,
    BatchAdaptResponse,
)

router = APIRouter(tags=["adapt"])


def _set_profile_if_provided(bridge, profile_name: Optional[str]) -> None:
    if not profile_name:
        return
    normalized = profile_name.strip().upper()
    try:
        bridge.set_profile(Profile[normalized])
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unsupported profile: {profile_name}") from exc


@router.post("/adapt", response_model=AdaptResponse)
def adapt_text(payload: AdaptRequest, request: Request) -> AdaptResponse:
    bridge = request.app.state.bridge
    _set_profile_if_provided(bridge, payload.profile)
    response = bridge.chat(payload.text, user_id=payload.user_id)
    return AdaptResponse(
        adapted_text=response.adapted_text,
        original_text=response.raw_text,
        profile_used=str(response.profile),
        transforms_applied=response.modules_run,
        processing_time_ms=response.processing_ms,
    )


@router.post("/adapt/batch", response_model=BatchAdaptResponse)
def adapt_batch(payload: BatchAdaptRequest, request: Request) -> BatchAdaptResponse:
    if len(payload.texts) > 20:
        raise HTTPException(status_code=400, detail="Maximum batch size is 20")

    bridge = request.app.state.bridge
    _set_profile_if_provided(bridge, payload.profile)
    results = []
    for item in payload.texts:
        result = bridge.chat(item, user_id=payload.user_id)
        results.append(
            AdaptResponse(
                adapted_text=result.adapted_text,
                original_text=result.raw_text,
                profile_used=str(result.profile),
                transforms_applied=result.modules_run,
                processing_time_ms=result.processing_ms,
            )
        )
    return BatchAdaptResponse(results=results)


@router.post("/adapt/stream")
async def adapt_stream(payload: AdaptRequest, request: Request) -> StreamingResponse:
    bridge = request.app.state.bridge
    _set_profile_if_provided(bridge, payload.profile)
    stream = bridge.chat_stream(payload.text, user_id=payload.user_id)

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
