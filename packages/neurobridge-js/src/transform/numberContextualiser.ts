import { Profile, ProfileConfig, TransformModule } from "../types";
import { contextualizeNumbers } from "./numbers";

export class NumberContextualiser implements TransformModule {
  public readonly name = "NumberContextualiser";

  public apply(text: string, _profile: ProfileConfig, profileId: Profile): string {
    if (profileId !== Profile.DYSCALCULIA) {
      return text;
    }
    return contextualizeNumbers(text);
  }
}
