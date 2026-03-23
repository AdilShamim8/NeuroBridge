# Day 25 - Anticipated Objections FAQ

## Why not prompt engineering only?

Prompting is necessary but not sufficient for consistent accessibility behavior in production. NeuroBridge provides deterministic transformation logic that can be tested independently of vendor model drift.

## Why not just one "accessible mode"?

Different cognitive needs can conflict. A single mode can improve one workflow while degrading another. Profile-based adaptation keeps tradeoffs explicit and configurable.

## Is this clinically validated?

NeuroBridge is not a clinical diagnostic or treatment tool. It is a developer accessibility layer informed by published patterns and community feedback. It should be evaluated as assistive software infrastructure.

## Does this store sensitive text?

Current default approach stores profile state, interaction counts, and hashed feedback references plus delta metrics. Raw feedback text is not required for adaptive behavior.

## Can this be bypassed per request?

Yes. Teams can choose explicit profile per user/session/request and can disable persistence depending on compliance requirements.
