import { Profile, ProfileConfig, TransformModule } from "../types";

const CONJUNCTION_DELIMITERS = [", and", ", but", ", which", ", that"];
const WORD_RE = /\b\w+\b/g;

function wordCount(sentence: string): number {
  return (sentence.match(WORD_RE) || []).length;
}

function ensureTerminalPunctuation(text: string): string {
  if (!text) return text;
  return text.slice(-1).match(/[.!?]/) ? text : `${text}.`;
}

function normalizeSentenceStart(text: string): string {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Split long sentences at natural clause boundaries.
 *
 * Mirrors the Python pipeline's SentenceSimplifier: sentences longer than
 * maxSentenceWords are split at conjunction delimiters (", and", ", but",
 * ", which", ", that") and then at semicolons, with each part re-capitalized
 * and given terminal punctuation.
 */
export class SentenceSimplifier implements TransformModule {
  public readonly name = "SentenceSimplifier";

  public apply(text: string, profile: ProfileConfig, _profileId: Profile): string {
    if (!text.trim()) return "";

    return text
      .split(/\n\n+/)
      .map((paragraph) => {
        const sentences = splitSentences(paragraph);
        if (!sentences.length) return paragraph;
        const rebuilt: string[] = [];
        for (const sentence of sentences) {
          rebuilt.push(...this.simplifySentence(sentence, profile.maxSentenceWords));
        }
        return rebuilt.filter(Boolean).join(" ");
      })
      .join("\n\n");
  }

  private simplifySentence(sentence: string, maxWords: number): string[] {
    if (wordCount(sentence) <= maxWords) return [sentence];

    const result: string[] = [];
    let pending: string[] = [sentence];
    let iterations = 0;
    while (pending.length && iterations < 8) {
      const current = pending.shift()!.trim();
      iterations += 1;
      if (wordCount(current) <= maxWords) {
        result.push(current);
        continue;
      }
      const splitParts = this.splitOnce(current);
      if (splitParts.length === 1) {
        result.push(current);
        continue;
      }
      pending = [...splitParts, ...pending];
    }
    if (pending.length) result.push(...pending);
    return result;
  }

  private splitOnce(sentence: string): string[] {
    for (const delimiter of CONJUNCTION_DELIMITERS) {
      const parts = this.splitByDelimiter(sentence, delimiter);
      if (parts) return parts;
    }
    if (sentence.includes(";")) {
      const semicolonIndex = sentence.indexOf(";");
      const left = ensureTerminalPunctuation(sentence.slice(0, semicolonIndex).trim());
      const right = normalizeSentenceStart(sentence.slice(semicolonIndex + 1).trim());
      if (left && right) return [left, right];
    }
    return [sentence];
  }

  private splitByDelimiter(sentence: string, delimiter: string): string[] | null {
    const lower = sentence.toLowerCase();
    const position = lower.indexOf(delimiter);
    if (position === -1) return null;

    const left = sentence.slice(0, position).trim();
    let right = sentence.slice(position + delimiter.length).trim();
    if (!left || !right) return null;

    const conjunction = delimiter.replace(",", "").trim();
    if (!right.toLowerCase().startsWith(conjunction)) {
      right = `${conjunction} ${right}`;
    }

    const leftPart = ensureTerminalPunctuation(left);
    const rightPart = normalizeSentenceStart(right);
    if (!leftPart || !rightPart) return null;
    return [leftPart, rightPart];
  }
}

/**
 * Lightweight sentence splitting at .!?, preserving newlines between
 * paragraphs (handled by the caller) and keeping markup fragments attached
 * to their sentence, mirroring the Python _merge_markup_fragments behavior
 * for the common bold-span case.
 */
export function splitSentences(text: string): string[] {
  const parts = text.split(/([.!?])/);
  const raw: string[] = [];
  let current = "";
  for (let index = 0; index < parts.length; index += 1) {
    if (index % 2 === 0) {
      current += parts[index];
    } else {
      current += parts[index];
      const trimmed = current.trim();
      if (trimmed) raw.push(trimmed);
      current = "";
    }
  }
  const tail = current.trim();
  if (tail) raw.push(tail);

  // Re-attach fragments that carry no words (for example a lone "**") and
  // closing bold markers that belong to the previous sentence.
  const merged: string[] = [];
  let boldOpen = false;
  for (const fragment of raw) {
    if (!/\w/.test(fragment)) {
      if (merged.length) merged[merged.length - 1] += fragment;
      boldOpen = (fragment.split("**").length - 1 + (boldOpen ? 1 : 0)) % 2 === 1;
      continue;
    }
    if (boldOpen && fragment.startsWith("**")) {
      if (merged.length) merged[merged.length - 1] += "**";
      merged.push(fragment.slice(2).trim());
      boldOpen = false;
    } else {
      merged.push(fragment);
    }
    boldOpen = (fragment.split("**").length - 1) % 2 === 1;
  }
  return merged;
}
