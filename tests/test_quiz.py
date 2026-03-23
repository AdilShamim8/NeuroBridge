"""Day 6 tests for quiz scoring, blending, and CLI execution."""

import json

from neurobridge.core.profile import Profile, get_profile_config
from neurobridge.core.quiz import ProfileBlender, ProfileQuiz, QuizEngine


def _answer_all(engine: QuizEngine, option_for_question: int) -> dict[str, int]:
    return {question.id: option_for_question for question in engine.QUESTIONS}


def test_scoring_all_adhd_answers() -> None:
    engine = QuizEngine()
    answers = _answer_all(engine, 0)
    result = engine.score_answers(answers)
    assert result.primary_profile == Profile.ADHD


def test_scoring_all_anxiety_answers() -> None:
    engine = QuizEngine()
    answers = _answer_all(engine, 2)
    result = engine.score_answers(answers)
    assert result.primary_profile == Profile.ANXIETY


def test_scoring_mixed_answers_with_secondary() -> None:
    engine = QuizEngine()
    answers: dict[str, int] = {}
    for index, question in enumerate(engine.QUESTIONS):
        if len(question.options) == 0:
            answers[question.id] = 0
        else:
            answers[question.id] = 0 if index % 2 == 0 else min(1, len(question.options) - 1)

    result = engine.score_answers(answers)
    assert result.primary_profile in {
        Profile.ADHD,
        Profile.AUTISM,
        Profile.DYSLEXIA,
        Profile.ANXIETY,
        Profile.DYSCALCULIA,
    }
    assert 0 <= result.confidence <= 1


def test_profile_blender_numeric_fields_weighted() -> None:
    primary = get_profile_config(Profile.ADHD)
    secondary = get_profile_config(Profile.DYSLEXIA)
    blended = ProfileBlender.blend(primary, secondary, weight=0.3)

    assert blended.chunk_size != 0
    assert blended.reading_level != 0
    assert blended.max_sentence_words != 0
    assert blended.tone == primary.tone
    assert blended.leading_style == primary.leading_style


def test_from_answers_json_payload() -> None:
    engine = QuizEngine()
    payload = {"answers": _answer_all(engine, 0)}
    result = engine.from_answers_json(json.dumps(payload))
    assert result.primary_profile == Profile.ADHD


def test_cli_quiz_can_run_with_mocked_input(monkeypatch) -> None:
    engine = QuizEngine()
    inputs = iter(["1"] * len(engine.QUESTIONS))
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    result = engine.run_cli()
    assert result.primary_profile == Profile.ADHD


def test_profile_quiz_facade_run(monkeypatch) -> None:
    engine = QuizEngine()
    inputs = iter(["3"] * len(engine.QUESTIONS))
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    result = ProfileQuiz.run(user_id="abc")
    assert result == Profile.ANXIETY
