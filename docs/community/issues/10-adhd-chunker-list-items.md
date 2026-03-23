# Improve ADHD Chunker to Preserve List Items

## Context
List items currently risk awkward chunk boundaries in ADHD mode.

## What to do
1. Detect list blocks before chunking.
2. Preserve list-item boundaries while chunking prose.
3. Add regression tests.

## Files to edit
- [neurobridge/core/transform.py](neurobridge/core/transform.py#L238)
- [neurobridge/core/transform.py](neurobridge/core/transform.py#L273)
- [tests/test_transform.py](tests/test_transform.py#L67)

## Definition of done
- ADHD chunker no longer splits list items.
- `python -m pytest tests/test_transform.py -q` passes.
