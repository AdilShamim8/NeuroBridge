"""Additional Day 22 tests for low-coverage utility and integration modules."""

from __future__ import annotations

from neurobridge import Config, Profile
from neurobridge.integrations.base import BaseLLMAdapter
from neurobridge.integrations.huggingface import NeuroBridgePipeline, NeuroBridgeTransformersAdapter
from neurobridge.utils.text import count_words, normalize_whitespace, safe_join


def test_text_utils_behaviour() -> None:
    assert normalize_whitespace("a   b\n c   d ") == "a b\nc d"
    assert count_words("Hello world 123") == 3
    assert safe_join(["alpha", "", "beta"], sep=", ") == "alpha, beta"


class _AdapterImpl(BaseLLMAdapter):
    def chat(self, message: str, **kwargs):  # noqa: ANN003
        _ = kwargs
        return f"echo:{message}"


def test_base_adapter_contract_via_subclass() -> None:
    impl = _AdapterImpl()
    assert impl.chat("hello") == "echo:hello"


class _DemoPipeline:
    def __call__(self, inputs, **kwargs):  # noqa: ANN001, ANN003
        _ = kwargs
        if isinstance(inputs, str):
            return [{"generated_text": f"This is critical and must be done ASAP. {inputs}"}]
        return {"generated_text": "This is urgent and immediate."}


def test_huggingface_pipeline_adapts_list_and_dict_outputs() -> None:
    wrapped = NeuroBridgePipeline(
        _DemoPipeline(), profile=Profile.ANXIETY, config=Config(memory_backend="none")
    )

    list_output = wrapped("hello")
    assert isinstance(list_output, list)
    assert "asap" not in list_output[0]["generated_text"].lower()

    dict_output = wrapped(["non-string input"])
    assert isinstance(dict_output, dict)
    assert "urgent" not in dict_output["generated_text"].lower()


class _MockTokenizer:
    def __call__(self, prompt: str, return_tensors: str = "pt"):
        _ = return_tensors
        return {"input_ids": [prompt]}

    def decode(self, item, skip_special_tokens: bool = True):  # noqa: ANN001
        _ = skip_special_tokens
        return str(item)


class _MockModel:
    def generate(self, **kwargs):  # noqa: ANN003
        prompt = kwargs.get("input_ids", ["sample"])[0]
        return [[f"This is critical and you must respond ASAP. {prompt}"]]


def test_huggingface_transformers_adapter_generate() -> None:
    adapter = NeuroBridgeTransformersAdapter(
        model=_MockModel(),
        tokenizer=_MockTokenizer(),
        profile=Profile.ANXIETY,
        config=Config(memory_backend="none"),
    )
    response = adapter.generate("Summarize this deployment note.")
    assert response.raw_text
    assert "asap" not in response.adapted_text.lower()
    assert "huggingface" == response.metadata["provider"]
