export enum Profile {
  ADHD = "ADHD",
  AUTISM = "AUTISM",
  DYSLEXIA = "DYSLEXIA",
  ANXIETY = "ANXIETY",
  DYSCALCULIA = "DYSCALCULIA",
  CUSTOM = "CUSTOM"
}

export type ToneMode = "calm" | "neutral" | "clear" | "supportive" | "energetic";
export type AmbiguityResolution = "explicit" | "balanced" | "literal";
export type NumberFormat = "contextual" | "raw" | "visual";
export type LeadingStyle = "summary_first" | "stepwise" | "literal_first";

export interface ProfileConfig {
  chunkSize: number;
  tone: ToneMode;
  ambiguityResolution: AmbiguityResolution;
  numberFormat: NumberFormat;
  leadingStyle: LeadingStyle;
  readingLevel: number;
  maxSentenceWords: number;
}

export interface AdaptedResponse {
  adaptedText: string;
  originalText: string;
  profileUsed: Profile;
  transformsApplied: string[];
  processingTimeMs: number;
}

export type MemoryBackend = "none" | "localStorage" | "node";
export type OutputFormat = "plain" | "markdown" | "html" | "json";

export interface NeuroBridgeConfig {
  outputFormat?: OutputFormat;
  feedbackLearning?: boolean;
  debug?: boolean;
  memoryBackend?: MemoryBackend;
}

export interface TransformModule {
  readonly name: string;
  apply(text: string, profile: ProfileConfig, profileId: Profile): string;
}
