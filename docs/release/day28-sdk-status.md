# Day 28 - JavaScript/TypeScript SDK Status

Date: 2026-03-23

## Implemented

- Full SDK scaffold at `packages/neurobridge-js/`.
- Core types and profile configs.
- `NeuroBridge` class with `setProfile`, `adapt`, and `adaptSync`.
- Transform modules (chunker, tone rewriter, number contextualiser, priority reorderer).
- Integrations for OpenAI, Anthropic, and Vercel-style middleware.
- Browser/global support via `window.NeuroBridge` assignment.
- Browser and Node memory adapters.
- Rollup build config for ESM/CJS/browser outputs.
- SDK README and examples.

## Publish Checklist

- `package.json` prepared with:
  - name: `neurobridge`
  - version: `0.2.0-beta.1`
  - CJS/ESM exports
  - Type declarations path
  - optional peer deps (`openai`, `@anthropic-ai/sdk`)

## Environment Constraints

Could not run build/publish commands because `npm` is not installed in this execution environment.

Blocked commands:

- `npm --prefix packages/neurobridge-js run build`
- `npm --prefix packages/neurobridge-js publish --access public`

## Next Steps on a Node-enabled machine

1. Install Node.js + npm.
2. Run:
   - `npm --prefix packages/neurobridge-js install`
   - `npm --prefix packages/neurobridge-js run build`
   - `npm --prefix packages/neurobridge-js publish --access public`
3. Validate bundle size target and browser example output.
