import { resolveProfileConfig } from "./profiles";
import {
  Chunker,
  NumberContextualiser,
  PriorityReorderer,
  ToneRewriter
} from "./transform";
import { AdaptedResponse, NeuroBridgeConfig, Profile, ProfileConfig, TransformModule } from "./types";

export class NeuroBridge {
  private profileId: Profile = Profile.ADHD;
  private profile: ProfileConfig = resolveProfileConfig(Profile.ADHD).config;
  private readonly config: Required<NeuroBridgeConfig>;
  private readonly modules: TransformModule[];

  public constructor(config: NeuroBridgeConfig = {}) {
    this.config = {
      outputFormat: config.outputFormat ?? "plain",
      feedbackLearning: config.feedbackLearning ?? true,
      debug: config.debug ?? false,
      memoryBackend: config.memoryBackend ?? "none"
    };

    this.modules = [
      new Chunker(),
      new ToneRewriter(),
      new NumberContextualiser(),
      new PriorityReorderer()
    ];
  }

  public setProfile(profile: Profile | ProfileConfig): void {
    const resolved = resolveProfileConfig(profile);
    this.profileId = resolved.profileId;
    this.profile = resolved.config;
  }

  public async adapt(text: string): Promise<AdaptedResponse> {
    return Promise.resolve(this.adaptSync(text));
  }

  public adaptSync(text: string): AdaptedResponse {
    const start = Date.now();
    let output = text;
    const transformsApplied: string[] = [];

    this.modules.forEach((module) => {
      const next = module.apply(output, this.profile, this.profileId);
      if (next !== output) {
        transformsApplied.push(module.name);
      }
      output = next;
    });

    return {
      adaptedText: output,
      originalText: text,
      profileUsed: this.profileId,
      transformsApplied,
      processingTimeMs: Date.now() - start
    };
  }

  public getConfig(): Required<NeuroBridgeConfig> {
    return { ...this.config };
  }
}
