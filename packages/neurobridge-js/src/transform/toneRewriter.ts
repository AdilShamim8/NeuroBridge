import { Profile, ProfileConfig, TransformModule } from "../types";
import { ANXIETY_REPLACEMENTS, CATASTROPHIC_REPLACEMENTS, IDIOM_MAP } from "./urgency";

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
      Object.entries(CATASTROPHIC_REPLACEMENTS).forEach(([source, target]) => {
        output = replaceAllCaseInsensitive(output, source, target);
      });
      Object.entries(ANXIETY_REPLACEMENTS).forEach(([source, target]) => {
        output = replaceAllCaseInsensitive(output, source, target);
      });
    }

    return output;
  }
}
