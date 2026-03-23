# Add 5 More Urgency Words to Anxiety Filter

## Context
The anxiety profile should catch more pressure language variants.

## What to do
1. Add 5 urgency words to lexicon.
2. Cover at least 2 with tests.

## Files to edit
- [neurobridge/data/urgency_words.json](neurobridge/data/urgency_words.json#L2)
- [neurobridge/core/transform.py](neurobridge/core/transform.py#L45)
- [tests/test_tone.py](tests/test_tone.py#L32)

## Definition of done
- New words influence urgency scoring/rewrite.
- `python -m pytest tests/test_tone.py -q` passes.
