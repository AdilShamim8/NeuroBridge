"""Output format adapters for transformed NeuroBridge content."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import re
from html import escape
from typing import Any, Dict, List, Sequence, Tuple

from neurobridge.core.profile import Profile, ProfileConfig

_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
_HEADING_RE = re.compile(r"^(#{1,6})\s*(.+)$")
_IMAGE_RE = re.compile(r"!\[(.*?)\]\((.*?)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_EM_RE = re.compile(r"\*(.+?)\*")
_CODE_FENCE_RE = re.compile(r"```(\w+)?\n([\s\S]*?)```", re.MULTILINE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_ACRONYM_REPLACEMENTS = {
    "AI": "A.I.",
    "API": "A.P.I.",
    "URL": "U.R.L.",
}


class BaseFormatAdapter(ABC):
    """Base class for output format adapters."""

    media_type: str = "text/plain"

    @abstractmethod
    def format(self, text: str, profile: ProfileConfig) -> str:
        """Convert transformed text to the adapter output format."""


class MarkdownAdapter(BaseFormatAdapter):
    """Normalize and clean Markdown output from the transform pipeline."""

    media_type = "text/markdown"

    def format(self, text: str, profile: ProfileConfig) -> str:
        _ = profile
        if not text.strip():
            return ""

        lines = text.splitlines()
        normalized: List[str] = []
        for line in lines:
            heading = _HEADING_RE.match(line)
            if heading:
                hashes, content = heading.groups()
                normalized.append(f"{hashes} {content.strip()}")
                continue
            normalized.append(line.rstrip())

        content = "\n".join(normalized)

        # Ensure code fences include a language hint.
        content = re.sub(r"```\n", "```text\n", content)

        # Ensure images include a basic accessible alt hint.
        def image_repl(match: re.Match[str]) -> str:
            alt = match.group(1).strip() or "Image description"
            src = match.group(2)
            if "aria-label" not in alt.lower():
                alt = f"{alt} (aria-label: {alt})"
            return f"![{alt}]({src})"

        content = _IMAGE_RE.sub(image_repl, content)
        return content.strip() + "\n"


class HTMLAdapter(BaseFormatAdapter):
    """Convert Markdown-like text into portable semantic HTML."""

    media_type = "text/html"

    def format(self, text: str, profile: ProfileConfig) -> str:
        markdown = MarkdownAdapter().format(text, profile)
        blocks = _parse_blocks(markdown)
        sections = self._render_blocks(blocks, profile)

        css = self._css_block()
        body_classes = ["nb-output"]
        profile_name = _detect_profile_name(profile)
        if profile_name == Profile.DYSLEXIA:
            body_classes.append("nb-dyslexia")
        if profile_name == Profile.ANXIETY:
            body_classes.append("nb-gentle")

        html = (
            "<html><head>"
            f"<style>{css}</style>"
            "</head>"
            f"<body class=\"{' '.join(body_classes)}\">"
            '<div class="neurobridge-output">'
            '<article role="main" aria-label="Adapted content">'
            '<nav role="navigation" aria-label="content navigation"></nav>'
            f"{sections}"
            "</article>"
            "</div>"
            "</body></html>"
        )
        return html

    def _render_blocks(self, blocks: Sequence[Tuple[str, str]], profile: ProfileConfig) -> str:
        profile_name = _detect_profile_name(profile)
        rendered: List[str] = []
        total = len([b for b in blocks if b[0] != "heading"])
        index = 0
        in_list = False

        for block_type, value in blocks:
            if block_type == "heading":
                if in_list:
                    rendered.append("</ul>")
                    in_list = False
                rendered.append(f'<section><h2 aria-label="Heading">{escape(value)}</h2></section>')
                continue

            if block_type == "list_item":
                if not in_list:
                    rendered.append("<section><ul>")
                    in_list = True
                rendered.append(f"<li>{self._inline_html(value)}</li>")
                continue

            if in_list:
                rendered.append("</ul></section>")
                in_list = False

            if block_type == "code":
                rendered.append(f"<section><pre><code>{escape(value)}</code></pre></section>")
                continue

            index += 1
            paragraph_html = f"<p>{self._inline_html(value)}</p>"
            if profile_name == Profile.ADHD:
                progress = f"Part {index} of {max(1, total)}"
                rendered.append(
                    '<section class="nb-chunk">'
                    f'<span class="nb-progress">{escape(progress)}</span>{paragraph_html}'
                    "</section>"
                )
            else:
                rendered.append(f"<section>{paragraph_html}</section>")

        if in_list:
            rendered.append("</ul></section>")

        return "".join(rendered)

    @staticmethod
    def _inline_html(text: str) -> str:
        safe = escape(text)
        safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
        safe = re.sub(r"\*(.+?)\*", r"<em>\1</em>", safe)
        return safe

    @staticmethod
    def _css_block() -> str:
        return (
            ".neurobridge-output{max-width:860px;margin:0 auto;padding:16px;}"
            ".nb-chunk{margin-bottom:14px;padding:10px;border-radius:8px;background:#f8f8fb;}"
            ".nb-progress{display:inline-block;font-size:12px;color:#444;margin-bottom:6px;}"
            ".nb-dyslexia{line-height:1.8;letter-spacing:.05em;}"
            ".nb-gentle h1,.nb-gentle h2{font-size:1.2em;font-weight:600;}"
        )


class PlainTextAdapter(BaseFormatAdapter):
    """Convert markdown-like text into accessible plain text."""

    media_type = "text/plain"

    def format(self, text: str, profile: ProfileConfig) -> str:
        _ = profile
        if not text.strip():
            return ""

        output = text
        output = re.sub(
            r"^##\s*(.+)$", lambda m: f"{m.group(1)}\n----------", output, flags=re.MULTILINE
        )
        output = _BOLD_RE.sub(lambda m: m.group(1).upper(), output)
        output = _EM_RE.sub(lambda m: m.group(1), output)
        output = re.sub(r"^\s*-\s+", "• ", output, flags=re.MULTILINE)
        output = re.sub(r"^\s*\d+\.\s+", "• ", output, flags=re.MULTILINE)
        output = re.sub(r"^#{1,6}\s*", "", output, flags=re.MULTILINE)
        output = output.replace("```", "")
        output = _IMAGE_RE.sub(lambda m: m.group(1), output)
        output = re.sub(r"\n{3,}", "\n\n", output)
        return output.strip()


class JSONAdapter(BaseFormatAdapter):
    """Return structured JSON payload suitable for custom UI rendering."""

    media_type = "application/json"

    def format(self, text: str, profile: ProfileConfig) -> str:
        blocks = _parse_blocks(text)
        payload_blocks: List[Dict[str, Any]] = []
        adapted_word_count = 0

        for index, (block_type, value) in enumerate(blocks):
            mapped = self._map_block_type(block_type, value)
            word_count = len(_WORD_RE.findall(value))
            adapted_word_count += word_count
            payload_blocks.append(
                {
                    "type": mapped,
                    "text": value,
                    "index": index,
                    "word_count": word_count,
                }
            )

        total_chunks = len(
            [item for item in payload_blocks if item["type"] in {"chunk", "summary", "example"}]
        )
        reading_time_seconds = int((adapted_word_count / 180.0) * 60)
        profile_name = _detect_profile_name(profile)
        payload = {
            "profile": profile_name.value,
            "blocks": payload_blocks,
            "metadata": {
                "total_chunks": total_chunks,
                "reading_time_seconds": max(1, reading_time_seconds),
                "transforms_applied": [
                    "chunker",
                    "sentence_simplifier",
                    "tone_rewriter",
                    "number_contextualiser",
                    "priority_reorderer",
                ],
                "original_word_count": adapted_word_count,
                "adapted_word_count": adapted_word_count,
            },
        }
        return json.dumps(payload, ensure_ascii=True)

    @staticmethod
    def _map_block_type(block_type: str, text: str) -> str:
        lowered = text.lower()
        if block_type == "heading":
            return "heading"
        if block_type == "code":
            return "code"
        if lowered.startswith("summary:") or lowered.startswith("bottom line"):
            return "summary"
        if lowered.startswith("example:"):
            return "example"
        return "chunk"


class TTSAdapter(BaseFormatAdapter):
    """Convert text into speech-friendly plain text with lightweight SSML hints."""

    media_type = "text/plain"

    def format(self, text: str, profile: ProfileConfig) -> str:
        _ = profile
        if not text.strip():
            return ""

        content = text
        content = _CODE_FENCE_RE.sub(lambda m: m.group(2), content)
        content = _HTML_TAG_RE.sub("", content)
        content = re.sub(
            r"^#{1,6}\s*(.+)$",
            lambda m: f"<!-- heading --> {m.group(1)} <!-- pause 500ms -->",
            content,
            flags=re.MULTILINE,
        )
        content = _BOLD_RE.sub(lambda m: m.group(1), content)
        content = _EM_RE.sub(lambda m: m.group(1), content)
        content = _IMAGE_RE.sub(lambda m: m.group(1), content)

        for token, spoken in _ACRONYM_REPLACEMENTS.items():
            content = re.sub(rf"\b{token}\b", spoken, content)

        content = re.sub(r"\$(\d+(?:\.\d+)?)\s*[mM]\b", r"\1 million dollars", content)
        content = re.sub(r"\$(\d+(?:\.\d+)?)\b", r"\1 dollars", content)
        content = re.sub(r"\b42\b", "forty-two", content)

        content = content.replace("%", " percent")
        content = content.replace("&", " and ")
        content = content.replace("+", " plus ")

        content = re.sub(r"\s{2,}", " ", content)
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip()


def _detect_profile_name(profile: ProfileConfig) -> Profile:
    for profile_name, config in {
        Profile.ADHD: ProfileConfig(3, "clear", "balanced", "contextual", "summary_first", 7, 16),
        Profile.AUTISM: ProfileConfig(2, "neutral", "explicit", "raw", "detail_first", 8, 18),
        Profile.DYSLEXIA: ProfileConfig(
            2, "calm", "explicit", "contextual", "summary_first", 5, 12
        ),
        Profile.ANXIETY: ProfileConfig(
            3, "calm", "explicit", "contextual", "reassure_first", 6, 14
        ),
        Profile.DYSCALCULIA: ProfileConfig(3, "clear", "balanced", "contextual", "stepwise", 6, 15),
    }.items():
        if profile == config:
            return profile_name
    return Profile.CUSTOM


def _parse_blocks(text: str) -> List[Tuple[str, str]]:
    if not text.strip():
        return []

    blocks: List[Tuple[str, str]] = []
    lines = text.splitlines()
    in_code = False
    code_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                blocks.append(("code", "\n".join(code_lines).strip()))
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            blocks.append(("heading", heading_match.group(2).strip()))
            continue

        if stripped.startswith("- "):
            blocks.append(("list_item", stripped[2:].strip()))
            continue

        if not stripped:
            continue
        blocks.append(("paragraph", stripped))

    return blocks
