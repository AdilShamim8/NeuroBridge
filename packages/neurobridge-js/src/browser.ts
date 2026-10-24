/**
 * Browser entry point.
 *
 * Excludes NodeFileMemory, which depends on the Node built-ins fs and path:
 * a browser bundle that statically imports them fails to load. Browser
 * consumers can use LocalStorageMemory instead.
 */
export { NeuroBridge } from "./bridge";
export { PROFILE_CONFIGS, resolveProfileConfig } from "./profiles";
export { wrapOpenAI } from "./integrations/openai";
export { wrapAnthropic } from "./integrations/anthropic";
export { neuroBridgeMiddleware } from "./integrations/vercel-ai";
export { LocalStorageMemory } from "./memory/localStorage";
export { Profile } from "./types";
export type {
  AdaptedResponse,
  NeuroBridgeConfig,
  ProfileConfig,
  TransformModule
} from "./types";
