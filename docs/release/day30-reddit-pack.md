# Day 30 Reddit Launch Posts

## r/MachineLearning (technical architecture)

Title: Built an open-source middleware to adapt LLM output for neurodivergent cognitive profiles

Body:
I built NeuroBridge as a post-processing adaptation layer for LLM outputs.

Architecture highlights:
- Deterministic transform pipeline (chunking, simplification, tone/urgency rewrite, numeric contextualization)
- Profile-aware configuration (ADHD/autism/dyslexia/anxiety/dyscalculia)
- ML-assisted profile detection with confidence gating and quiz fallback
- Integration-friendly wrappers (without replacing model/provider stack)

Would appreciate feedback on model-vs-rules boundary, calibration strategy, and evaluation methodology.

## r/Python (package focus)

Title: I shipped NeuroBridge: a Python package that adapts AI text for cognitive accessibility

Body:
I shipped a Python package called NeuroBridge.

Goal: adapt AI responses to be easier to read/process for different cognitive profiles.

Quick usage:
from neurobridge import NeuroBridge, Profile
bridge = NeuroBridge(); bridge.set_profile(Profile.DYSLEXIA)

Looking for feedback on API design, packaging, and integration ergonomics.

## r/ADHD (human focus)

Title: I built an open-source tool to make AI responses less overwhelming for ADHD brains

Body:
I built NeuroBridge because long, dense AI answers often increase friction instead of helping.

It rewrites output into clearer, more scannable structure (summary-first, cleaner sequencing, reduced overload).

I would really value real-world feedback on what helps vs what still feels noisy.

## r/programming (general audience)

Title: NeuroBridge launch: accessibility middleware for AI output (Python + API + web demo)

Body:
Launched NeuroBridge after a 30-day build sprint.

It is an open-source middleware that adapts LLM output for cognitive accessibility.

Includes package, API server, website demo, and tests/security checks.

Would appreciate feedback from developers integrating AI into user-facing products.
