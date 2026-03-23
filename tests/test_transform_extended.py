"""Day 22 extended transform coverage and edge-case tests."""

from __future__ import annotations

from neurobridge.core.profile import Profile, get_profile_config
from neurobridge.core.transform import TransformPipeline


def test_transform_handles_one_word_input() -> None:
    pipeline = TransformPipeline(profile=get_profile_config(Profile.ADHD))
    out = pipeline.transform("Hello")
    assert out


def test_transform_handles_very_long_input_10000_words() -> None:
    pipeline = TransformPipeline(profile=get_profile_config(Profile.DYSLEXIA))
    text = " ".join(["word"] * 10_000) + "."
    out = pipeline.transform(text)
    assert len(out) > 0


def test_transform_handles_only_numbers_for_dyscalculia() -> None:
    pipeline = TransformPipeline(profile=get_profile_config(Profile.DYSCALCULIA))
    out = pipeline.transform("100 250 3900 42% 0.003")
    assert "(" in out


def test_transform_preserves_code_block_content() -> None:
    pipeline = TransformPipeline(profile=get_profile_config(Profile.ANXIETY))
    source = """```python
for i in range(3):
    print(i)
```"""
    out = pipeline.transform(source)
    assert "for i in range(3):" in out
    assert "print(i)" in out


def test_transform_preserves_markdown_table_syntax() -> None:
    pipeline = TransformPipeline(profile=get_profile_config(Profile.AUTISM))
    source = "| Name | Value |\n| --- | --- |\n| Latency | 120ms |"
    out = pipeline.transform(source)
    assert "| Name | Value |" in out
    assert "| --- | --- |" in out


def test_transform_handles_unicode_text_arabic_chinese_japanese_hindi_emoji() -> None:
    pipeline = TransformPipeline(profile=get_profile_config(Profile.AUTISM))
    text = "مرحبا بالعالم. 你好，世界。こんにちは世界。नमस्ते दुनिया।🙂"
    out = pipeline.transform(text)
    assert out


def test_transform_is_idempotent_for_stable_input() -> None:
    pipeline = TransformPipeline(profile=get_profile_config(Profile.ANXIETY))
    text = "This is critical and you must complete this ASAP."
    once = pipeline.transform(text)
    twice = pipeline.transform(once)
    assert once == twice
