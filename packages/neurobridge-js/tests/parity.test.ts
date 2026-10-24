/**
 * Cross-SDK parity: the JavaScript pipeline must produce byte-identical
 * adapted text to the Python pipeline for the same profile and input.
 *
 * The fixtures in tests/fixtures/parity.json are generated from the Python
 * implementation by:
 *
 *   python packages/neurobridge-js/scripts/generate-parity-fixtures.py
 *
 * If this test fails after a deliberate Python change, regenerate the
 * fixtures and keep both implementations in sync. A failure without a
 * Python change means the JS port drifted and must be fixed, not the
 * fixtures.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { NeuroBridge } from "../src/bridge";
import { Profile } from "../src/types";

interface ParityFixture {
  profile: "adhd" | "autism" | "dyslexia" | "anxiety" | "dyscalculia";
  input: string;
  expected: string;
}

const fixturesPath = join(
  dirname(fileURLToPath(import.meta.url)),
  "fixtures",
  "parity.json"
);
const fixtures: ParityFixture[] = JSON.parse(readFileSync(fixturesPath, "utf-8"));

describe("python parity", () => {
  it("loads a non-empty fixture set", () => {
    expect(fixtures.length).toBeGreaterThan(0);
    expect(fixtures.some((f) => f.profile === "anxiety")).toBe(true);
  });

  for (const fixture of fixtures) {
    it(`${fixture.profile}: ${fixture.input.slice(0, 48)}...`, () => {
      const bridge = new NeuroBridge();
      const profileId = Profile[
        fixture.profile.toUpperCase() as keyof typeof Profile
      ] as Profile;
      bridge.setProfile(profileId);
      const response = bridge.adaptSync(fixture.input);
      expect(response.adaptedText).toBe(fixture.expected);
    });
  }
});
