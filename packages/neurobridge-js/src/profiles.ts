import { Profile, ProfileConfig } from "./types";

/**
 * Authoritative profile defaults, kept in lockstep with the Python package's
 * neurobridge.core.profile.DEFAULT_PROFILE_CONFIGS. Change both together.
 */
export const PROFILE_CONFIGS: Record<Profile, ProfileConfig> = {
  [Profile.ADHD]: {
    chunkSize: 3,
    tone: "clear",
    ambiguityResolution: "balanced",
    numberFormat: "contextual",
    leadingStyle: "summary_first",
    readingLevel: 7,
    maxSentenceWords: 16
  },
  [Profile.AUTISM]: {
    chunkSize: 2,
    tone: "neutral",
    ambiguityResolution: "explicit",
    numberFormat: "raw",
    leadingStyle: "detail_first",
    readingLevel: 8,
    maxSentenceWords: 18
  },
  [Profile.DYSLEXIA]: {
    chunkSize: 2,
    tone: "calm",
    ambiguityResolution: "explicit",
    numberFormat: "contextual",
    leadingStyle: "summary_first",
    readingLevel: 5,
    maxSentenceWords: 12
  },
  [Profile.ANXIETY]: {
    chunkSize: 3,
    tone: "calm",
    ambiguityResolution: "explicit",
    numberFormat: "contextual",
    leadingStyle: "reassure_first",
    readingLevel: 6,
    maxSentenceWords: 14
  },
  [Profile.DYSCALCULIA]: {
    chunkSize: 3,
    tone: "clear",
    ambiguityResolution: "balanced",
    numberFormat: "contextual",
    leadingStyle: "stepwise",
    readingLevel: 6,
    maxSentenceWords: 15
  },
  [Profile.CUSTOM]: {
    chunkSize: 3,
    tone: "neutral",
    ambiguityResolution: "balanced",
    numberFormat: "raw",
    leadingStyle: "detail_first",
    readingLevel: 8,
    maxSentenceWords: 18
  }
};

function configsEqual(a: ProfileConfig, b: ProfileConfig): boolean {
  return (
    a.chunkSize === b.chunkSize &&
    a.tone === b.tone &&
    a.ambiguityResolution === b.ambiguityResolution &&
    a.numberFormat === b.numberFormat &&
    a.leadingStyle === b.leadingStyle &&
    a.readingLevel === b.readingLevel &&
    a.maxSentenceWords === b.maxSentenceWords
  );
}

/**
 * Resolve a profile enum or a raw config object.
 *
 * A config that exactly matches a built-in profile resolves to that profile's
 * id, mirroring the Python pipeline's value-based profile detection: profile-
 * specific transforms (dyscalculia number context, ADHD reordering, anxiety
 * softening, autism idiom handling) then apply to hand-written configs that
 * simply copied a built-in.
 */
export function resolveProfileConfig(
  profile: Profile | ProfileConfig
): { profileId: Profile; config: ProfileConfig } {
  if (typeof profile === "object") {
    const config = { ...profile };
    for (const candidate of [
      Profile.ADHD,
      Profile.AUTISM,
      Profile.DYSLEXIA,
      Profile.ANXIETY,
      Profile.DYSCALCULIA
    ]) {
      if (configsEqual(config, PROFILE_CONFIGS[candidate])) {
        return { profileId: candidate, config };
      }
    }
    return { profileId: Profile.CUSTOM, config };
  }
  return { profileId: profile, config: { ...PROFILE_CONFIGS[profile] } };
}
