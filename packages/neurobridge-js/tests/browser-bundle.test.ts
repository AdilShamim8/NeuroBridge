/**
 * Browser bundle smoke test.
 *
 * The dist/browser/neurobridge.global.js artifact is what script-tag users
 * load; a broken build config (wrong format, missing exports, accidental
 * Node-only imports) would only surface at runtime in the browser. Build
 * the bundle, evaluate it the way a browser would (as a global IIFE), and
 * verify the public API adapts text end to end.
 *
 * Run with: npm run test:browser (requires the bundle to be built first).
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const bundlePath = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "dist",
  "browser",
  "neurobridge.global.js"
);

interface BrowserGlobal {
  NeuroBridge: new () => {
    setProfile(profile: unknown): void;
    adapt(text: string): Promise<{ adaptedText: string }>;
  };
  Profile: Record<string, string>;
}

function loadBrowserGlobal(): BrowserGlobal {
  const source = readFileSync(bundlePath, "utf8");
  // Deliberately NOT strict: in a browser the IIFE's top-level var becomes
  // window.NeuroBridge; a sloppy direct eval models that binding.
  const loader = new Function("source", "eval(source); return NeuroBridge;");
  return loader(source) as BrowserGlobal;
}

describe("browser bundle", () => {
  it("exposes the public API on the global", () => {
    const global = loadBrowserGlobal();
    expect(typeof global.NeuroBridge).toBe("function");
    expect(global.Profile.ANXIETY).toBe("ANXIETY");
  });

  it("adapts text end to end from the bundle", async () => {
    const global = loadBrowserGlobal();
    const bridge = new global.NeuroBridge();
    bridge.setProfile(global.Profile.ANXIETY);
    const response = await bridge.adapt(
      "You must immediately fix the critical bug. Revenue was 22% lower."
    );
    expect(response.adaptedText).toContain("A calm note:");
    expect(response.adaptedText).toContain("when ready");
  });

  it("keeps dyscalculia number context in the bundle", async () => {
    const global = loadBrowserGlobal();
    const bridge = new global.NeuroBridge();
    bridge.setProfile(global.Profile.DYSCALCULIA);
    const response = await bridge.adapt("Revenue was 22% lower.");
    expect(response.adaptedText).toBe("Revenue was 22% (2 in every 9) lower.");
  });
});
