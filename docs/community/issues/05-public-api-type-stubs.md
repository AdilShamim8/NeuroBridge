# Add Type Stubs (.pyi) for Public API

## Context
Stub files improve IDE and type-checker quality for users importing NeuroBridge.

## What to do
1. Add `neurobridge/__init__.pyi`.
2. Define signatures for public exports.
3. Ensure packaging includes stubs where needed.

## Files to edit
- [neurobridge/__init__.py](neurobridge/__init__.py#L5)
- [pyproject.toml](pyproject.toml#L68)
- [tests/test_structure.py](tests/test_structure.py#L7)

## Definition of done
- Stub file matches public API exports.
- `python -m mypy neurobridge/` has no new stub errors.
