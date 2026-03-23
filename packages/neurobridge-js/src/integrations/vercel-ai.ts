import { NeuroBridge } from "../bridge";
import { Profile } from "../types";

export type StreamingTextResponse = {
  transformChunk: (text: string) => string;
};

export function neuroBridgeMiddleware(profile: Profile): StreamingTextResponse {
  const bridge = new NeuroBridge();
  bridge.setProfile(profile);

  return {
    transformChunk(text: string): string {
      return bridge.adaptSync(text).adaptedText;
    }
  };
}
