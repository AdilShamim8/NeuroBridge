import { split } from "sentence-splitter";

import { Profile, ProfileConfig, TransformModule } from "../types";

function sentenceText(input: string): string[] {
  const nodes = split(input);
  return nodes
    .filter((node: unknown) => (node as { type?: string }).type === "Sentence")
    .map((node: unknown) => String((node as { raw: string }).raw).trim())
    .filter(Boolean);
}

/** Bold the first 4-6 words of a chunk to create an attention anchor. */
function boldAnchorWords(chunk: string): string {
  const words = chunk.split(/\s+/).filter(Boolean);
  if (!words.length) return chunk;
  const anchorCount = Math.min(Math.max(4, 5), 6, words.length);
  const anchored = words.slice(0, anchorCount).join(" ");
  const remainder = words.slice(anchorCount).join(" ");
  return remainder ? `**${anchored}** ${remainder}` : `**${anchored}**`;
}

/**
 * Split text into readable sentence chunks.
 *
 * Mirrors the Python pipeline's Chunker: chunking happens within each
 * paragraph so paragraph boundaries survive as chunk boundaries, dyslexia
 * output uses a wider separator, and ADHD output bolds an attention anchor at
 * the start of each chunk.
 */
export class Chunker implements TransformModule {
  public readonly name = "Chunker";

  public apply(text: string, profile: ProfileConfig, profileId: Profile): string {
    if (!text.trim()) return "";

    let chunkSize = Math.max(1, profile.chunkSize);
    let separator = "\n\n";
    if (profileId === Profile.DYSLEXIA) {
      chunkSize = Math.min(chunkSize, 3);
      separator = "\n\n\n";
    }

    return text
      .split(/\n\n+/)
      .map((paragraph) => {
        const sentences = sentenceText(paragraph);
        if (!sentences.length) return paragraph;

        const chunks: string[] = [];
        for (let i = 0; i < sentences.length; i += chunkSize) {
          chunks.push(sentences.slice(i, i + chunkSize).join(" "));
        }
        const joined = chunks.join(separator);
        return profileId === Profile.ADHD
          ? chunks.map(boldAnchorWords).join(separator)
          : joined;
      })
      .join(separator);
  }
}
