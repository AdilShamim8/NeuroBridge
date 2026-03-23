import { split } from "sentence-splitter";

import { Profile, ProfileConfig, TransformModule } from "../types";

function sentenceText(input: string): string[] {
  const nodes = split(input);
  return nodes
    .filter((node: unknown) => (node as { type?: string }).type === "Sentence")
    .map((node: unknown) => String((node as { raw: string }).raw).trim())
    .filter(Boolean);
}

export class Chunker implements TransformModule {
  public readonly name = "Chunker";

  public apply(text: string, profile: ProfileConfig, profileId: Profile): string {
    const sentences = sentenceText(text);
    if (!sentences.length) {
      return text;
    }

    let chunkSize = Math.max(1, profile.chunkSize);
    if (profileId === Profile.ADHD) {
      chunkSize = Math.min(chunkSize, 3);
    }

    const chunks: string[] = [];
    for (let i = 0; i < sentences.length; i += chunkSize) {
      chunks.push(sentences.slice(i, i + chunkSize).join(" "));
    }

    return chunks.join("\n\n");
  }
}
