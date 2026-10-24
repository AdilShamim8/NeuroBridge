# Profiles

A profile is a set of **presentation preferences** — how text is chunked,
toned, and structured. Profiles are not diagnoses: they describe how a reader
prefers information to be presented, and NeuroBridge never changes the
underlying meaning, only the presentation.

NeuroBridge never silently alters meaning: urgency is only *softened* when a
profile opts into a calmer tone, and numbers are never rounded away — a
percentage below the display threshold is stated as "under 2.5%" rather than
becoming "0 in every 1".

## Built-in Profiles

| Profile | Chunk size | Tone | Numbers | Leading style | Max sentence words |
|---|---|---|---|---|---|
| ADHD | 3 | clear | contextual | summary first | 16 |
| Autism | 2 | neutral | raw | detail first | 18 |
| Dyslexia | 2 | calm | contextual | summary first | 12 |
| Anxiety | 3 | calm | contextual | reassure first | 14 |
| Dyscalculia | 3 | clear | contextual | stepwise | 15 |

What each dimension means:

- **Chunk size** — how many ideas are grouped before a visual break.
- **Tone** — the register of the rewrite (`clear`, `neutral`, `calm`).
- **Ambiguity resolution** — `explicit` spells out implications that
  `balanced` leaves to the reader.
- **Number format** — `contextual` restates figures in plain terms
  ("22% — roughly one fifth"); `raw` keeps figures verbatim.
- **Leading style** — whether the output opens with a summary, the details,
  a reassurance, or a step-by-step structure.
- **Max sentence words** — hard cap enforced by the sentence simplifier.

## Custom Profiles

Every dimension is adjustable through `CustomProfile`:

```python
from neurobridge import CustomProfile, NeuroBridge

custom = CustomProfile(
    chunk_size=2,
    tone="calm",
    ambiguity_resolution="explicit",
    number_format="contextual",
    leading_style="summary_first",
    reading_level=6,
    max_sentence_words=12,
)

bridge = NeuroBridge()
bridge.set_profile(custom)
print(bridge.adapt("Deploy is blocked until the migration is verified."))
```

Values are validated when the profile is applied (`bridge.set_profile`)
against safe ranges — for example, `max_sentence_words` must stay between 5
and 40, and out-of-range values raise `ValueError`.

## Choosing a Profile

- Pick it directly with `bridge.set_profile(Profile.DYSCALCULIA)`.
- Answer a short questionnaire with `ProfileQuiz` and use the scored
  recommendation.
- Let the opt-in ML detector infer a profile from interaction events; when
  confidence is low it falls back to the quiz instead of guessing
  (see `docs/ml_detection_design.md`).
