import { Profile, ProfileConfig } from "./types";

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
    ambiguityResolution: "literal",
    numberFormat: "raw",
    leadingStyle: "literal_first",
    readingLevel: 8,
    maxSentenceWords: 18
  },
  [Profile.DYSLEXIA]: {
    chunkSize: 2,
    tone: "clear",
    ambiguityResolution: "explicit",
    numberFormat: "contextual",
    leadingStyle: "stepwise",
    readingLevel: 6,
    maxSentenceWords: 14
  },
  [Profile.ANXIETY]: {
    chunkSize: 3,
    tone: "calm",
    ambiguityResolution: "balanced",
    numberFormat: "contextual",
    leadingStyle: "summary_first",
    readingLevel: 7,
    maxSentenceWords: 15
  },
  [Profile.DYSCALCULIA]: {
    chunkSize: 3,
    tone: "supportive",
    ambiguityResolution: "explicit",
    numberFormat: "contextual",
    leadingStyle: "summary_first",
    readingLevel: 7,
    maxSentenceWords: 16
  },
  [Profile.CUSTOM]: {
    chunkSize: 3,
    tone: "neutral",
    ambiguityResolution: "balanced",
    numberFormat: "contextual",
    leadingStyle: "summary_first",
    readingLevel: 7,
    maxSentenceWords: 16
  }
};

export function resolveProfileConfig(profile: Profile | ProfileConfig): { profileId: Profile; config: ProfileConfig } {
  if (typeof profile === "object") {
    return { profileId: Profile.CUSTOM, config: { ...profile } };
  }
  return { profileId: profile, config: { ...PROFILE_CONFIGS[profile] } };
}
