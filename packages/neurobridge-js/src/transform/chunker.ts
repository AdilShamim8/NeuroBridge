import { Profile, ProfileConfig, TransformModule } from "../types";
import { protectRegions } from "./protect";
import { splitSentences } from "./sentenceSimplifier";

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

    return protectRegions(text)
      .map((region) => {
        if (region.protected) {
          return region.text;
        }
        if (!region.text.trim()) {
          return region.text;
        }
        return this.chunkRegion(region.text, chunkSize, separator, profileId);
      })
      .join("")
      .trim();
  }

  private chunkRegion(
    text: string,
    chunkSize: number,
    separator: string,
    profileId: Profile
  ): string {
    return text
      .split("\n\n")
      .map((paragraph) => {
        const sentences = splitSentences(paragraph);
        if (!sentences.length) return paragraph;

        const chunks: string[] = [];
        for (let i = 0; i < sentences.length; i += chunkSize) {
          chunks.push(sentences.slice(i, i + chunkSize).join(" "));
        }
        if (profileId === Profile.ADHD) {
          return chunks.map(boldAnchorWords).join(separator);
        }
        return chunks.join(separator);
      })
      .join(separator);
  }
}
