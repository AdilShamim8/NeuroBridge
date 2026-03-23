# neurobridge (JavaScript/TypeScript SDK)

[![npm version](https://img.shields.io/npm/v/neurobridge.svg)](https://www.npmjs.com/package/neurobridge)
[![bundle size](https://img.shields.io/bundlephobia/minzip/neurobridge)](https://bundlephobia.com/package/neurobridge)

Cognitive accessibility middleware for AI output in the JavaScript ecosystem.

## Quick Start (Node.js)

```ts
import { NeuroBridge, Profile } from "neurobridge";

const nb = new NeuroBridge();
nb.setProfile(Profile.ADHD);
const result = nb.adaptSync("Explain this migration plan in detail.");
console.log(result.adaptedText);
```

## Browser Example

```html
<script src="https://unpkg.com/neurobridge/dist/browser/neurobridge.global.js"></script>
<script>
  const nb = new window.NeuroBridge();
  nb.setProfile("ADHD");
  const result = nb.adaptSync("This is critical and must be done ASAP.");
  console.log(result.adaptedText);
</script>
```

## Integrations

- `wrapOpenAI(client, profile)` for OpenAI SDK
- `wrapAnthropic(client, profile)` for Anthropic SDK
- `neuroBridgeMiddleware(profile)` for Vercel AI SDK style middleware

## Build Targets

- ESM: `dist/esm/index.js`
- CJS: `dist/cjs/index.cjs`
- Browser IIFE: `dist/browser/neurobridge.global.js`

## Related

- Python package: https://pypi.org/project/neurobridge/
- Repository: https://github.com/yourusername/neurobridge
