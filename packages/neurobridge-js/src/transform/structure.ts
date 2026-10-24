import { splitSentences } from "./sentenceSimplifier";

const CONCLUSION_HINTS = [
  "therefore",
  "in summary",
  "the result is",
  "this means",
  "ultimately",
  "the answer is",
];

const EXAMPLE_HINTS = ["for example", "such as", "consider", "for instance"];

function stripEmphasis(text: string): string {
  return text.replace(/\*\*/g, "");
}

function classifyParagraph(paragraph: string): "conclusion" | "example" | "background" {
  const lower = paragraph.toLowerCase();
  if (CONCLUSION_HINTS.some((hint) => lower.includes(hint))) {
    return "conclusion";
  }
  if (EXAMPLE_HINTS.some((hint) => lower.includes(hint))) {
    return "example";
  }
  return "background";
}

function extractSummarySentence(paragraph: string): string {
  const sentences = splitSentences(paragraph);
  if (sentences.length) {
    return sentences[0];
  }
  return paragraph.trim() || "Key details are provided below.";
}

function stripLeadingSentence(paragraph: string): string {
  const sentences = splitSentences(paragraph);
  if (sentences.length <= 1) {
    return "";
  }
  const remainder = sentences.slice(1).join(" ").trim();
  return remainder || "";
}

/**
 * Prefix a paragraph with a scanning label.
 *
 * Code fences must start at the beginning of a line to be recognized by
 * CommonMark renderers, so for fenced paragraphs the label goes on its own
 * line instead of sharing one with the fence.
 */
function labelParagraph(label: string, paragraph: string): string {
  if (paragraph.replace(/^\s+/, "").startsWith("```")) {
    return `${label}:\n${paragraph}`;
  }
  return `${label}: ${paragraph}`;
}

/**
 * Reorder paragraphs into an inverted-pyramid structure for the ADHD
 * profile.
 *
 * Full port of the Python `PriorityReorderer`: conclusion-like paragraphs
 * become "Summary:", example-like paragraphs become "Example:", everything
 * else is labeled "Background:", and when no explicit conclusion exists the
 * first sentence of the final paragraph is promoted to a bolded
 * "Bottom line:" while the remainder of that paragraph stays in the body
 * without being duplicated. A single-paragraph input is split into
 * sentences first so the takeaway still surfaces.
 */
export function reorderByPriority(text: string): string {
  if (!text.trim()) return "";

  let paragraphs = text
    .trim()
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
  if (!paragraphs.length) return text;

  if (paragraphs.length === 1) {
    const sentenceUnits = splitSentences(paragraphs[0]).filter(Boolean);
    if (sentenceUnits.length > 1) {
      paragraphs = sentenceUnits;
    }
  }

  const conclusions: string[] = [];
  const backgrounds: string[] = [];
  const examples: string[] = [];
  let lastParagraphIsBackground = false;

  paragraphs.forEach((paragraph, index) => {
    const kind = classifyParagraph(paragraph);
    if (kind === "conclusion") {
      conclusions.push(`Summary: ${paragraph}`);
    } else if (kind === "example") {
      examples.push(labelParagraph("Example", paragraph));
    } else {
      backgrounds.push(labelParagraph("Background", paragraph));
      lastParagraphIsBackground = index === paragraphs.length - 1;
    }
  });

  const result: string[] = [];
  if (conclusions.length) {
    result.push(...conclusions);
  } else {
    const summarySentence = stripEmphasis(extractSummarySentence(paragraphs[paragraphs.length - 1]));
    result.push(`**Bottom line: ${summarySentence}**`);
    const remainder = stripLeadingSentence(paragraphs[paragraphs.length - 1]);
    if (lastParagraphIsBackground) {
      if (remainder) {
        backgrounds[backgrounds.length - 1] = labelParagraph("Background", remainder);
      } else {
        backgrounds.pop();
      }
    } else if (remainder) {
      result.push(labelParagraph("Background", remainder));
    }
  }
  result.push(...backgrounds);
  result.push(...examples);

  return result.join("\n\n").trim();
}
