# Day 30 HN Launch Pack

## Show HN title

Show HN: NeuroBridge - open-source Python middleware to adapt AI output for ADHD, autism, dyslexia

## HN post body

I built NeuroBridge over the last 30 days to make AI output easier to process for neurodivergent users.

It is an open-source middleware layer that rewrites LLM responses based on cognitive profiles (ADHD, autism, dyslexia, anxiety, dyscalculia) while preserving meaning.

Core idea:
- Keep model/provider choice unchanged.
- Add adaptation as a post-processing pipeline.
- Let teams integrate with Python, API routes, or middleware wrappers.

Repo includes:
- Python package + CLI
- REST API server
- Website demo playground + quiz
- JS/TS SDK scaffold
- Tests, security checks, and docs

Feedback welcome, especially from developers building AI products where output accessibility is critical.

## First comment (post immediately)

Technical notes:
- Pipeline modules include chunking, sentence simplification, urgency/tone adjustments, numeric contextualization, and priority ordering.
- There is rule-based adaptation plus an ML-assisted profile detector with confidence gating and fallback to quiz.
- Profile preferences can be explicitly set or inferred from interaction telemetry.
- Integrations target common LLM flows so teams can adopt without replacing their stack.

Main tradeoff so far: balancing stronger adaptation with preserving original intent under strict deterministic tests.

Happy to share implementation details, benchmark setup, and failure cases.
