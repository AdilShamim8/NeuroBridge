# I Built What WCAG 2.2 Forgot: Cognitive Accessibility Middleware for AI

## SECTION 1 - The Problem

A developer with ADHD opens a chat window and asks a practical question: "How do I fix this failing migration?"

The model responds with confidence and technical correctness. It also responds with 400 words of dense prose, nested caveats, and no visual structure. The developer reads the first three sentences, switches tabs to check one command, returns, loses the thread, re-reads, gets distracted by one unfamiliar term, and gives up. The bug is still there.

That moment is usually framed as an attention or discipline issue. It is not. It is a format issue.

Modern AI products treat output quality as a single axis: factual quality. But usability is multidimensional. Two users can receive the same accurate answer and have opposite outcomes because the presentation fits one cognitive style and blocks another.

This matters at a global scale. An estimated 1.5 billion people are neurodivergent across conditions like ADHD, autism, dyslexia, anxiety disorders, and dyscalculia. Yet most AI products still deliver one default response shape: long linear text, urgency-heavy tone, ambiguous idioms, and raw numerical abstractions.

We built responsive web design for devices. We have not built responsive cognition design for AI.

There is also a policy and legal shift underway. Accessibility expectations are no longer optional product polish. The EU accessibility regime now includes stronger obligations around digital accessibility outcomes in real user workflows. Teams that treat cognitive accessibility as "nice to have" will be behind technically, ethically, and operationally.

What surprised me most while building NeuroBridge is how much value is locked behind tiny structural changes:
- move the key point to the top
- split dense paragraphs into chunks
- reduce urgency language without changing intent
- make numbers concrete and contextual
- remove ambiguous phrasing when literal interpretation matters

The model does not need to be replaced. The answer does not need to be shortened until it is useless. It needs to be adapted to how a specific person can process it.

That gap is where NeuroBridge lives.

## SECTION 2 - What I Built

NeuroBridge is an open-source middleware layer that sits between your LLM output and your user interface. It transforms the same model response into different presentation styles based on cognitive profile preferences.

It is intentionally simple to integrate:

```python
from neurobridge import NeuroBridge, Profile

nb = NeuroBridge(llm_client=openai_client)
nb.set_profile(Profile.ADHD)
response = nb.chat("Explain how machine learning works")
```

You keep your current model stack. NeuroBridge handles adaptation.

Two quick examples:

ADHD style:
- Before: a long paragraph with multiple caveats and no clear priority order.
- After: one-line bottom line first, then short high-signal bullets in task order.

Dyslexia style:
- Before: dense sentence chains with abstract connectors and visual fatigue.
- After: shorter sentence cadence, clearer spacing, reduced reading friction, simpler lexical flow.

The key principle is preservation of intent. NeuroBridge is not summarization for novelty. It is accessibility-oriented transformation for comprehension and action.

## SECTION 3 - How It Works

NeuroBridge uses a deterministic transformation pipeline. Each stage addresses a known cognitive friction pattern. The pipeline can run in CLI mode, library mode, or server mode.

### 1) Chunker

The chunker breaks long responses into cognitively manageable segments. Under the hood, sentence boundaries are detected with NLTK tokenization and then grouped by profile-aware chunk sizing rules.

For ADHD-oriented output, chunk size defaults smaller and priority content is pulled earlier. For dyslexia-oriented output, chunks are optimized for scanability and visual pacing.

Chunking is more than line breaks. It determines how working memory load accumulates while reading. A user who can process four short units may fail on one long unit with equivalent total words.

### 2) ToneRewriter + UrgencyFilter

AI responses often over-index on urgency terms: "critical," "must," "immediately," "ASAP." These terms are semantically valid in some contexts but can create avoidable stress spikes, especially for anxiety-sensitive users.

The tone stage rewrites tone intensity while preserving task meaning. The urgency stage dampens pressure terms and substitutes calmer equivalents where possible.

This stage also includes an idiom and ambiguity cleanup pass. Figurative language can be expressive for some users and confusing for others. Autism-oriented profiles bias toward literal phrasing and explicit intent markers.

