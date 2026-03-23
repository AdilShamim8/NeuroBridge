import { NeuroBridge } from "../bridge";
import { Profile } from "../types";

type AnthropicCreate = (...args: any[]) => Promise<any>;

export function wrapAnthropic<TClient extends { messages: { create: AnthropicCreate } }>(
  client: TClient,
  profile: Profile
): TClient {
  const bridge = new NeuroBridge();
  bridge.setProfile(profile);

  const originalCreate = client.messages.create.bind(client.messages);
  client.messages.create = (async (...args: any[]) => {
    const response = await originalCreate(...args);

    const first = response?.content?.[0];
    if (first && typeof first.text === "string" && first.text.trim()) {
      first.text = bridge.adaptSync(first.text).adaptedText;
    }

    return response;
  }) as AnthropicCreate;

  return client;
}
