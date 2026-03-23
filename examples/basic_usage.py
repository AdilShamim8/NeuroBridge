"""Day 7 usage examples for NeuroBridge."""

from neurobridge import CustomProfile, NeuroBridge, Profile, ProfileQuiz
from neurobridge.integrations.openai import wrap


def example_basic_two_line() -> None:
    bridge = NeuroBridge(llm_client=None)
    bridge.set_profile(Profile.ADHD)
    response = bridge.chat("Explain how machine learning works.")
    print("[basic]", response.adapted_text)


def example_with_memory_user_id() -> None:
    bridge = NeuroBridge()
    bridge.set_profile(Profile.DYSLEXIA)
    response = bridge.chat("Explain rate limiting strategies.", user_id="demo-user")
    print("[memory]", response.adapted_text)


def example_with_quiz_detection() -> None:
    bridge = NeuroBridge()
    detected = ProfileQuiz.run(user_id="quiz-demo")
    bridge.set_profile(detected)
    response = bridge.chat("Help me plan this bugfix task.")
    print("[quiz]", response.adapted_text)


def example_openai_wrap(client: object) -> None:
    adapted_client = wrap(client, profile=Profile.ANXIETY)
    _ = adapted_client
    print("[openai] client wrapped successfully")


def example_custom_profile() -> None:
    custom = CustomProfile(
        chunk_size=2,
        tone="calm",
        ambiguity_resolution="explicit",
        number_format="contextual",
        leading_style="summary_first",
        reading_level=6,
        max_sentence_words=12,
    )
    bridge = NeuroBridge()
    bridge.set_profile(custom)
    response = bridge.chat("Summarize this architecture proposal.")
    print("[custom]", response.adapted_text)

if __name__ == "__main__":
    example_basic_two_line()
    example_with_memory_user_id()
    example_custom_profile()