### 3) NumberContextualiser

Raw numerics are often hard to interpret without anchors. NeuroBridge can add simple reference framing for percentages, magnitudes, and quantities.

Example pattern:
- raw: "cost increased by 38%"
- contextual: "cost increased by 38% (about 2 in 5)"

The goal is not to distort precision; it is to reduce interpretation overhead and support faster decisions in cognitively heavy contexts.

### 4) PriorityReorderer

Many AI answers bury the actionable conclusion at the end. PriorityReorderer applies an inverted-pyramid pattern borrowed from journalism and incident communication:
- bottom line first
- next actions second
- context and caveats last

For users with attention volatility, this often determines whether the answer gets used at all.

### 5) Memory + Feedback Learning Loop

NeuroBridge includes optional persistence to track profile settings and interaction feedback safely.

Recent hardening added privacy-first constraints:
- hashed references for feedback text fields
- delta-oriented feedback metrics instead of raw text retention
- user export and delete APIs

The feedback loop can periodically adjust profile settings (for example, chunk size or sentence constraints) based on observed edits, while keeping the data model minimal.

### API + Adapters

The same pipeline powers:
- Python library calls
- FastAPI endpoints (`/adapt`, `/adapt/batch`, `/adapt/stream`)
- CLI commands (`adapt`, `quiz`, `info`)
- output adapters (markdown, html, plain text, json, tts)

This gives one adaptation policy surface across product, tooling, and experiments.

## SECTION 4 - Architecture Decisions

### Why middleware instead of a new LLM?

Building another model would not solve integration friction for teams already using provider APIs. Middleware lets teams adopt accessibility improvements without replatforming inference.

### Why profiles instead of per-user black-box ML first?

Profiles are inspectable, explainable, and fast to validate with users. They create a clear starting point for adaptation policy before adding heavier personalization.

### Why open source instead of closed SaaS?

Accessibility infrastructure improves faster when scrutiny is public. Different communities need different adaptations, and transparent defaults encourage better critique and iteration.

### Why Python?

The ecosystem fit is practical: FastAPI for API surfaces, rich NLP tooling, wide LLM integration support, and strong developer familiarity in AI teams.

## SECTION 5 - What I Learned

The biggest lesson: "shorter" is not equal to "more accessible."

Early versions over-compressed. They removed useful context and made some answers less trustworthy. Accessibility is not about deleting information. It is about presenting the same information in the order, density, and tone that a person can process.

Second lesson: profile behavior needs boundaries.

If a transformation is too aggressive, users feel patronized. If it is too subtle, users do not feel a difference. Good defaults sit in a narrow band between those two failures.

Third lesson: community feedback changes architecture decisions.

Input from neurodivergent developers repeatedly emphasized these points:
- do not force one "accessible" style
- allow explicit profile control
- keep adaptation deterministic and auditable
- treat privacy as first-class, not retrofit

That feedback directly influenced current security and privacy design:
- export/delete user data endpoints
- hashed feedback storage pattern
- strict validation and request controls

Fourth lesson: launch readiness is multidimensional.

A package can be installable and still not be release-ready if coverage, linting, typing, and profile-differentiation checks are below the bar. Quality gates are part of accessibility quality because regressions disproportionately hurt users who rely on adaptation.

## SECTION 6 - What's Next

v0.2.0 is focused on stronger adaptation intelligence and contributor growth.

Near-term priorities:
- ML-assisted profile detection as optional layer on top of explicit profile selection
- richer benchmarking for readability outcomes per profile
- broader integrations and production deployment templates
- expanded profile research with community participation

The long-term goal is not to become "the one right format." The goal is to make adaptation composable, testable, and normal in AI product design.

## CONCLUSION - Call to Action

If you build AI products, cognitive accessibility should be in your architecture diagram, not in your backlog someday list.

- GitHub: https://github.com/yourusername/neurobridge
- PyPI: https://pypi.org/project/neurobridge/
- Discord: https://discord.gg/neurobridge

If you are neurodivergent and want to help improve profile behavior, please open an issue and share what worked, what failed, and what felt cognitively heavy.
