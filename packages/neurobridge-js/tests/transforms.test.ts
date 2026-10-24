import { describe, expect, it } from "vitest";

import { PROFILE_CONFIGS } from "../src/profiles";
import { Profile } from "../src/types";
import { Chunker } from "../src/transform/chunker";
import { NumberContextualiser } from "../src/transform/numberContextualiser";
import { PriorityReorderer } from "../src/transform/priorityReorderer";
import { SentenceSimplifier, splitSentences } from "../src/transform/sentenceSimplifier";
import { ToneRewriter } from "../src/transform/toneRewriter";

describe("SentenceSimplifier", () => {
  const simplifier = new SentenceSimplifier();
  const anxiety = PROFILE_CONFIGS[Profile.ANXIETY]; // maxSentenceWords: 14

  it("splits sentences that exceed the word budget at conjunctions", () => {
    const longSentence =
      "The deployment pipeline runs the tests, and then it builds the container image, and finally it publishes the package to the registry for everyone.";
    const out = simplifier.apply(longSentence, anxiety, Profile.ANXIETY);
    // Long clauses become separate sentences.
    expect(out.split(". ").length).toBeGreaterThanOrEqual(3);
    // No content lost: every original word still appears.
    for (const word of ["deployment", "container", "publishes"]) {
      expect(out.toLowerCase()).toContain(word);
    }
  });

  it("leaves short sentences alone", () => {
    const text = "Short sentence. Another one.";
    expect(simplifier.apply(text, anxiety, Profile.ANXIETY)).toBe(text);
  });

  it("preserves paragraph breaks", () => {
    const out = simplifier.apply("First paragraph.\n\nSecond paragraph.", anxiety, Profile.ANXIETY);
    expect(out).toContain("\n\n");
  });
});

describe("splitSentences", () => {
  it("keeps bold markers attached to their sentence", () => {
    const sentences = splitSentences("**Bold intro.** Plain second sentence.");
    expect(sentences[0]).toBe("**Bold intro.**");
    expect(sentences[1]).toBe("Plain second sentence.");
  });
});

describe("Chunker", () => {
  const chunker = new Chunker();

  it("never merges sentences across paragraph boundaries", () => {
    const out = chunker.apply(
      "Para one sentence.\n\nPara two sentence.\n\nPara three sentence.",
      PROFILE_CONFIGS[Profile.ADHD],
      Profile.ADHD
    );
    expect(out.split("\n\n").length).toBeGreaterThanOrEqual(3);
  });

  it("uses the wider dyslexia separator", () => {
    const out = chunker.apply(
      "One sentence here. Another one follows. A third one too.",
      PROFILE_CONFIGS[Profile.DYSLEXIA],
      Profile.DYSLEXIA
    );
    expect(out).toContain("\n\n\n");
  });

  it("bolds an attention anchor for ADHD chunks", () => {
    const out = chunker.apply(
      "One sentence here. Another one follows.",
      PROFILE_CONFIGS[Profile.ADHD],
      Profile.ADHD
    );
    expect(out).toMatch(/\*\*One sentence here\./);
  });

  it("passes blank text through", () => {
    expect(chunker.apply("   ", PROFILE_CONFIGS[Profile.ADHD], Profile.ADHD)).toBe("");
  });
});

describe("NumberContextualiser", () => {
  const contextualiser = new NumberContextualiser();
  const dyscalculia = PROFILE_CONFIGS[Profile.DYSCALCULIA];

  it("annotates percentages with the exact fraction the Python pipeline emits", () => {
    const out = contextualiser.apply("About 19% of users.", dyscalculia, Profile.DYSCALCULIA);
    expect(out).toContain("19% (3 in every 16)");
  });

  it("uses real magnitude comparisons for currency, not placeholders", () => {
    // Regression: currency amounts were annotated '(contextualized amount)'.
    const out = contextualiser.apply(
      "The server costs $45,000 per year.",
      dyscalculia,
      Profile.DYSCALCULIA
    );
    expect(out).not.toContain("contextualized amount");
    expect(out).toMatch(/\$45,000 \((.+)\)/);
  });

  it("handles scaled currency suffixes", () => {
    const out = contextualiser.apply("Budget is $3.2m total.", dyscalculia, Profile.DYSCALCULIA);
    expect(out).toContain("$3.2m (");
    expect(out).not.toContain("contextualized amount");
  });

  it("states an honest bound for tiny percentages", () => {
    const out = contextualiser.apply("Only 2% failed.", dyscalculia, Profile.DYSCALCULIA);
    expect(out).toContain("less than 1 in every 20");
  });

  it("does nothing for non-dyscalculia profiles", () => {
    const text = "About 19% of users.";
    expect(
      contextualiser.apply(text, PROFILE_CONFIGS[Profile.ADHD], Profile.ADHD)
    ).toBe(text);
  });
});

describe("ToneRewriter anxiety softening", () => {
  const rewriter = new ToneRewriter();
  const anxiety = PROFILE_CONFIGS[Profile.ANXIETY];

  it("softens catastrophic phrasing", () => {
    const out = rewriter.apply("This will break production.", anxiety, Profile.ANXIETY);
    expect(out).toContain("might need attention");
    expect(out.toLowerCase()).not.toContain("will break");
  });

  it("does not rewrite for non-anxiety profiles", () => {
    const text = "You must fix this critical error immediately.";
    expect(rewriter.apply(text, PROFILE_CONFIGS[Profile.ADHD], Profile.ADHD)).toBe(text);
  });
});

describe("PriorityReorderer", () => {
  const reorderer = new PriorityReorderer();

  it("prefixes a bottom line for ADHD", () => {
    const out = reorderer.apply(
      "Background details here.\n\nClosing thought goes last.",
      PROFILE_CONFIGS[Profile.ADHD],
      Profile.ADHD
    );
    expect(out.toLowerCase()).toContain("bottom line");
  });

  it("leaves other profiles untouched", () => {
    const text = "Background details here.\n\nClosing thought goes last.";
    expect(reorderer.apply(text, PROFILE_CONFIGS[Profile.AUTISM], Profile.AUTISM)).toBe(text);
  });
});
