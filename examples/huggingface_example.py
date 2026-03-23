"""Day 10 HuggingFace integration examples."""

from dataclasses import dataclass

from neurobridge import Config, Profile
from neurobridge.integrations.huggingface import NeuroBridgePipeline


class DemoPipeline:
    def __call__(self, inputs, **kwargs):
        _ = kwargs
        if isinstance(inputs, str):
            return [{"generated_text": f"Generated: {inputs} This is critical and must be done ASAP."}]
        return [{"generated_text": "This is urgent and needs immediate action."}]


@dataclass
class DemoChatPrompt:
    role: str
    content: str


def example_with_gpt2_pattern() -> None:
    wrapped = NeuroBridgePipeline(
        pipeline_obj=DemoPipeline(),
        profile=Profile.ANXIETY,
        config=Config(memory_backend="none"),
    )
    output = wrapped("Explain gradient descent in one paragraph.")
    print("[gpt2-pattern]", output[0]["generated_text"])


def example_with_chat_model_pattern() -> None:
    wrapped = NeuroBridgePipeline(
        pipeline_obj=DemoPipeline(),
        profile=Profile.ANXIETY,
        config=Config(memory_backend="none"),
    )
    messages = [
        DemoChatPrompt(role="system", content="Be helpful"),
        DemoChatPrompt(role="user", content="Summarize this release plan"),
    ]
    output = wrapped(messages)
    print("[mistral-pattern]", output[0]["generated_text"])


if __name__ == "__main__":
    example_with_gpt2_pattern()
    example_with_chat_model_pattern()
