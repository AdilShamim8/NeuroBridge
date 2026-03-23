import { NeuroBridge } from "./bridge";

export { NeuroBridge } from "./bridge";
export { PROFILE_CONFIGS, resolveProfileConfig } from "./profiles";
export { wrapOpenAI } from "./integrations/openai";
export { wrapAnthropic } from "./integrations/anthropic";
export { neuroBridgeMiddleware } from "./integrations/vercel-ai";
export { LocalStorageMemory } from "./memory/localStorage";
export { NodeFileMemory } from "./memory/node";
export { Profile } from "./types";
export type {
  AdaptedResponse,
  NeuroBridgeConfig,
  ProfileConfig,
  TransformModule
} from "./types";

const globalTarget = globalThis as Record<string, unknown>;
if (!globalTarget.NeuroBridge) {
  globalTarget.NeuroBridge = NeuroBridge;
}
