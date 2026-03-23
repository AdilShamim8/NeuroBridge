# Add 10 More Idioms to Autism Dictionary

## Context
Autism-oriented adaptation depends on accurate figurative-to-literal rewrites.

## What to do
1. Add 10 new idiom mappings.
2. Keep replacements literal and concise.
3. Extend tests for replacement behavior.

## Files to edit
- [neurobridge/data/idioms.json](neurobridge/data/idioms.json#L2)
- [neurobridge/core/transform.py](neurobridge/core/transform.py#L50)
- [tests/test_tone.py](tests/test_tone.py#L18)

## Definition of done
- New idioms are rewritten correctly.
- `python -m pytest tests/test_tone.py -q` passes.
