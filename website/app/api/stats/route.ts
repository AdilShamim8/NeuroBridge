import { NextResponse } from "next/server";

export const revalidate = 3600;

type DailyPoint = { day: string; stars: number };

type StatsPayload = {
  repo: string;
  stars: number;
  stars30d: DailyPoint[];
  starsGained30d: number;
  openIssues: number;
  closedIssues: number;
  contributors: number;
  pypiDownloads30d: number;
  npmDownloads30d: number;
  huggingFaceUsage30d: number;
  generatedAt: string;
};

function dateKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function buildEmptySeries(): DailyPoint[] {
  const now = new Date();
  const points: DailyPoint[] = [];
  for (let i = 29; i >= 0; i -= 1) {
    const day = new Date(now);
    day.setUTCDate(now.getUTCDate() - i);
    points.push({ day: dateKey(day), stars: 0 });
  }
  return points;
}

async function fetchJson<T>(url: string, headers: Record<string, string>): Promise<T | null> {
  try {
    const response = await fetch(url, { headers, next: { revalidate: 3600 } });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function parseLastPage(linkHeader: string | null): number {
  if (!linkHeader) {
    return 0;
  }
  const match = linkHeader.match(/&page=(\d+)>; rel="last"/);
  return match ? Number(match[1]) : 0;
}

async function getGithubStats(repo: string, headers: Record<string, string>): Promise<{
  stars: number;
  stars30d: DailyPoint[];
  starsGained30d: number;
  openIssues: number;
  closedIssues: number;
  contributors: number;
}> {
  const emptySeries = buildEmptySeries();
  const repoData = await fetchJson<{
    stargazers_count?: number;
  }>(`https://api.github.com/repos/${repo}`, headers);

  const openIssuesData = await fetchJson<{ total_count?: number }>(
    `https://api.github.com/search/issues?q=repo:${repo}+type:issue+state:open`,
    headers
  );
  const closedIssuesData = await fetchJson<{ total_count?: number }>(
    `https://api.github.com/search/issues?q=repo:${repo}+type:issue+state:closed`,
    headers
  );

  let contributors = 0;
  try {
    const contributorsResponse = await fetch(
      `https://api.github.com/repos/${repo}/contributors?per_page=1&anon=true`,
      { headers, next: { revalidate: 3600 } }
    );
    if (contributorsResponse.ok) {
      const lastPage = parseLastPage(contributorsResponse.headers.get("link"));
      if (lastPage > 0) {
        contributors = lastPage;
      } else {
        const firstPage = (await contributorsResponse.json()) as unknown[];
        contributors = firstPage.length;
      }
    }
  } catch {
    contributors = 0;
  }

  const starsNow = Number(repoData?.stargazers_count || 0);
  const since = new Date();
  since.setUTCDate(since.getUTCDate() - 29);

  const starEvents: Record<string, number> = {};
  let starsGained30d = 0;

  for (let page = 1; page <= 4; page += 1) {
    try {
      const response = await fetch(
        `https://api.github.com/repos/${repo}/stargazers?per_page=100&page=${page}`,
        {
          headers: {
            ...headers,
            Accept: "application/vnd.github.star+json"
          },
          next: { revalidate: 3600 }
        }
      );
      if (!response.ok) {
        break;
      }
      const payload = (await response.json()) as Array<{ starred_at?: string }>;
      if (!payload.length) {
        break;
      }

      let reachedOlderWindow = false;
      for (const item of payload) {
        if (!item.starred_at) {
          continue;
        }
        const starredAt = new Date(item.starred_at);
        if (starredAt < since) {
          reachedOlderWindow = true;
          continue;
        }
        const key = dateKey(starredAt);
        starEvents[key] = (starEvents[key] || 0) + 1;
        starsGained30d += 1;
      }
      if (reachedOlderWindow) {
        break;
      }
    } catch {
      break;
    }
  }

  const baseline = Math.max(0, starsNow - starsGained30d);
  let running = baseline;
  const stars30d = emptySeries.map((point) => {
    running += starEvents[point.day] || 0;
    return { day: point.day, stars: running };
  });

  return {
    stars: starsNow,
    stars30d,
    starsGained30d,
    openIssues: Number(openIssuesData?.total_count || 0),
    closedIssues: Number(closedIssuesData?.total_count || 0),
    contributors
  };
}

export async function GET() {
  const repo = process.env.NEUROBRIDGE_GITHUB_REPO || "octocat/Hello-World";
  const packageName = process.env.NEUROBRIDGE_PACKAGE_NAME || "neurobridge";
  const npmPackage = process.env.NEUROBRIDGE_NPM_PACKAGE || "neurobridge";

  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json"
  };
  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  const github = await getGithubStats(repo, headers);

  const pypi = await fetchJson<{ data?: { last_month?: number } }>(
    `https://pypistats.org/api/packages/${packageName}/recent`,
    {}
  );
  const npm = await fetchJson<{ downloads?: number }>(
    `https://api.npmjs.org/downloads/point/last-month/${npmPackage}`,
    {}
  );

  const payload: StatsPayload = {
    repo,
    stars: github.stars,
    stars30d: github.stars30d,
    starsGained30d: github.starsGained30d,
    openIssues: github.openIssues,
    closedIssues: github.closedIssues,
    contributors: github.contributors,
    pypiDownloads30d: Number(pypi?.data?.last_month || 0),
    npmDownloads30d: Number(npm?.downloads || 0),
    huggingFaceUsage30d: Number(process.env.NEUROBRIDGE_HF_USAGE || 0),
    generatedAt: new Date().toISOString()
  };

  return NextResponse.json(payload);
}
