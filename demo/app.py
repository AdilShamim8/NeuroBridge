"""Gradio demo app for NeuroBridge HuggingFace Space."""

from __future__ import annotations

from pathlib import Path
import json
from time import perf_counter
from typing import Any, Dict, List, Sequence, Tuple

import gradio as gr

from neurobridge import NeuroBridge, Profile
from neurobridge.core.quiz import QuizEngine

TITLE = "NeuroBridge - Try Cognitive Accessibility for AI"

PROFILE_LABELS: Dict[str, Profile] = {
    "ADHD": Profile.ADHD,
    "Autism": Profile.AUTISM,
    "Dyslexia": Profile.DYSLEXIA,
    "Anxiety": Profile.ANXIETY,
    "Dyscalculia": Profile.DYSCALCULIA,
}

OUTPUT_FORMATS = ["Markdown", "Plain Text", "JSON"]
SHOWCASE_DIR = Path(__file__).parent / "showcase"


def _read_showcase_text(name: str) -> str:
    path = SHOWCASE_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _build_examples() -> List[List[str]]:
    return [
        [_read_showcase_text("original_adhd.txt"), "ADHD", "Markdown"],
        [_read_showcase_text("original_autism.txt"), "Autism", "Markdown"],
        [_read_showcase_text("original_dyslexia.txt"), "Dyslexia", "Markdown"],
        [_read_showcase_text("original_anxiety.txt"), "Anxiety", "Plain Text"],
        [_read_showcase_text("original_dyscalculia.txt"), "Dyscalculia", "JSON"],
    ]


def adapt_text(text: str, profile_label: str, output_format: str) -> Tuple[str, Dict[str, Any]]:
    if not text or not text.strip():
        return "Please paste text before adapting.", {"transforms_applied": [], "processing_time_ms": 0}

    bridge = NeuroBridge()
    bridge.set_profile(PROFILE_LABELS.get(profile_label, Profile.ADHD))

    started = perf_counter()
    response = bridge.chat(text)
    elapsed_ms = round((perf_counter() - started) * 1000, 2)

    adapted = response.adapted_text
    if output_format == "JSON":
        rendered = "```json\n" + json.dumps(
            {
                "profile": profile_label,
                "adapted_text": adapted,
            },
            ensure_ascii=True,
            indent=2,
        ) + "\n```"
    elif output_format == "Plain Text":
        rendered = adapted
    else:
        rendered = adapted

    meta = {
        "transforms_applied": response.modules_run,
        "processing_time_ms": response.processing_ms or elapsed_ms,
    }
    return rendered, meta


def _code_template(profile_label: str) -> str:
    enum_name = profile_label.upper()
    return f'''from neurobridge import NeuroBridge, Profile

text = "Explain this release plan with clear steps and calm tone."

bridge = NeuroBridge()
bridge.set_profile(Profile.{enum_name})

response = bridge.chat(text)
print(response.adapted_text)
print(response.modules_run)
'''


def code_for_profile(profile_label: str) -> str:
    return _code_template(profile_label)


def _quiz_option_choices(question_index: int, engine: QuizEngine) -> List[str]:
    question = engine.QUESTIONS[question_index]
    return [option.text for option in question.options]


def score_quiz(*selected_texts: str) -> Tuple[str, List[Tuple[str, str]]]:
    engine = QuizEngine()
    answers: Dict[str, int] = {}

    for i, question in enumerate(engine.QUESTIONS):
        selected = selected_texts[i] if i < len(selected_texts) else None
        if not selected:
            return (
                f"Please answer question {i + 1} before scoring.",
                [("Missing answer", "warning")],
            )

        options = [opt.text for opt in question.options]
        try:
            selected_index = options.index(selected)
        except ValueError:
            return (
                f"Invalid selection for question {i + 1}.",
                [("Invalid option", "warning")],
            )
        answers[question.id] = selected_index

    result = engine.score_answers(answers)
    profile_name = result.primary_profile.value
    confidence = round(result.confidence * 100, 1)

    summary = (
        f"Recommended profile: {profile_name}\n"
        f"Confidence: {confidence}%\n"
        f"Secondary profile: {result.secondary_profile.value if result.secondary_profile else 'None'}"
    )

    highlighted = [
        ("Recommended profile: ", "label"),
        (profile_name, "profile"),
        (f" ({confidence}% confidence)", "label"),
    ]
    return summary, highlighted


def build_quiz_components(engine: QuizEngine) -> Sequence[gr.Radio]:
    radios: List[gr.Radio] = []
    for index, question in enumerate(engine.QUESTIONS):
        radios.append(
            gr.Radio(
                choices=_quiz_option_choices(index, engine),
                label=f"Q{index + 1}. {question.prompt}",
                value=None,
            )
        )
    return radios


def build_app() -> gr.Blocks:
    engine = QuizEngine()
    examples = _build_examples()

    with gr.Blocks(title=TITLE) as demo:
        gr.Markdown(
            "# NeuroBridge - Try Cognitive Accessibility for AI\n"
            "Adapt AI output by cognitive profile, run a profile quiz, and copy integration code."
        )

        with gr.Tabs():
            with gr.Tab("Adapt Text"):
                input_text = gr.Textbox(label="Paste any AI output", lines=8)
                profile = gr.Radio(
                    choices=list(PROFILE_LABELS.keys()),
                    value="ADHD",
                    label="Profile",
                )
                output_format = gr.Dropdown(OUTPUT_FORMATS, value="Markdown", label="Output format")
                adapt_btn = gr.Button("Adapt")
                adapted_output = gr.Markdown(label="Adapted output")
                meta_output = gr.JSON(label="Transforms + timing")

                adapt_btn.click(
                    fn=adapt_text,
                    inputs=[input_text, profile, output_format],
                    outputs=[adapted_output, meta_output],
                )

                gr.Examples(
                    examples=examples,
                    inputs=[input_text, profile, output_format],
                    outputs=[adapted_output, meta_output],
                    fn=adapt_text,
                    cache_examples=False,
                    label="Load examples",
                )

            with gr.Tab("Profile Quiz"):
                radios = build_quiz_components(engine)
                quiz_btn = gr.Button("Get My Profile")
                quiz_summary = gr.Markdown()
                quiz_highlight = gr.HighlightedText(
                    label="Recommendation",
                    color_map={
                        "profile": "#7F77DD",
                        "label": "#B9B5E3",
                        "warning": "#E89BA4",
                    },
                )
                quiz_btn.click(fn=score_quiz, inputs=list(radios), outputs=[quiz_summary, quiz_highlight])

            with gr.Tab("Code Example"):
                code_profile = gr.Radio(
                    choices=list(PROFILE_LABELS.keys()),
                    value="ADHD",
                    label="Profile",
                )
                code_block = gr.Code(
                    value=_code_template("ADHD"),
                    language="python",
                    label="10-line integration example",
                )
                code_profile.change(fn=code_for_profile, inputs=[code_profile], outputs=[code_block])

        gr.Markdown(
            "### Links\n"
            "- GitHub: https://github.com/yourusername/neurobridge\n"
            "- Website: https://neurobridge.dev\n"
            "- PyPI: https://pypi.org/project/neurobridge/\n"
            "- Discord: https://discord.gg/neurobridge"
        )

    return demo


app = build_app()

if __name__ == "__main__":
    app.launch()
