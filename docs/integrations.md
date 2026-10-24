# Integrations

NeuroBridge integrates with LLM clients by wrapping them: you hand over your
existing client, you get back a client with the same interface whose outputs
are adapted to the active profile. No API keys are duplicated or stored by
the wrappers — they only transform text in flight.

## OpenAI

```python
from openai import OpenAI

from neurobridge import Profile
from neurobridge.integrations import openai as neurobridge_openai

client = neurobridge_openai.wrap(OpenAI(api_key="..."), profile=Profile.ANXIETY)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain the refund policy"}],
)
print(response.choices[0].message.content)  # adapted
```

Streaming responses are adapted chunk by chunk. If the OpenAI package is not
installed, importing the module raises an actionable error.

## Anthropic

```python
import anthropic

from neurobridge import Profile
from neurobridge.integrations import anthropic as neurobridge_anthropic

client = neurobridge_anthropic.wrap(
    anthropic.Anthropic(api_key="..."), profile=Profile.DYSCALCULIA
)
message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain compound interest"}],
)
print(message.content[0].text)  # adapted
```

## LangChain

Two drop-in helpers for LangChain chains:

- `NeuroBridgeOutputParser` — adapts any chain's final string output.
- `NeuroBridgeCallbackHandler` — adapts outputs via callbacks.

```python
from neurobridge import Profile
from neurobridge.integrations.langchain import NeuroBridgeOutputParser

parser = NeuroBridgeOutputParser(profile=Profile.ADHD)
adapted = parser.parse("A long, dense explanation with many caveats.")
```

Requires the `langchain` package.

## HuggingFace

`NeuroBridgeTransformersAdapter` adapts text-generation pipeline outputs for
local `transformers` models.

## REST API server

The package ships a FastAPI server (see
[Getting Started](getting-started.md)) exposing the same adaptation over
HTTP, with optional API-key auth, per-identity rate limiting, and request
size caps. Run it with:

```bash
python -m uvicorn neurobridge.server.app:app --host 127.0.0.1 --port 8000
```

## Examples

Runnable end-to-end scripts live in the
[`examples/`](https://github.com/AdilShamim8/NeuroBridge/tree/main/examples)
directory: `basic_usage.py`, `langchain_example.py`, and
`huggingface_example.py`.
