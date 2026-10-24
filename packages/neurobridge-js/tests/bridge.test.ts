import { describe, expect, it } from "vitest";

import { NeuroBridge } from "../src/bridge";
import { PROFILE_CONFIGS, resolveProfileConfig } from "../src/profiles";
import { Profile } from "../src/types";

describe("PROFILE_CONFIGS parity with the Python package", () => {
  // These values mirror neurobridge/core/profile.py DEFAULT_PROFILE_CONFIGS.
  const expected: Record<string, [number, string, string, string, string, number, number]> = {
    ADHD: [3, "clear", "balanced", "contextual", "summary_first", 7, 16],
    AUTISM: [2, "neutral", "explicit", "raw", "detail_first", 8, 18],
    DYSLEXIA: [2, "calm", "explicit", "contextual", "summary_first", 5, 12],
    ANXIETY: [3, "calm", "explicit", "contextual", "reassure_first", 6, 14],
    DYSCALCULIA: [3, "clear", "balanced", "contextual", "stepwise", 6, 15],
    CUSTOM: [3, "neutral", "balanced", "raw", "detail_first", 8, 18]
  };

  for (const [name, values] of Object.entries(expected)) {
    it(`${name} matches the Python defaults`, () => {
      const config = PROFILE_CONFIGS[Profile[name as keyof typeof Profile]];
      expect([
        config.chunkSize,
        config.tone,
        config.ambiguityResolution,
        config.numberFormat,
        config.leadingStyle,
        config.readingLevel,
        config.maxSentenceWords
      ]).toEqual(values);
    });
  }
});

describe("resolveProfileConfig", () => {
  it("returns the enum config for enum input", () => {
    const resolved = resolveProfileConfig(Profile.DYSLEXIA);
    expect(resolved.profileId).toBe(Profile.DYSLEXIA);
    expect(resolved.config).toEqual(PROFILE_CONFIGS[Profile.DYSLEXIA]);
  });

  it("detects a hand-written config that equals a built-in profile", () => {
    // Regression: identical-to-built-in configs got CUSTOM and lost their
    // profile-specific transforms. The Python pipeline matches by value.
    const resolved = resolveProfileConfig({ ...PROFILE_CONFIGS[Profile.ANXIETY] });
    expect(resolved.profileId).toBe(Profile.ANXIETY);
  });

  it("keeps CUSTOM for genuinely custom configs", () => {
    const resolved = resolveProfileConfig({
      ...PROFILE_CONFIGS[Profile.ADHD],
      chunkSize: 5
    });
    expect(resolved.profileId).toBe(Profile.CUSTOM);
  });
});

describe("NeuroBridge.adaptSync", () => {
  it("returns an AdaptedResponse with the original text preserved", () => {
    const bridge = new NeuroBridge();
    bridge.setProfile(Profile.ADHD);
    const result = bridge.adaptSync("First sentence here. Second sentence follows.");
    expect(result.originalText).toBe("First sentence here. Second sentence follows.");
    expect(result.profileUsed).toBe(Profile.ADHD);
    expect(typeof result.processingTimeMs).toBe("number");
  });

  it("anxiety softening keeps sentences grammatical", () => {
    // Regression: every urgency word used to become "important", producing
    // "You important complete this" style output.
    const bridge = new NeuroBridge();
    bridge.setProfile(Profile.ANXIETY);
    const result = bridge.adaptSync("You must complete this urgent task before the deadline.");
    const lowered = result.adaptedText.toLowerCase();
    expect(lowered).toContain("consider");
    expect(lowered).toContain("worth noting");
    expect(lowered).toContain("target date");
    expect(lowered).not.toContain(" must ");
    expect(lowered).not.toContain("urgent");
    expect(lowered).not.toContain("deadline");
    // No blanket-replacement artifacts.
    expect(lowered).not.toContain("important complete");
  });

  it("autism rewrites idioms to plain language", () => {
    const bridge = new NeuroBridge();
    bridge.setProfile(Profile.AUTISM);
    const result = bridge.adaptSync("Let's touch base tomorrow about the launch.");
    expect(result.adaptedText.toLowerCase()).toContain("make contact");
  });

  it("custom config identical to a built-in still gets profile transforms", () => {
    const bridge = new NeuroBridge();
    bridge.setProfile({ ...PROFILE_CONFIGS[Profile.DYSCALCULIA] });
    const result = bridge.adaptSync("About 19% of users prefer this layout.");
    // Dyscalculia number context must fire, proving profile detection.
    // "3 in every 16" is exactly what the Python pipeline emits for 19%.
    expect(result.adaptedText).toContain("3 in every 16");
  });

  it("empty and whitespace input pass through untouched", () => {
    const bridge = new NeuroBridge();
    expect(bridge.adaptSync("   ")).toMatchObject({ adaptedText: "   " });
  });
});
