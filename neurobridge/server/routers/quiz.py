"""Quiz endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict

from fastapi import APIRouter, HTTPException, Request

from neurobridge.core.quiz import QuizEngine
from neurobridge.server.models import QuizQuestionsResponse, QuizResultResponse, QuizSubmitRequest

router = APIRouter(tags=["quiz"])


@router.get("/quiz/questions", response_model=QuizQuestionsResponse)
def get_questions() -> QuizQuestionsResponse:
    engine = QuizEngine()
    questions = []
    for question in engine.QUESTIONS:
        questions.append(
            {
                "id": question.id,
                "prompt": question.prompt,
                "weight": question.weight,
                "options": [option.text for option in question.options],
            }
        )
    return QuizQuestionsResponse(questions=questions)


@router.post("/quiz/submit", response_model=QuizResultResponse)
def submit_quiz(payload: QuizSubmitRequest, request: Request) -> QuizResultResponse:
    engine = QuizEngine()
    answers: Dict[str, int] = {}
    for question in engine.QUESTIONS:
        if question.id not in payload.answers:
            raise HTTPException(status_code=400, detail=f"Missing answer for {question.id}")
        raw = payload.answers[question.id]
        try:
            option_index = int(raw)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid answer index for {question.id}"
            ) from exc
        answers[question.id] = option_index

    result = engine.score_answers(answers)

    bridge = request.app.state.bridge
    if payload.user_id:
        bridge.set_profile(result)
        if bridge.memory_store is not None:
            bridge.memory_store.save_profile(payload.user_id, result.recommended_config)

    return QuizResultResponse(
        primary_profile=result.primary_profile.value,
        secondary_profile=result.secondary_profile.value if result.secondary_profile else None,
        confidence=result.confidence,
        recommended_config=asdict(result.recommended_config),
    )
