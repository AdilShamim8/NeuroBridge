/**
 * axe-core accessibility audit for the built website.
 *
 * Usage:
 *   npm run a11y            # audit an already-running server (A11Y_BASE_URL)
 *   npm run a11y:ci         # build-free CI path: starts `next start` itself,
 *                           # waits for readiness, audits, shuts down.
 *
 * Loads each main page in headless Chromium, injects axe-core, and reports
 * every violation. Exits non-zero when any page has violations, so CI fails
 * on accessibility regressions. A cognitive-accessibility product must not
 * ship WCAG failures.
 */
import { spawn } from "node:child_process";

import { chromium } from "playwright";
import { AxeBuilder } from "@axe-core/playwright";

const PORT = Number(process.env.A11Y_PORT || 3170);
const BASE_URL = process.env.A11Y_BASE_URL || `http://127.0.0.1:${PORT}`;
const MANAGE_SERVER = process.argv.includes("--serve");

const PAGES = ["/", "/playground", "/quiz", "/docs", "/changelog"];

function startServer() {
  const child = spawn("npx", ["next", "start", "-p", String(PORT)], {
    stdio: ["ignore", "ignore", "inherit"],
    detached: false
  });
  return child;
}

async function waitForServer(url, timeoutMs = 45000) {
  const deadline = Date.now() + timeoutMs;
  process.stdout.write(`waiting for ${url} `);
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { redirect: "manual" });
      if (response.status < 500) {
        process.stdout.write(" up\n");
        return true;
      }
    } catch {
      // not listening yet
    }
    process.stdout.write(".");
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  process.stdout.write(" timed out\n");
  return false;
}

async function audit() {
  let total = 0;
  const browser = await chromium.launch();
  // Explicit context: @axe-core/playwright calls context.newPage internally
  // while finishing its run, which a bare browser.newPage() cannot serve on
  // current Playwright versions.
  const context = await browser.newContext();
  const page = await context.newPage();
  for (const path of PAGES) {
    const url = BASE_URL + path;
    const response = await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
    if (!response || response.status() >= 400) {
      console.error(`${path}: HTTP ${response ? response.status() : "no response"}`);
      total += 1;
      continue;
    }
    const results = await new AxeBuilder({ page }).analyze();
    const violations = results.violations;
    if (!violations.length) {
      console.log(`${path}: clean`);
      continue;
    }
    total += violations.length;
    console.log(`${path}: ${violations.length} violation(s)`);
    for (const violation of violations) {
      console.log(`  [${violation.impact}] ${violation.id}: ${violation.help}`);
      for (const node of violation.nodes.slice(0, 3)) {
        console.log(`      ${JSON.stringify(node.target).slice(0, 100)}`);
      }
    }
  }
  await context.close();
  await browser.close();
  console.log(`\nTOTAL: ${total} violation(s) across ${PAGES.length} page(s)`);
  return total;
}

async function main() {
  let server = null;
  if (MANAGE_SERVER) {
    server = startServer();
    const ready = await waitForServer(`${BASE_URL}/`);
    if (!ready) {
      server.kill("SIGTERM");
      process.exit(1);
    }
  }

  let total = 0;
  try {
    total = await audit();
  } finally {
    if (server) {
      server.kill("SIGTERM");
      await new Promise((resolve) => {
        server.once("exit", resolve);
        setTimeout(resolve, 5000);
      });
    }
  }
  process.exitCode = total === 0 ? 0 : 1;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
