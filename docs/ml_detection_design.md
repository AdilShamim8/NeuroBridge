# ML Profile Detection Design (v0.2.0)

## Problem Statement

NeuroBridge currently requires explicit profile selection (or quiz) before adaptation. This works, but adds setup friction. We want an opt-in system that infers likely profile from interaction behavior while preserving user control and privacy.

Hypothesis: interaction patterns with adapted text can predict the most helpful profile after about 20 events.

## Approach

We introduce a lightweight `ProfileDetector` backed by a `RandomForestClassifier` and a local `InteractionTracker`.

Flow:

1. Track interaction events (`chunk_dwell`, `chunk_reread`, `tts_activated`, `section_skipped`, `text_copied`, feedback signals).
2. Convert event history into 15 engineered features.
3. Run classifier to produce `(profile, confidence, reasoning)`.
4. If confidence < 0.6, fall back to quiz.
5. If confidence > 0.7 and user opted in, auto-update active profile.

### Alternatives Considered

- Prompt-only adaptation memory: rejected due to low consistency and poor observability.
- Deep learning sequence model: rejected for v0.2 due to complexity and deployment overhead.
- Rule-only heuristic detector: useful fallback, but lower expected accuracy than tree-based model.

## Feature List and Privacy Implications

Features used:

1. event_count
2. avg_chunk_dwell_ms
3. avg_scroll_speed
4. chunk_reread_rate
5. tts_activation_rate
6. section_skipped_rate
7. text_copied_rate
8. feedback_positive_rate
9. feedback_negative_rate
10. urgency_section_skip_rate
11. calming_section_reread_rate
12. long_word_pause_ms
13. first_chunk_reread_rate
14. partial_quiz_signal
15. edit_distance_rate

Privacy implications:
- Features are aggregate behavior signals, not raw content.
- No raw text is required for model inference.
- Feedback text is already hash/minimization based in storage.

## Privacy Safeguards

- Opt-in only: no silent enrollment.
- Local-first processing: events are analyzed locally by default.
- Anonymization by design: detector consumes summary metrics.
- Export/delete support remains available for user data.

## Training Data Strategy

Phase 1 (now): synthetic data generation by profile archetypes.

- 1000 synthetic users per profile.
- Label-aware distributions for dwell time, rereads, urgency skipping, TTS use, etc.

Phase 2 (later): opt-in real data.

- Add consented telemetry pipeline with anonymized aggregates.
- Blend synthetic and real data for retraining.

## Accuracy Targets and Evaluation

Target:
- >= 80% primary-profile accuracy using at least 20 events.

Evaluation plan:
- Train/test split 80/20.
- Report: accuracy, precision/recall per class, confusion matrix.
- Regression-check metrics in CI before model updates.

## Bias and Fairness Concerns

Risks:
- Overfitting to synthetic assumptions.
- Misclassification in underrepresented behavior patterns.

Mitigations:
- Keep explicit profile override available at all times.
- Perform recurring fairness audits on false-positive/false-negative rates per cohort.
- Include community review before major detector-policy changes.
- Treat detector as assistive recommendation, not diagnosis.
