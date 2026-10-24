import { Profile, ProfileConfig, TransformModule } from "../types";
import {
  ANXIETY_REPLACEMENTS,
  CATASTROPHIC_REPLACEMENTS,
  IDIOM_MAP,
} from "./urgency";
import { mapUnprotectedRegions } from "./protect";

const FILLER_REPLACEMENTS: Record<string, string> = {
  "It is worth noting that": "",
  "As you may know": "",
  "It goes without saying": "",
  "Needless to say": "",
  "To be honest": "",
  "At the end of the day": "",
};

const VAGUE_QUALIFIER_REPLACEMENTS: Record<string, string> = {
  some: "a few",
  many: "several",
  soon: "within a clear timeframe",
  later: "at a later time",
  "a lot": "many",
};

const SARCASM_REPLACEMENTS: Record<string, string> = {
  "Oh great": "This is difficult",
  "Just what I needed": "This is not ideal",
  Wonderful: "Not ideal",
};

const NEGATIVE_WORDS_RE =
  /\b(concern|risk|issue|problem|setback|error|fail|failure|difficult|hard|complicated)\b/i;

function replaceAllCaseInsensitive(text: string, source: string, target: string): string {
  const escaped = source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`\\b${escaped}\\b`, "gi");
  return text.replace(pattern, target);
}

function applyReplacements(text: string, replacements: Record<string, string>): string {
  let output = text;
  for (const [source, target] of Object.entries(replacements)) {
    output = replaceAllCaseInsensitive(output, source, target);
  }
  return output;
}

/**
 * Rewrite tone for anxiety/autism needs and remove filler phrases globally.
 *
 * Port of the Python `ToneRewriter`: filler phrases are stripped for every
 * profile, the anxiety path softens vocabulary and prefixes paragraphs that
 * still contain negative words with grounding context, and the autism path
 * replaces idioms, vague qualifiers, and sarcasm with literal phrasing.
 * Protected regions (code fences, numbered lists) pass through untouched.
 */
export class ToneRewriter implements TransformModule {
  public readonly name = "ToneRewriter";

  public apply(text: string, _profile: ProfileConfig, profileId: Profile): string {
    if (!text.trim()) return "";

    return mapUnprotectedRegions(text, (region) => {
      let updated = this.stripFillers(region);
      if (profileId === Profile.ANXIETY) {
        updated = this.rewriteAnxiety(updated);
      } else if (profileId === Profile.AUTISM) {
        updated = this.rewriteAutism(updated);
      }
      return updated;
    });
  }

  /** Remove filler phrases; collapse horizontal whitespace only. */
  private stripFillers(text: string): string {
    let updated = text;
    for (const [source, target] of Object.entries(FILLER_REPLACEMENTS)) {
      const escaped = source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      updated = updated.replace(new RegExp(`\\b${escaped}\\b`, "g"), target);
    }
    return updated.replace(/[^\S\n]+/g, " ");
  }

  /**
   * Soften anxious vocabulary, then ground paragraphs that still name
   * negative outcomes: even-indexed paragraphs get neutral context, odd
   * ones lead with the good news, mirroring the Python implementation.
   */
  private rewriteAnxiety(text: string): string {
    let updated = applyReplacements(text, ANXIETY_REPLACEMENTS);
    updated = applyReplacements(updated, CATASTROPHIC_REPLACEMENTS);

    return updated
      .split("\n\n")
      .map((paragraph, index) => {
        const clean = paragraph.trim();
        if (!clean) return paragraph;
        if (NEGATIVE_WORDS_RE.test(clean)) {
          const prefix = index % 2 === 0 ? "Here is some context: " : "Good news first - ";
          return prefix + clean;
        }
        return paragraph;
      })
      .join("\n\n");
  }

  /** Replace idioms, vague qualifiers, and sarcasm with literal wording. */
  private rewriteAutism(text: string): string {
    let updated = text;
    for (const [idiom, replacement] of Object.entries(IDIOM_MAP)) {
      updated = replaceAllCaseInsensitive(updated, idiom, replacement);
    }
    updated = applyReplacements(updated, VAGUE_QUALIFIER_REPLACEMENTS);
    updated = applyReplacements(updated, SARCASM_REPLACEMENTS);
    return updated;
  }
}
