# Testing Guide

## Run tests locally

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -e ".[dev,server]"`
3. Run full test suite:
   - `pytest`
4. Run coverage report:
   - `pytest --cov=neurobridge --cov-report=term-missing --cov-report=html --cov-fail-under=85`

## Integration tests and cassettes

Integration cassette tests are in [tests/integrations](tests/integrations) and cassette fixtures are in [tests/cassettes](tests/cassettes).

- VCR mode in CI uses replay-only behavior from checked-in cassettes.
- To re-record cassettes locally, switch `record_mode` in the test to `once`, run tests, and commit updated YAML files.
- Keep cassettes free of secrets and use mock-style payloads.

## Add a new profile test

1. Create or update tests in [tests/test_transform.py](tests/test_transform.py), [tests/test_profiles.py](tests/test_profiles.py), or [tests/test_accessibility.py](tests/test_accessibility.py).
2. Include profile setup with `bridge.set_profile(Profile.X)`.
3. Assert both correctness and accessibility outcomes (for example sentence length, urgency reduction, or number context).
4. Prefer deterministic text fixtures over random-only checks.

## Mutation testing

Run mutation testing focused on transform logic:

- `mutmut run --paths-to-mutate neurobridge/core/transform.py`
- `mutmut results`

Quality target:

- Mutation score above 70% for [neurobridge/core/transform.py](neurobridge/core/transform.py).

## Useful subsets

- Core transform tests: `pytest tests/test_transform.py tests/test_profiles.py tests/test_accessibility.py`
- Server tests: `pytest tests/server/test_api.py tests/server/test_api_extended.py`
- Integration tests: `pytest tests/integrations`
