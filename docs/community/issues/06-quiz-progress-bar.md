# Add Progress Bar to CLI Quiz

## Context
Users should see progress through the 15-question quiz flow.

## What to do
1. Show progress in quiz CLI rendering.
2. Keep output terminal-friendly.
3. Extend CLI quiz tests.

## Files to edit
- [neurobridge/core/quiz.py](neurobridge/core/quiz.py#L226)
- [neurobridge/core/quiz.py](neurobridge/core/quiz.py#L232)
- [tests/test_quiz.py](tests/test_quiz.py#L68)

## Definition of done
- Progress indicator appears per question.
- `python -m pytest tests/test_quiz.py -q` passes.
