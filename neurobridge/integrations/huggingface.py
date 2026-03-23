"""HuggingFace integration adapters for NeuroBridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from neurobridge.core.bridge import AdaptedResponse, Config, NeuroBridge
from neurobridge.core.profile import Profile


class NeuroBridgePipeline:
    """Wrap a HuggingFace pipeline-like callable and adapt generated text."""

    def __init__(
        self, pipeline_obj: Any, profile: Profile = Profile.ADHD, config: Optional[Config] = None
    ) -> None:
        self.pipeline_obj = pipeline_obj
        self.bridge = NeuroBridge(config=config)
        self.bridge.set_profile(profile)

    def __call__(self, inputs: Any, **kwargs: Any) -> Any:
        output = self.pipeline_obj(inputs, **kwargs)
        return self._adapt_pipeline_output(output)

    def _adapt_pipeline_output(self, output: Any) -> Any:
        if isinstance(output, list):
            adapted_items: List[Any] = []
            for item in output:
                if isinstance(item, dict) and isinstance(item.get("generated_text"), str):
                    mutated = dict(item)
                    mutated["generated_text"] = self.bridge.adapt(mutated["generated_text"])
                    adapted_items.append(mutated)
                else:
                    adapted_items.append(item)
            return adapted_items

        if isinstance(output, dict) and isinstance(output.get("generated_text"), str):
            mutated = dict(output)
            mutated["generated_text"] = self.bridge.adapt(mutated["generated_text"])
            return mutated

        if isinstance(output, str):
            return self.bridge.adapt(output)

        return output


@dataclass
class NeuroBridgeTransformersAdapter:
    """Direct model + tokenizer integration with generation control."""

    model: Any
    tokenizer: Any
    profile: Profile = Profile.ADHD
    config: Optional[Config] = None

    def __post_init__(self) -> None:
        self.bridge = NeuroBridge(config=self.config)
        self.bridge.set_profile(self.profile)

    def generate(
        self, prompt: str, max_new_tokens: int = 512, **generation_kwargs: Any
    ) -> AdaptedResponse:
        tokenized = self.tokenizer(prompt, return_tensors="pt")
        kwargs: Dict[str, Any] = {"max_new_tokens": max_new_tokens}
        kwargs.update(generation_kwargs)
        generated = self.model.generate(**tokenized, **kwargs)

        decoded = self.tokenizer.decode(generated[0], skip_special_tokens=True)
        adapted = self.bridge.adapt(decoded)
        return AdaptedResponse(
            raw_text=decoded,
            adapted_text=adapted,
            profile=self.bridge.profile,
            interaction_id="hf-generate",
            modules_run=[entry.module for entry in self.bridge._pipeline.last_run],  # noqa: SLF001
            processing_ms=0.0,
            metadata={"provider": "huggingface", "max_new_tokens": max_new_tokens},
        )
