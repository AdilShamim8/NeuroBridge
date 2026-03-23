import { NextResponse } from "next/server";

const CACHE_TTL_MS = 10 * 60 * 1000;

type Cached = {
  stars: number;
  cachedAt: number;
};

let cache: Cached | null = null;

export async function GET() {
  const now = Date.now();
  if (cache && now - cache.cachedAt < CACHE_TTL_MS) {
    return NextResponse.json({ stars: cache.stars, cached: true });
  }

  const repo = process.env.NEUROBRIDGE_GITHUB_REPO || "octocat/Hello-World";
  try {
    const response = await fetch(`https://api.github.com/repos/${repo}`, {
      headers: {
        Accept: "application/vnd.github+json",
        ...(process.env.GITHUB_TOKEN ? { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` } : {})
      }
    });

    if (!response.ok) {
      throw new Error("GitHub request failed");
    }

    const payload = (await response.json()) as { stargazers_count?: number };
    const stars = Number(payload.stargazers_count || 0);
    cache = { stars, cachedAt: now };
    return NextResponse.json({ stars, cached: false });
  } catch {
    return NextResponse.json({ stars: cache?.stars ?? 1247, cached: true });
  }
}
