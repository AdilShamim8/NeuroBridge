"""Quiz endpoints."""

from __future__ import annotations

from dataclasses import asdict

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
    answers: dict[str, int] = {}
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
        # Out-of-range and negative indices are syntactically valid ints but
        # crash score_answers with an unhandled ValueError (opaque 500).
        if not 0 <= option_index < len(question.options):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Answer index for {question.id} must be between 0 and "
                    f"{len(question.options) - 1}"
                ),
            )
        answers[question.id] = option_index

    result = engine.score_answers(answers)

    # Persist the recommendation for the submitting user only. The shared
    # bridge default is never mutated by an HTTP request.
    if payload.user_id:
        bridge = request.app.state.bridge
        if bridge.memory_store is not None:
            bridge.memory_store.save_profile(payload.user_id, result.recommended_config)

    return QuizResultResponse(
        primary_profile=result.primary_profile.value,
        secondary_profile=result.secondary_profile.value if result.secondary_profile else None,
        confidence=result.confidence,
        recommended_config=asdict(result.recommended_config),
    )
