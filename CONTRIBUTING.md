# Contributing to NeuroBridge

First time contributing to open source? Welcome. You are in the right place.

NeuroBridge exists to improve cognitive accessibility in AI products. We value practical, respectful, test-backed contributions from developers, researchers, designers, and people sharing lived experience.

## Start Here

1. Read [README.md](README.md) for project context.
2. Pick an issue labeled [good first issue](https://github.com/yourusername/neurobridge/labels/good%20first%20issue).
3. Comment on the issue so maintainers know you are taking it.
4. Open a small PR with tests.

## Development Environment Setup

These steps are tested on Windows and macOS.

### Windows (PowerShell)

1. Clone the repository.
2. Create a virtual environment:
   `python -m venv .venv`
3. Activate it:
   `.\\.venv\\Scripts\\Activate.ps1`
4. Install dependencies:
   `python -m pip install -e ".[dev,server]"`
5. Run baseline checks:
   - `python -m pytest tests/ -q`
   - `python -m ruff check neurobridge/`
   - `python -m black --check neurobridge/`
   - `python -m mypy neurobridge/`

### macOS (zsh/bash)

1. Clone the repository.
2. Create a virtual environment:
   `python3 -m venv .venv`
3. Activate it:
   `source .venv/bin/activate`
4. Install dependencies:
   `python -m pip install -e ".[dev,server]"`
5. Run baseline checks:
   - `python -m pytest tests/ -q`
   - `python -m ruff check neurobridge/`
   - `python -m black --check neurobridge/`
   - `python -m mypy neurobridge/`

## Good First Issues

Use the [good first issue](https://github.com/yourusername/neurobridge/labels/good%20first%20issue) label for your first PR.

Good first issues in this repo are:
- Small, isolated changes (one module or one dataset file)
- Easy to verify with one or two tests
- Low risk to public APIs
- Paired with clear acceptance criteria

## How to Add a New Transform Module

Example target: add a module that adds reading-time hints.

1. Implement a new class in [neurobridge/core/transform.py](neurobridge/core/transform.py) following the `BaseTransformModule` pattern.
2. Register the module in the pipeline bootstrap where modules are assembled.
3. Add unit tests in [tests/test_transform.py](tests/test_transform.py) and/or [tests/test_transform_extended.py](tests/test_transform_extended.py).
4. Validate with `python -m pytest tests/test_transform.py -q`.

## How to Improve a Profile

Profile improvements should include both reasoning and evidence.

1. Update defaults in [neurobridge/core/profile.py](neurobridge/core/profile.py).
2. Update behavior or dictionaries in [neurobridge/core/transform.py](neurobridge/core/transform.py), [neurobridge/data/idioms.json](neurobridge/data/idioms.json), or [neurobridge/data/urgency_words.json](neurobridge/data/urgency_words.json).
3. Add tests that demonstrate the intended behavior change.
4. In your PR description, cite research or lived-experience rationale for the change.

## PR Process

- Keep PRs small and focused: one change per PR.
- Add tests for behavior changes.
- Update docs when public behavior changes.
- Link the issue in your PR description.

## Code Review Expectations

- Maintainers aim to respond within 48 hours.
- Feedback should be constructive, specific, and respectful.
- If changes are requested, push follow-up commits (no force-push required unless asked).

## Definition of Done

A PR is done when all of the following are true:

1. Tests pass locally (`pytest`).
2. Coverage is maintained at or above current project gate.
3. Linting and formatting checks pass.
4. Public-facing docs are updated when behavior changes.
5. `CHANGELOG.md` includes an appropriate entry under Unreleased.

## Reporting Bugs

Please include:
- Reproduction steps
- Expected behavior
- Actual behavior
- Python version and OS
- Any relevant logs or stack traces
