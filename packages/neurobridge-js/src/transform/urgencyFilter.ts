import { Profile, ProfileConfig, TransformModule } from "../types";
import { splitSentences } from "./sentenceSimplifier";
import { ANXIETY_REPLACEMENTS, URGENCY_WORDS } from "./urgency";
import { mapUnprotectedRegions } from "./protect";

const CAPS_WORD_RE = /\b[A-Z]{3,}\b/g;
const EXCLAMATION_RE = /!+/g;
const NEGATIVE_EMOTION_RE =
  /\b(critical|panic|danger|catastrophic|severe|failure|broken|wrong)\b/gi;
const IMPERATIVE_START_RE =
  /^\s*(fix|do|send|finish|complete|respond|submit|update|review|act|resolve)\b/i;

function countMatches(text: string, pattern: RegExp): number {
  const global = new RegExp(pattern.source, pattern.flags.includes("g") ? pattern.flags : `${pattern.flags}g`);
  return (text.match(global) || []).length;
}

function replaceWord(text: string, source: string, target: string): string {
  const escaped = source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return text.replace(new RegExp(`\\b${escaped}\\b`, "gi"), target);
}

/**
 * Score a sentence's urgency intensity, mirroring the Python pipeline.
 *
 * Caps words and exclamation marks contribute up to 2 points each, urgency
 * vocabulary up to 3, negative-emotion words up to 2, and an imperative
 * opening verb adds 2; the total is capped at 10.
 */
export function scoreSentenceUrgency(sentence: string): number {
  let score = 0;
  score += Math.min(2, countMatches(sentence, CAPS_WORD_RE));
  score += Math.min(2, countMatches(sentence, EXCLAMATION_RE));
  score += Math.min(3, countMatches(sentence, new RegExp(`\\b(${URGENCY_WORDS.map((word) => word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\b`, "i")));
  score += Math.min(2, countMatches(sentence, NEGATIVE_EMOTION_RE));
  if (IMPERATIVE_START_RE.test(sentence)) {
    score += 2;
  }
  return Math.min(score, 10);
}

/** Soften every urgency signal inside a single sentence. */
export function removeUrgency(sentence: string): string {
  let softened = sentence;
  for (const [source, target] of Object.entries(ANXIETY_REPLACEMENTS)) {
    softened = replaceWord(softened, source, target);
  }
  for (const word of URGENCY_WORDS) {
    softened = replaceWord(softened, word, "important");
  }
  softened = softened.replace(/!+/g, ".");
  softened = softened.replace(CAPS_WORD_RE, (match) => match.charAt(0) + match.slice(1).toLowerCase());
  softened = softened.replace(/\s{2,}/g, " ").trim();
  if (softened && !".!?".includes(softened.slice(-1))) {
    softened += ".";
  }
  return softened;
}

/**
 * Reduce urgency signals for the anxiety profile while preserving
 * information.
 *
 * Port of the Python `UrgencyFilter`: each sentence is scored; strongly
 * urgent sentences (score >= 7) are softened in place, and moderately urgent
 * sentences (4-6) are softened and prefixed with a calm note so the reader
 * can see the temperature was deliberately lowered. Paragraph structure is
 * preserved throughout.
 */
export class UrgencyFilter implements TransformModule {
  public readonly name = "UrgencyFilter";

  public apply(text: string, _profile: ProfileConfig, profileId: Profile): string {
    if (!text.trim()) return "";
    if (profileId !== Profile.ANXIETY) {
      return text;
    }

    return mapUnprotectedRegions(text, (region) => {
      if (!region.trim()) {
        return region;
      }
      return region
        .split("\n\n")
        .map((paragraph) => {
          const sentences = splitSentences(paragraph);
          if (!sentences.length) return paragraph;
          return sentences.map((sentence) => this.rewriteSentence(sentence)).join(" ");
        })
        .join("\n\n");
    });
  }

  private rewriteSentence(sentence: string): string {
    const score = scoreSentenceUrgency(sentence);
    if (score >= 7) {
      return removeUrgency(sentence);
    }
    if (score >= 4) {
      return `A calm note: ${removeUrgency(sentence)}`;
    }
    return sentence;
  }
}
