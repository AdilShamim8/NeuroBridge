# Retrospective (Internal)

## What took longer than expected and why

- Security and privacy hardening took longer because edge-case input validation and API middleware interactions required multiple rounds of changes and regression tests.
- Cross-surface parity (Python package, server APIs, docs site, JS SDK) increased verification effort and context switching.

## What was easier than expected

- ML profile detection scaffolding moved quickly with synthetic feature generation and a compact random-forest baseline.
- Community operations artifacts (code of conduct, maintainers guide, contribution templates) were straightforward once project voice was established.

## What we would do differently from Day 1

- Lock a coverage strategy and test ownership map up front for core runtime modules.
- Define website telemetry and stats data sources before UI implementation.
- Start JS SDK build/publish validation in parallel earlier to avoid environment surprises late in the sprint.

## The one technical decision we are most uncertain about

- How much behavior should be inferred by ML detector versus explicit quiz/profile controls in early product stages.

## Feature we are most proud of

- End-to-end adaptation pipeline with profile-aware transforms plus practical server and website integration paths.

## Metric that defines success

- Percentage of users who keep profile-aware mode enabled after first week, paired with qualitative reports of reduced cognitive friction.
