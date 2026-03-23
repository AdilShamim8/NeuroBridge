"""Additional exception coverage tests."""

from neurobridge.exceptions import (
    LLMClientError,
    MemoryBackendError,
    ProfileNotSetError,
    TransformError,
)


def test_exception_messages_and_suggestions() -> None:
    profile_err = ProfileNotSetError()
    assert "set_profile" in str(profile_err)
    assert "built-in profile" in profile_err.suggestion.lower()

    llm_err = LLMClientError("network")
    assert "LLM client returned an error" in str(llm_err)

    transform_err = TransformError("chunker", "boom")
    assert "chunker" in str(transform_err)

    memory_err = MemoryBackendError()
    assert "memory backend" in memory_err.suggestion.lower()
