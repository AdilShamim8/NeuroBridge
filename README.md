<div align="center">

<img src="https://img.shields.io/badge/NeuroBridge-v0.1.0-7F77DD?style=for-the-badge&logoColor=white" alt="NeuroBridge" />

# 🧠 NeuroBridge

### Cognitive Accessibility Middleware for AI — The Adaptation Layer the Web Has Been Missing

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Coverage gate: 85%](https://img.shields.io/badge/coverage%20gate-85%25-brightgreen.svg)](TESTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/AdilShamim8/NeuroBridge?style=social)](https://github.com/AdilShamim8/NeuroBridge/stargazers)
[![Discord](https://img.shields.io/discord/placeholder?color=7289DA&label=Discord&logo=discord)](https://discord.gg/neurobridge)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Every AI today speaks in one language. Human brains work in a thousand different ways.**

NeuroBridge is the open-source middleware that sits between any LLM and any application, transforming AI outputs in real time to match how each individual user actually thinks, reads, and processes information.

[**Quickstart**](#-quickstart) · [**Docs**](https://neurobridge.dev/docs) · [**Profiles**](#-cognitive-profiles) · [**Integrations**](#-integrations) · [**Roadmap**](#-roadmap) · [**Community**](#-community)

**Live Demo**: [HuggingFace Space](#deployment-status-not-yet-deployed) · [Colab Notebook](notebooks/NeuroBridge_Quickstart.ipynb)

**Release Validation**: See [docs/release/day29-final-polish-report.md](docs/release/day29-final-polish-report.md) and [docs/release/day30-launch-execution.md](docs/release/day30-launch-execution.md) for the latest quality and launch checks.

---

> *"The most profound technologies are those that disappear. NeuroBridge makes AI invisible to cognitive barriers."*

</div>

---

## 🌍 The Problem

Somewhere between **1.5 and 2.9 billion people worldwide** are neurodivergent — living with ADHD, autism, dyslexia, dyscalculia, anxiety disorders, or other cognitive differences (estimates vary by study, and conditions overlap; the table below shows per-condition prevalence). Yet most AI systems produce the exact same output format for all of them: dense, linear, neurotypical text walls.

This is not a minor UX inconvenience. It is a **fundamental accessibility failure**.

| Condition | Global Prevalence | How Current AI Fails Them |
|---|---|---|
| Dyslexia | ~15% (1.2B people) | Dense text blocks trigger reading barriers |
| ADHD | ~10% (780M people) | Long outputs lose attention within seconds |
| Autism Spectrum | ~2.5% (190M people) | Ambiguous tone and implied meaning cause confusion |
| Anxiety Disorders | ~4% (300M people) | Urgent or negative framing spikes distress |
| Dyscalculia | ~6% (460M people) | Raw numbers without context overwhelm processing |

Accessibility regulation is tightening: the **EU Accessibility Act** extends obligations to more digital products from June 2025, and the **ADA** has increasingly been applied to digital experiences. Cognitive accessibility is part of that conversation, and open-source tooling for it is scarce.

**NeuroBridge is that solution.**

---

## ✨ What NeuroBridge Does

NeuroBridge intercepts AI output and transforms it through a four-stage pipeline — transparently, in milliseconds, with no changes to your existing LLM integration.

```
LLM Output  →  [Profile Engine]  →  [Transform Layer]  →  [Format Adapter]  →  User
                  Who is this?        What to change?       How to render it?
```

**For a user with ADHD**, a 400-word explanation of quantum entanglement becomes 6 punchy bullet points with a bold hook, a one-sentence summary, and a "tell me more" button.

**For a user with autism**, the same explanation strips all metaphors, marks every implication explicitly, and presents information in precise, literal, unambiguous language.

**For a user with dyslexia**, the text is restructured with wider line spacing, shorter sentences, progressive disclosure, and optional audio narration.

Same LLM. Same query. Completely different — and completely right — output for each person.

---

## 🚀 Quickstart

### Installation

```bash
pip install git+https://github.com/AdilShamim8/NeuroBridge.git
```

### Quickstart: adapt text directly

```python
from neurobridge import NeuroBridge, Profile

nb = NeuroBridge()
nb.set_profile(Profile.ADHD)

response = nb.chat("Explain how machine learning works")
print(response.adapted_text)
```

### Drop-in for the OpenAI SDK

```python
from openai import OpenAI
from neurobridge import Profile
from neurobridge.integrations import wrap_openai

client = wrap_openai(OpenAI(), profile=Profile.ADHD)

# Every chat completion (streaming included) now goes to the real API
# first and comes back adapted.
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain how machine learning works"}],
)
```

> `NeuroBridge(llm_client=...)` expects a client exposing a callable
> `chat(message=..., **kwargs)` interface (or `chat_stream` for streaming);
> the OpenAI SDK's `client.chat` is a namespace, not callable - use
> `wrap_openai` for that.

### Choosing a profile with the quiz

`ProfileQuiz` is interactive (it prompts on the terminal), so run it from a
command line rather than a server or notebook:

```bash
neurobridge quiz            # interactive assessment, prints the recommendation
neurobridge quiz --save --user-id user_123
```

Or programmatically when you already have answers:

```python
from neurobridge.core.quiz import QuizEngine

engine = QuizEngine()
result = engine.from_answers_json('{"answers": {"q1": 0, "q2": 1}}')
# result.primary_profile, result.recommended_config
```

### JavaScript/TypeScript SDK (Preview)

```bash
cd packages/neurobridge-js
npm install
npm run build
```

See package docs in `packages/neurobridge-js/README.md`.

### Drop-in OpenAI Replacement

```python
# Before
from openai import OpenAI
client = OpenAI()

# After (literally 2 lines changed)
from openai import OpenAI
from neurobridge.integrations.openai import wrap

client = wrap(OpenAI(), profile=Profile.DYSLEXIA)
# All client.chat.completions.create() calls now auto-adapt
```

### Security And Privacy Baseline

- Use HTTPS for all production traffic (API and website).
- Configure Bearer API key auth via `NEUROBRIDGE_API_KEY` for protected deployments.
- Review [SECURITY.md](SECURITY.md) for disclosure and hardening guidance.
- Review [docs/PRIVACY_POLICY.md](docs/PRIVACY_POLICY.md) for data-handling behavior.

---

## 🧩 Cognitive Profiles

NeuroBridge ships with 5 research-backed built-in profiles, each designed in collaboration with neurodivergent communities and clinical guidelines.

### `Profile.ADHD`
- Breaks outputs into **short, scannable chunks** (max 3 sentences per block)
- Leads with the **most important information first** (inverted pyramid)
- Uses **bold anchors** to help eyes re-find context
- Adds progress indicators ("Step 2 of 4") to long content
- Strips filler phrases ("It is worth noting that...")

### `Profile.AUTISM`
- Eliminates **all ambiguous or implied language**
- Replaces idioms, metaphors, and sarcasm with **literal equivalents**
- Makes all **social/emotional context explicit** ("This might feel frustrating")
- Provides **structured, predictable formatting** — no surprises
- Uses **exact, precise language** over approximations

### `Profile.DYSLEXIA`
- **Short sentences** (max 15 words average)
- **One idea per paragraph**, generous whitespace
- **Active voice** throughout — no passive constructions
- Avoids visually similar letter clusters (optimised font guidance)
- Supports **text-to-speech output mode**

### `Profile.ANXIETY`
- **Neutral, calm tone** — removes urgency language ("ASAP", "critical", "must")
- Leads with **reassurance and context** before delivering difficult information
- Avoids catastrophic framings — uses balanced, grounded language
- Provides **clear next steps** so the user never feels lost
- Strips overwhelming option lists — presents one clear recommendation first

### `Profile.DYSCALCULIA`
- **Contextualises every number** ("$3.2M — roughly the cost of 30 average homes")
- Converts mathematical notation to **plain language explanations**
- Uses **visual comparisons** instead of raw statistics
- Avoids percentage-heavy reasoning, offers ratio-based alternatives

### Custom Profile Builder

```python
from neurobridge import CustomProfile

my_profile = CustomProfile(
    chunk_size=2,                    # sentences per block
    tone="calm",                     # calm | neutral | energetic
    ambiguity_resolution="explicit", # explicit | implicit
    number_format="contextual",      # contextual | raw | visual
    leading_style="summary_first",   # summary_first | detail_first
    reading_level=6,                 # grade level target
)

nb.set_profile(my_profile)
```

---

## 🔌 Integrations

NeuroBridge is designed to be a **zero-friction drop-in** for every major AI ecosystem.

| Integration | Status | How to use |
|---|---|---|
| OpenAI SDK | Stable | `wrap()` from `neurobridge.integrations` |
| Anthropic SDK | Stable | `wrap()` from `neurobridge.integrations` |
| LangChain | Stable | output parsers, callback handlers, chains, retrievers |
| Hugging Face | Stable | pipeline and transformers adapters |
| FastAPI server | Stable | `pip install -e ".[server]"`, then `neurobridge serve` |
| Redis memory | Stable | `pip install -e ".[redis]"` |

### LangChain Example

```python
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from neurobridge.integrations import NeuroBridgeOutputParser

llm = ChatOpenAI()
parser = NeuroBridgeOutputParser(profile=Profile.ADHD)
prompt = PromptTemplate.from_template("Explain {topic} simply.")

chain = prompt | llm | parser
# All chain outputs now auto-adapt
```

The langchain integration requires `langchain-core` (installed with the
`langchain` dependency); `langchain_openai` is the current package for the
OpenAI chat model (`langchain.chat_models` was removed in langchain 0.3).


## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Your Application                   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              NeuroBridge Core                        │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────┐  │
│  │Profile Engine│  │Transform Layer│  │  Memory  │  │
│  │              │  │               │  │  Store   │  │
│  │ - Quiz       │  │ - Chunker     │  │          │  │
│  │ - Detection  │  │ - Tone Rewriter│  │ - SQLite │  │
│  │ - Custom API │  │ - Simplifier  │  │ - Redis  │  │
│  │ - Persistence│  │ - Structurer  │  │ - Custom │  │
│  └──────────────┘  └───────────────┘  └──────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │              Format Adapter                  │    │
│  │  Markdown │ HTML │ Plain Text │ TTS │ JSON   │    │
│  └──────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│         Any LLM (OpenAI / Anthropic / Local)        │
└─────────────────────────────────────────────────────┘
```

### Core Modules

**`neurobridge.core.profile`** — Manages cognitive profiles. Includes the `ProfileQuiz` (15-question adaptive assessment), profile persistence, and a REST API for profile management across sessions.

**`neurobridge.core.transform`** - The heart of NeuroBridge. Contains 6 transformation modules run in order: `Chunker`, `SentenceSimplifier`, `UrgencyFilter`, `ToneRewriter`, `NumberContextualiser`, and `PriorityReorderer`.

**`neurobridge.core.memory`** — Learns user preferences over time. When a user edits an adapted output ("make this shorter"), NeuroBridge records the delta and updates their profile. Supports SQLite (default), Redis, and custom backends.

**`neurobridge.core.format_adapter`** — Converts transformed text into the right output format: rich Markdown, HTML with ARIA labels, plain text, JSON (for custom rendering), or a TTS-ready string.

---

## 📊 Performance

NeuroBridge's transform pipeline is pure CPU work over text and adds
sub-millisecond-per-sentence overhead to an LLM call; total overhead is
dominated by the LLM itself.

Reproduce the numbers on your own hardware with the committed benchmark
scripts rather than trusting marketing tables:

```bash
python benchmarks/benchmark_pipeline.py   # end-to-end pipeline latency
python benchmarks/benchmark_transform.py  # transform throughput
python benchmarks/benchmark_memory.py     # memory backend latency
```

| Profile load | 0.3ms | 1.1ms |
| Transform pipeline | 8ms | 24ms |
| Format adapter | 1.2ms | 4ms |
| **Total overhead** | **~10ms** | **~30ms** |


---

## 🔬 Research Foundation

NeuroBridge's transformation rules are grounded in peer-reviewed research and established accessibility guidelines:

- **Web Content Accessibility Guidelines (WCAG) 2.2** — Cognitive Accessibility guidance (SC 3.1.5, 3.2.4)
- **Plain Language Action and Information Network (PLAIN)** — US federal plain language guidelines
- **Cognitive Accessibility Roadmap** — W3C/WAI cognitive-a11y task force guidelines
- **DSM-5 / ICD-11** diagnostic criteria for ADHD, ASD, specific learning disorders
- **Understood.org** research on dyslexia-friendly text formatting
- **ADHD-Friendly Design** patterns from the CHADD (Children and Adults with ADHD) community

---

## 🛠 Configuration

```python
from neurobridge import NeuroBridge, Config

nb = NeuroBridge(
    llm_client=your_client,
    config=Config(
        memory_backend="sqlite",        # sqlite | redis | none
        memory_path="./nb_memory.db",
        cache_profiles=True,            # cache profile transforms
        feedback_learning=True,         # learn from user edits
        output_format="markdown",       # markdown | html | plain | json | tts
        max_chunk_words=80,             # override profile chunk size
        debug=False,                    # verbose transform logging
    )
)
```

### Environment Variables

```bash
NEUROBRIDGE_MEMORY_BACKEND=redis
NEUROBRIDGE_REDIS_URL=redis://localhost:6379
NEUROBRIDGE_FEEDBACK_LEARNING=true
NEUROBRIDGE_DEBUG=false
```

---

## 🌐 REST API Server

NeuroBridge ships with a FastAPI server for language-agnostic integration.

```bash
neurobridge serve --port 8080 --host 127.0.0.1
```

```bash
# Set a user profile
curl -X POST http://localhost:8080/api/v1/profile \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u123", "profile": "ADHD"}'

# Adapt any text
curl -X POST http://localhost:8080/api/v1/adapt \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u123", "text": "Your LLM output here"}'
```

Docs UI: `http://127.0.0.1:8080/docs`

---

## 🧪 Testing

```bash
git clone https://github.com/AdilShamim8/NeuroBridge.git
git clone https://github.com/AdilShamim8/NeuroBridge.git
cd NeuroBridge
pip install -e ".[dev]"      # includes the full server test stack

# Run the full test suite
pytest tests/ -q

# Run with coverage (CI gate is 85%)
pytest --cov=neurobridge --cov-report=term --cov-fail-under=85 -q

# Static checks (the same set CI runs)
mypy neurobridge/
ruff check .
black --check .

# JavaScript SDK
cd packages/neurobridge-js && npm ci && npm test
```

---

## 🗺 Roadmap

### v0.1.0 — Foundation (Shipped)
- [x] Core Transform Pipeline
- [x] 5 built-in cognitive profiles
- [x] OpenAI, Anthropic, LangChain integrations
- [x] SQLite memory backend
- [x] ProfileQuiz (15-question assessment)
- [x] REST API server

### v0.2.0 — In Progress

Planned scope is tracked in:

- [docs/release/v0.2.0-scope-lock.md](docs/release/v0.2.0-scope-lock.md)
- [docs/release/v0.2.0-design-draft.md](docs/release/v0.2.0-design-draft.md)
- [docs/release/v0.2.0-community-feedback-thread.md](docs/release/v0.2.0-community-feedback-thread.md)

---

## 🤝 Contributing

NeuroBridge is built for and with neurodivergent communities. Contributions of all kinds are warmly welcome.

### How to Contribute

1. **Code** — See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and PR guidelines
2. **Profile Research** — Help us improve transformation rules with lived-experience input
3. **Translations** — Adapt profiles for non-English languages and reading cultures  
4. **Testing** — Use NeuroBridge and tell us what works, what doesn't, what's missing
5. **Documentation** — Help make our docs accessible (meta, we know)

### First-Time Contributors

Look for issues tagged [`good first issue`](https://github.com/AdilShamim8/NeuroBridge/issues?q=label%3A%22good+first+issue%22) and [`help wanted`](https://github.com/AdilShamim8/NeuroBridge/issues?q=label%3A%22help+wanted%22).

### Code of Conduct

NeuroBridge follows the [Contributor Covenant](CODE_OF_CONDUCT.md). We are committed to maintaining a welcoming, inclusive environment — especially for contributors who are themselves neurodivergent.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for full details.

Use NeuroBridge freely in commercial products. Attribution appreciated but not required.

---

## 💬 Community

- **Discord**: [discord.gg/neurobridge](https://discord.gg/neurobridge) — #general, #profile-research, #integrations
- **GitHub Discussions**: For feature requests, questions, and sharing what you've built
- **Twitter/X**: [@NeuroBridgeAI](https://twitter.com/neurobridgeai)
- **Newsletter**: [neurobridge.dev/newsletter](https://neurobridge.dev/newsletter) — monthly update on research and releases

---

## 🙏 Acknowledgements

Built on the shoulders of giants: the teams behind PyTorch, Hugging Face Transformers, LangChain, and OpenCV whose open-source philosophy made the AI ecosystem what it is. Dedicated to the 1.5 billion people whose brains work differently — and beautifully.

---

<div align="center">

**If NeuroBridge helps you or someone you care about, please consider ⭐ starring the repo.**

It's the single most powerful thing you can do to help this project reach the people who need it.

Made with care · MIT Licensed · [neurobridge.dev](https://neurobridge.dev)

</div>
