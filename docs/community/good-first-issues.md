# Good First Issues (Initial Batch of 10)

Each section is a ready-to-post GitHub issue body.

## Issue 1: Add 10 more idioms to autism idiom dictionary

Context:
Autism-oriented adaptation relies on replacing figurative expressions with literal phrasing. Expanding the idiom dictionary improves clarity for more real-world prompts.

What to do:
1. Add 10 new idiom mappings to [neurobridge/data/idioms.json](neurobridge/data/idioms.json#L2).
2. Keep values literal and concise.
3. Ensure JSON remains sorted logically and valid.
4. Add/extend tests in [tests/test_tone.py](tests/test_tone.py#L18) to verify replacement behavior.

Files to edit:
- [neurobridge/data/idioms.json](neurobridge/data/idioms.json#L2)
- [neurobridge/core/transform.py](neurobridge/core/transform.py#L50)
- [tests/test_tone.py](tests/test_tone.py#L18)

Definition of done:
- New idioms are replaced in transform output.
- `python -m pytest tests/test_tone.py -q` passes.

## Issue 2: Add 5 urgency words to anxiety filter

Context:
Anxiety profile works best when urgency language is dampened. The current urgency lexicon can miss common pressure words.

What to do:
1. Add 5 urgency tokens to [neurobridge/data/urgency_words.json](neurobridge/data/urgency_words.json#L2).
2. Keep token style lowercase and phrase-safe.
3. Add test coverage for at least 2 new tokens.

Files to edit:
- [neurobridge/data/urgency_words.json](neurobridge/data/urgency_words.json#L2)
- [neurobridge/core/transform.py](neurobridge/core/transform.py#L45)
- [tests/test_tone.py](tests/test_tone.py#L32)

Definition of done:
- New urgency words affect urgency scoring and rewrites.
- `python -m pytest tests/test_tone.py -q` passes.

## Issue 3: Add Portuguese (Brazil) profile variant

Context:
NeuroBridge currently focuses on English defaults. A PT-BR profile variant helps broaden adoption and experimentation.

What to do:
1. Add a new profile enum entry for PT-BR variant in [neurobridge/core/profile.py](neurobridge/core/profile.py#L12).
2. Add default profile config in [neurobridge/core/profile.py](neurobridge/core/profile.py#L49).
3. Allow profile validation in [neurobridge/core/validators.py](neurobridge/core/validators.py#L12).
4. Add one test proving profile retrieval/validation path.

Files to edit:
- [neurobridge/core/profile.py](neurobridge/core/profile.py#L12)
- [neurobridge/core/profile.py](neurobridge/core/profile.py#L49)
- [neurobridge/core/validators.py](neurobridge/core/validators.py#L12)
- [tests/test_profiles.py](tests/test_profiles.py#L21)

Definition of done:
- New profile can be selected without validation errors.
- `python -m pytest tests/test_profiles.py -q` passes.

## Issue 4: Improve error message when wrapped client is None

Context:
If `wrap()` is called with `None`, current behavior can fail later with less actionable attribute errors.

What to do:
1. Add explicit guard in OpenAI wrapper `wrap()` to reject `None` with a clear `TypeError`.
2. Mirror behavior for Anthropic wrapper if needed for consistency.
3. Add tests validating exact error text.

Files to edit:
- [neurobridge/integrations/openai.py](neurobridge/integrations/openai.py#L148)
- [neurobridge/integrations/anthropic.py](neurobridge/integrations/anthropic.py#L62)
- [tests/test_integration.py](tests/test_integration.py#L43)

Definition of done:
- Passing `None` yields explicit developer-friendly error.
- `python -m pytest tests/test_integration.py -q` passes.

## Issue 5: Add public API type stubs (.pyi)

Context:
Typing support improves editor experience and API discoverability for downstream users.

What to do:
1. Create `neurobridge/__init__.pyi` with exported public symbols.
2. Add stubs for core public classes used by importers.
3. Ensure package data includes stubs if needed.

Files to edit:
- [neurobridge/__init__.py](neurobridge/__init__.py#L5)
- [pyproject.toml](pyproject.toml#L68)
- [tests/test_structure.py](tests/test_structure.py#L7)

Definition of done:
- Stubs exist and align with public exports.
- `python -m mypy neurobridge/` runs without new stub-related failures.

## Issue 6: Add progress bar to CLI quiz

Context:
Quiz has 15 questions; a progress indicator helps users orient and reduces abandonment.

What to do:
1. Add progress display while iterating questions in CLI quiz flow.
2. Keep output readable in non-interactive terminals.
3. Add tests covering output shape for quiz command path.

Files to edit:
- [neurobridge/core/quiz.py](neurobridge/core/quiz.py#L226)
- [neurobridge/core/quiz.py](neurobridge/core/quiz.py#L232)
- [tests/test_quiz.py](tests/test_quiz.py#L68)

Definition of done:
- Quiz output shows clear progress (`Question X/15` or equivalent).
- `python -m pytest tests/test_quiz.py -q` passes.

## Issue 7: Add Ollama integration example

Context:
Many local-first developers use Ollama. A first-party example lowers onboarding friction.

What to do:
1. Add an Ollama usage example in integrations docs.
2. Include setup steps, sample code, and expected output snippet.
3. Keep example runnable with minimal prerequisites.

Files to edit:
- [docs/integrations.md](docs/integrations.md#L1)
- [README.md](README.md#L21)
- [examples](examples)

Definition of done:
- Docs include a clear Ollama section with code snippet.
- Example command path is reproducible locally.

## Issue 8: Add --version flag to CLI

Context:
CLI users expect a quick version check for support/debugging workflows.

What to do:
1. Add `--version` option at root CLI level.
2. Print semantic version and exit cleanly.
3. Add tests for flag behavior.

Files to edit:
- [neurobridge/cli.py](neurobridge/cli.py#L28)
- [neurobridge/cli.py](neurobridge/cli.py#L218)
- [tests/test_cli.py](tests/test_cli.py#L12)

Definition of done:
- `neurobridge --version` returns version and exits with code 0.
- `python -m pytest tests/test_cli.py -q` passes.

## Issue 9: Add reading time estimate to AdaptedResponse

Context:
A reading-time estimate helps users choose whether to skim now or defer.

What to do:
1. Add `estimated_reading_time_seconds` (or similar) to response model.
2. Populate it in `chat()` and `chat_stream()` final response.
3. Add tests validating value is present and non-negative.

Files to edit:
- [neurobridge/core/bridge.py](neurobridge/core/bridge.py#L92)
- [neurobridge/core/bridge.py](neurobridge/core/bridge.py#L200)
- [neurobridge/core/bridge.py](neurobridge/core/bridge.py#L349)
- [tests/test_bridge.py](tests/test_bridge.py#L27)

Definition of done:
- Response includes reading-time field for normal and streaming flows.
- `python -m pytest tests/test_bridge.py tests/test_streaming.py -q` passes.

## Issue 10: Improve ADHD chunker to preserve list items

Context:
ADHD chunking can split list items in suboptimal spots, reducing scanability.

What to do:
1. Update chunker logic to detect numbered/bulleted list blocks.
2. Preserve list item boundaries during chunk grouping.
3. Add regression tests for mixed prose + list inputs.

Files to edit:
- [neurobridge/core/transform.py](neurobridge/core/transform.py#L238)
- [neurobridge/core/transform.py](neurobridge/core/transform.py#L273)
- [tests/test_transform.py](tests/test_transform.py#L67)

Definition of done:
- List items are not split across chunks in ADHD mode.
- `python -m pytest tests/test_transform.py -q` passes.
