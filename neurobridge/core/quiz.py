"""Profile quiz engine for cognitive profile recommendation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Dict, Optional, Tuple

from neurobridge.core.profile import Profile, ProfileConfig, get_profile_config


@dataclass(frozen=True)
class QuizOption:
    """An answer option with weighted score deltas per profile."""

    text: str
    scores: Dict[str, float]


@dataclass(frozen=True)
class QuizQuestion:
    """A quiz question used to infer a cognitive profile."""

    id: str
    prompt: str
    options: Tuple[QuizOption, ...]
    weight: float


@dataclass(frozen=True)
class QuizResult:
    """Final quiz output with primary and optional secondary profile."""

    primary_profile: Profile
    secondary_profile: Optional[Profile]
    confidence: float
    scores: Dict[str, float]
    recommended_config: ProfileConfig


class ProfileBlender:
    """Blend two profile configs while preserving primary profile semantics."""

    @staticmethod
    def blend(
        primary: ProfileConfig, secondary: ProfileConfig, weight: float = 0.3
    ) -> ProfileConfig:
        if weight < 0 or weight > 1:
            raise ValueError("weight must be between 0 and 1")

        def weighted_int(primary_value: int, secondary_value: int) -> int:
            value = round((1 - weight) * primary_value + weight * secondary_value)
            return max(1, value)

        blended = ProfileConfig(
            chunk_size=weighted_int(primary.chunk_size, secondary.chunk_size),
            tone=primary.tone,
            ambiguity_resolution=primary.ambiguity_resolution,
            number_format=primary.number_format,
            leading_style=primary.leading_style,
            reading_level=weighted_int(primary.reading_level, secondary.reading_level),
            max_sentence_words=weighted_int(
                primary.max_sentence_words, secondary.max_sentence_words
            ),
        )
        blended.validate()
        return blended


class QuizEngine:
    """Interactive and programmatic quiz engine for profile inference."""

    QUESTIONS: Tuple[QuizQuestion, ...] = (
        QuizQuestion(
            id="q1",
            prompt="Long walls of text without breaks make me feel...",
            options=(
                QuizOption("Overwhelmed and I lose focus", {"ADHD": 1.0, "DYSLEXIA": 0.7}),
                QuizOption("I can read them if literal and clear", {"AUTISM": 0.6}),
                QuizOption("Anxious, especially with urgent language", {"ANXIETY": 0.8}),
            ),
            weight=1.2,
        ),
        QuizQuestion(
            id="q2",
            prompt="When instructions include idioms or metaphors, I prefer...",
            options=(
                QuizOption("Literal wording", {"AUTISM": 1.0}),
                QuizOption("Short, direct bullets", {"ADHD": 0.7, "DYSLEXIA": 0.5}),
                QuizOption("Gentle, reassuring framing", {"ANXIETY": 0.5}),
            ),
            weight=1.0,
        ),
        QuizQuestion(
            id="q3",
            prompt="Numbers in text are easiest when they are...",
            options=(
                QuizOption("Explained with context and examples", {"DYSCALCULIA": 1.0}),
                QuizOption("Short and grouped in clear blocks", {"ADHD": 0.4, "DYSLEXIA": 0.4}),
                QuizOption("Minimal and calm", {"ANXIETY": 0.3}),
            ),
            weight=1.1,
        ),
        QuizQuestion(
            id="q4",
            prompt="I process information best when the answer starts with...",
            options=(
                QuizOption("The key point first", {"ADHD": 1.0}),
                QuizOption("Precise definitions", {"AUTISM": 0.8}),
                QuizOption("A reassuring summary", {"ANXIETY": 0.7}),
            ),
            weight=1.0,
        ),
        QuizQuestion(
            id="q5",
            prompt="Reading speed and comfort improve for me when sentences are...",
            options=(
                QuizOption("Short and single-idea", {"DYSLEXIA": 1.0, "ADHD": 0.5}),
                QuizOption("Detailed but unambiguous", {"AUTISM": 0.6}),
                QuizOption("Calm and supportive", {"ANXIETY": 0.4}),
            ),
            weight=1.0,
        ),
        QuizQuestion(
            id="q6",
            prompt='I react to urgent wording like "ASAP" by feeling...',
            options=(
                QuizOption("Stressed or pressured", {"ANXIETY": 1.0}),
                QuizOption("Distracted from the task", {"ADHD": 0.5}),
                QuizOption("Mostly unaffected", {"AUTISM": 0.2}),
            ),
            weight=1.1,
        ),
        QuizQuestion(
            id="q7",
            prompt="For multi-step tasks, I prefer output that is...",
            options=(
                QuizOption("Chunked into clear sections", {"ADHD": 0.9, "DYSLEXIA": 0.6}),
                QuizOption("Strictly structured and explicit", {"AUTISM": 0.8}),
                QuizOption("Short with one next step", {"ANXIETY": 0.5}),
            ),
            weight=1.0,
        ),
        QuizQuestion(
            id="q8",
            prompt="When information is ambiguous, I need...",
            options=(
                QuizOption("Explicit details and no implied meaning", {"AUTISM": 1.0}),
                QuizOption("A concise summary to stay on track", {"ADHD": 0.6}),
                QuizOption("Simple wording and spacing", {"DYSLEXIA": 0.5}),
            ),
            weight=1.2,
        ),
        QuizQuestion(
            id="q9",
            prompt="If an answer is very long, what helps most?",
            options=(
                QuizOption("Top takeaway plus bullet points", {"ADHD": 1.0}),
                QuizOption("Short paragraphs and plain language", {"DYSLEXIA": 0.8}),
                QuizOption("Consistent, predictable structure", {"AUTISM": 0.6}),
            ),
            weight=1.0,
        ),
        QuizQuestion(
            id="q10",
            prompt="I understand percentages best when they are...",
            options=(
                QuizOption("Converted to relatable comparisons", {"DYSCALCULIA": 1.0}),
                QuizOption("Shown briefly in a summary", {"ADHD": 0.4}),
                QuizOption("Optional detail after the main point", {"ANXIETY": 0.3}),
            ),
            weight=1.1,
        ),
        QuizQuestion(
            id="q11",
            prompt="I find passive voice and dense prose...",
            options=(
                QuizOption("Hard to parse quickly", {"DYSLEXIA": 0.8, "ADHD": 0.5}),
                QuizOption("Acceptable if exact and literal", {"AUTISM": 0.4}),
                QuizOption("Potentially stressful", {"ANXIETY": 0.3}),
            ),
            weight=0.9,
        ),
        QuizQuestion(
            id="q12",
            prompt="For error explanations, I prefer tone that is...",
            options=(
                QuizOption("Neutral and calm", {"ANXIETY": 1.0}),
                QuizOption("Direct and concise", {"ADHD": 0.6}),
                QuizOption("Literal and exact", {"AUTISM": 0.5}),
            ),
            weight=1.0,
        ),
        QuizQuestion(
            id="q13",
            prompt="I retain information best when text includes...",
            options=(
                QuizOption("Visual spacing and shorter lines", {"DYSLEXIA": 1.0}),
                QuizOption("Prioritized ordering", {"ADHD": 0.7}),
                QuizOption("Precise definitions", {"AUTISM": 0.4}),
            ),
            weight=1.0,
        ),
        QuizQuestion(
            id="q14",
            prompt="How do you feel about many options listed at once?",
            options=(
                QuizOption("Overwhelmed; I prefer one clear recommendation", {"ANXIETY": 0.9}),
                QuizOption("Distracted; I prefer a prioritized list", {"ADHD": 0.7}),
                QuizOption("Fine if format is consistent", {"AUTISM": 0.4}),
            ),
            weight=0.9,
        ),
        QuizQuestion(
            id="q15",
            prompt="The output style that helps me most is...",
            options=(
                QuizOption("Fast-scannable and summary-first", {"ADHD": 1.0}),
                QuizOption("Literal and unambiguous", {"AUTISM": 0.9}),
                QuizOption("Readable, spacious, and plain", {"DYSLEXIA": 0.9}),
                QuizOption("Calm, non-urgent, and guided", {"ANXIETY": 0.9}),
                QuizOption("Number-explained and context-rich", {"DYSCALCULIA": 0.9}),
            ),
            weight=1.3,
        ),
    )

    def run_cli(self) -> QuizResult:
        """Run an interactive CLI quiz and return a scored result."""
        print("NeuroBridge Profile Quiz")
        print("Answer each question by entering the option number.\n")

        answers: Dict[str, int] = {}
        for index, question in enumerate(self.QUESTIONS, start=1):
            print(f"Q{index}. {question.prompt}")
            for option_index, option in enumerate(question.options, start=1):
                print(f"  {option_index}. {option.text}")
            selected = self._prompt_option(len(question.options))
            answers[question.id] = selected
            print("")

        result = self.score_answers(answers)
        print(f"Primary profile: {result.primary_profile.value}")
        if result.secondary_profile is not None:
            print(f"Secondary profile: {result.secondary_profile.value}")
        print(f"Confidence: {result.confidence:.2f}")
        return result

    def from_answers_json(self, json_str: str) -> QuizResult:
        """Score quiz answers from a JSON payload.

        Accepted format:
        {"answers": {"q1": 1, "q2": 0, ...}}
        where values are zero-based option indices.
        """
        try:
            payload = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON payload for answers") from exc

        answers = payload.get("answers") if isinstance(payload, dict) else None
        if not isinstance(answers, dict):
            raise ValueError("JSON payload must contain an 'answers' object")

        normalized: Dict[str, int] = {}
        for question in self.QUESTIONS:
            if question.id not in answers:
                raise ValueError(f"Missing answer for question: {question.id}")
            raw_index = answers[question.id]
            if not isinstance(raw_index, int):
                raise ValueError(f"Answer index for {question.id} must be an integer")
            normalized[question.id] = raw_index
        return self.score_answers(normalized)

    def score_answers(self, answers: Dict[str, int]) -> QuizResult:
        """Score answer indices and compute primary/secondary profile recommendation."""
        score_map: Dict[str, float] = {
            Profile.ADHD.name: 0.0,
            Profile.AUTISM.name: 0.0,
            Profile.DYSLEXIA.name: 0.0,
            Profile.ANXIETY.name: 0.0,
            Profile.DYSCALCULIA.name: 0.0,
        }

        for question in self.QUESTIONS:
            if question.id not in answers:
                raise ValueError(f"Missing answer for question: {question.id}")
            option_index = answers[question.id]
            if option_index < 0 or option_index >= len(question.options):
                raise ValueError(f"Invalid option index for question {question.id}: {option_index}")
            option = question.options[option_index]
            for profile_name, delta in option.scores.items():
                if profile_name not in score_map:
                    continue
                score_map[profile_name] += question.weight * float(delta)

        ranked = sorted(score_map.items(), key=lambda item: item[1], reverse=True)
        primary_name, primary_score = ranked[0]
        secondary_name, secondary_score = ranked[1]

        primary_profile = Profile[primary_name]
        secondary_profile: Optional[Profile] = None
        if primary_score > 0 and secondary_score / primary_score >= 0.7:
            secondary_profile = Profile[secondary_name]

        total = sum(score_map.values())
        confidence = primary_score / total if total > 0 else 0.0

        primary_config = get_profile_config(primary_profile)
        recommended = primary_config
        if secondary_profile is not None:
            secondary_config = get_profile_config(secondary_profile)
            recommended = ProfileBlender.blend(primary_config, secondary_config, weight=0.3)

        return QuizResult(
            primary_profile=primary_profile,
            secondary_profile=secondary_profile,
            confidence=confidence,
            scores=score_map,
            recommended_config=recommended,
        )

    @staticmethod
    def _prompt_option(max_option: int) -> int:
        while True:
            raw = input(f"Choose 1-{max_option}: ").strip()
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= max_option:
                    return value - 1
            print("Invalid selection. Please try again.")


class ProfileQuiz:
    """Public quiz facade used by package-level imports."""

    @staticmethod
    def run(user_id: Optional[str] = None) -> Profile:
        """Run the CLI quiz and return the detected primary profile."""
        _ = user_id
        return QuizEngine().run_cli().primary_profile
