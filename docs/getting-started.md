# Getting Started

NeuroBridge is cognitive-accessibility middleware: it rewrites text (and LLM
output) to fit a reader's profile — chunking, tone, sentence length, number
formatting, and structure — without changing the underlying meaning.

## Installation

The package is not yet published on PyPI. Install directly from GitHub:

```bash
pip install git+https://github.com/AdilShamim8/NeuroBridge.git
```

To hack on the project itself, clone it and install with the development
extras:

```bash
git clone https://github.com/AdilShamim8/NeuroBridge.git
cd NeuroBridge
pip install -e ".[dev]"
```

## Quick Example

`adapt()` transforms text without calling any LLM — this works offline:

```python
from neurobridge import NeuroBridge, Profile

bridge = NeuroBridge()
bridge.set_profile(Profile.ADHD)

result = bridge.adapt("You must immediately fix the critical bug.")
print(result)
```

## Round-Tripping an LLM

`chat()` sends a prompt to a configured LLM, then adapts the response before
returning it. Without an LLM configured the call degrades to adapting the
prompt itself (useful for local experiments); with one configured, the raw
model output is preserved on `raw_response`.

To adapt every response from an existing OpenAI (or Anthropic) client, wrap
the client once and keep using it as before:

```python
from openai import OpenAI

from neurobridge import Profile
from neurobridge.integrations import openai as neurobridge_openai

client = neurobridge_openai.wrap(OpenAI(api_key="..."), profile=Profile.ANXIETY)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain observability"}],
)
print(response.choices[0].message.content)  # already adapted
```

## Picking a Profile

Three ways to choose how text is presented:

1. **Directly** — `bridge.set_profile(Profile.DYSCALCULIA)`.
2. **Quiz** — `ProfileQuiz` asks a short set of questions and scores a
   recommended profile.
3. **Custom** — `CustomProfile(...)` tunes every dimension yourself.

See [Profiles](profiles.md) for what each profile changes.

## REST API

The package also ships a FastAPI server:

```bash
python -m uvicorn neurobridge.server.app:app --host 127.0.0.1 --port 8000

curl -X POST http://127.0.0.1:8000/api/v1/adapt \
  -H "Content-Type: application/json" \
  -d '{"text": "Revenue was 22% lower than target.", "profile": "anxiety"}'
```

Health check: `GET /api/v1/health`. Set `NEUROBRIDGE_API_KEY` to require
Bearer authentication on every route.

## Next Steps

- [Profiles](profiles.md) — the six built-in profiles and custom profiles.
- [Integrations](integrations.md) — OpenAI, Anthropic, LangChain, HuggingFace.
- [API Reference](api-reference.md) — generated from docstrings.
