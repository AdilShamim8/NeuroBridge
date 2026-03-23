# Improve Error Message When Wrapped Client Is None

## Context
Passing `None` into wrappers should fail fast with actionable guidance.

## What to do
1. Add explicit `None` guard and message in wrapper `wrap()`.
2. Keep behavior consistent between OpenAI and Anthropic wrappers.
3. Add tests for error message.

## Files to edit
- [neurobridge/integrations/openai.py](neurobridge/integrations/openai.py#L148)
- [neurobridge/integrations/anthropic.py](neurobridge/integrations/anthropic.py#L62)
- [tests/test_integration.py](tests/test_integration.py#L43)

## Definition of done
- `wrap(None, ...)` raises clear `TypeError`.
- `python -m pytest tests/test_integration.py -q` passes.
