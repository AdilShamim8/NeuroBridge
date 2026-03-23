import { Profile, ProfileConfig, TransformModule } from "../types";
import { reorderByPriority } from "./structure";

export class PriorityReorderer implements TransformModule {
  public readonly name = "PriorityReorderer";

  public apply(text: string, _profile: ProfileConfig, profileId: Profile): string {
    if (profileId !== Profile.ADHD) {
      return text;
    }
    return reorderByPriority(text);
  }
}
