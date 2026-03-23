"""Day 4 tests for NumberContextualiser and PriorityReorderer."""

from neurobridge.core.profile import Profile, get_profile_config
from neurobridge.core.transform import NumberContextualiser, PriorityReorderer, TransformPipeline


def test_number_contextualiser_handles_various_number_formats() -> None:
    profile = get_profile_config(Profile.DYSCALCULIA)
    module = NumberContextualiser()
    text = (
        "Revenue is $3.2M, adoption is 25%, and population reached 1,500,000. "
        "Error rate is 0.003 and migration takes 5-10 years. Backup size is 2 GB."
    )
    out = module.apply(text, profile)
    assert "$3.2M (" in out
    assert "25% (" in out
    assert "1,500,000 (" in out
    assert "0.003 (" in out
    assert "5-10 years (" in out
    assert "2 GB (" in out


def test_number_contextualiser_skips_already_contextualised_numbers() -> None:
    profile = get_profile_config(Profile.DYSCALCULIA)
    module = NumberContextualiser()
    text = "The budget is $500 (already explained) and the pass rate is 50% (about half)."
    out = module.apply(text, profile)
    assert out.count("$500 (") == 1
    assert out.count("50% (") == 1


def test_priority_reorderer_with_clear_conclusion() -> None:
    profile = get_profile_config(Profile.ADHD)
    module = PriorityReorderer()
    text = (
        "The system reads telemetry and aggregates metrics each hour.\n\n"
        "For example, it stores latency and error counts for dashboards.\n\n"
        "Ultimately, the answer is to cache summaries before rendering."
    )
    out = module.apply(text, profile)
    lines = [line for line in out.split("\n\n") if line.strip()]
    assert lines[0].startswith("Summary:")
    assert any(line.startswith("Background:") for line in lines)
    assert any(line.startswith("Example:") for line in lines)


def test_priority_reorderer_without_conclusion_adds_bottom_line() -> None:
    profile = get_profile_config(Profile.ADHD)
    module = PriorityReorderer()
    text = (
        "This module validates input and normalizes fields.\n\n"
        "It writes the result to storage and emits an event for consumers."
    )
    out = module.apply(text, profile)
    assert out.split("\n\n")[0].startswith("**Bottom line:")


def test_priority_reorderer_single_paragraph_text() -> None:
    profile = get_profile_config(Profile.ADHD)
    module = PriorityReorderer()
    text = "The worker processes data in batches and records summary metrics."
    out = module.apply(text, profile)
    assert "Bottom line" in out or "Summary:" in out


def test_day4_pipeline_end_to_end_adhd_structure() -> None:
    profile = get_profile_config(Profile.ADHD)
    pipeline = TransformPipeline(profile=profile)
    sentence = "This paragraph provides background context about the architecture and implementation tradeoffs."
    long_block = " ".join([sentence for _ in range(30)])
    text = (
        f"{long_block}\n\n"
        "For example, the team can batch requests to reduce overhead and improve throughput.\n\n"
        "Therefore, the result is that we should prioritize a summary-first response format for users."
    )
    out = pipeline.transform(text)
    assert "Summary:" in out
    assert "Background:" in out
    assert "Example:" in out
