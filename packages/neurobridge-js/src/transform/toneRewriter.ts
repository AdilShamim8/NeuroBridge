import { Profile, ProfileConfig, TransformModule } from "../types";
import { IDIOM_MAP, URGENCY_WORDS } from "./urgency";

function replaceAllCaseInsensitive(text: string, source: string, target: string): string {
  const escaped = source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`\\b${escaped}\\b`, "gi");
  return text.replace(pattern, target);
}

export class ToneRewriter implements TransformModule {
  public readonly name = "ToneRewriter";

  public apply(text: string, _profile: ProfileConfig, profileId: Profile): string {
    let output = text;

    if (profileId === Profile.AUTISM) {
      Object.entries(IDIOM_MAP).forEach(([idiom, replacement]) => {
        output = replaceAllCaseInsensitive(output, idiom, replacement);
      });
    }

    if (profileId === Profile.ANXIETY) {
      URGENCY_WORDS.forEach((word) => {
        output = replaceAllCaseInsensitive(output, word, "important");
      });
    }

    return output;
  }
}
