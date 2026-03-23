import { NeuroBridge } from "../bridge";
import { Profile } from "../types";

type ChatCompletionCreate = (...args: any[]) => Promise<any>;

function adaptStringContent(content: unknown, bridge: NeuroBridge): unknown {
  if (typeof content !== "string" || !content.trim()) {
    return content;
  }
  return bridge.adaptSync(content).adaptedText;
}

export function wrapOpenAI<TClient extends { chat: { completions: { create: ChatCompletionCreate } } }>(
  client: TClient,
  profile: Profile
): TClient {
  const bridge = new NeuroBridge();
  bridge.setProfile(profile);

  const originalCreate = client.chat.completions.create.bind(client.chat.completions);

  client.chat.completions.create = (async (...args: any[]) => {
    const response = await originalCreate(...args);

    if (args[0]?.stream === true && response?.[Symbol.asyncIterator]) {
      const source = response;
      const wrapped = {
        async *[Symbol.asyncIterator]() {
          for await (const chunk of source) {
            const content = chunk?.choices?.[0]?.delta?.content;
            if (typeof content === "string" && content.trim()) {
              chunk.choices[0].delta.content = bridge.adaptSync(content).adaptedText;
            }
            yield chunk;
          }
        }
      };
      return wrapped as typeof response;
    }

    const message = response?.choices?.[0]?.message;
    if (message) {
      message.content = adaptStringContent(message.content, bridge);
    }

    return response;
  }) as ChatCompletionCreate;

  return client;
}
