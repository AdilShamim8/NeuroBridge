import type { Metadata } from "next";
import { headers } from "next/headers";

export const metadata: Metadata = {
  title: "Community Stats",
  description: "Live community and adoption metrics for NeuroBridge.",
  alternates: { canonical: "/stats" }
};

type StatsPayload = {
  repo: string;
  stars: number;
  stars30d: Array<{ day: string; stars: number }>;
  starsGained30d: number;
  openIssues: number;
  closedIssues: number;
  contributors: number;
  pypiDownloads30d: number;
  npmDownloads30d: number;
  huggingFaceUsage30d: number;
  generatedAt: string;
};

const FALLBACK: StatsPayload = {
  repo: "octocat/Hello-World",
  stars: 0,
  stars30d: [],
  starsGained30d: 0,
  openIssues: 0,
  closedIssues: 0,
  contributors: 0,
  pypiDownloads30d: 0,
  npmDownloads30d: 0,
  huggingFaceUsage30d: 0,
  generatedAt: new Date(0).toISOString()
};

async function getStats(): Promise<StatsPayload> {
  const headerStore = headers();
  const proto = headerStore.get("x-forwarded-proto") || "http";
  const host = headerStore.get("x-forwarded-host") || headerStore.get("host") || "localhost:3000";
  const origin = `${proto}://${host}`;

  try {
    const response = await fetch(`${origin}/api/stats`, {
      next: { revalidate: 3600 }
    });
    if (!response.ok) {
      return FALLBACK;
    }
    return (await response.json()) as StatsPayload;
  } catch {
    return FALLBACK;
  }
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function Sparkline({ series }: { series: Array<{ day: string; stars: number }> }) {
  if (!series.length) {
    return <p className="text-sm text-brand-slate">No star history available yet.</p>;
  }

  const max = Math.max(...series.map((point) => point.stars), 1);

  return (
    <div className="mt-3">
      <div className="grid grid-cols-10 gap-1 md:grid-cols-30">
        {series.map((point) => (
          <div
            key={point.day}
            title={`${point.day}: ${point.stars}`}
            className="rounded-sm bg-brand-primary/75"
            style={{ height: `${Math.max(8, Math.round((point.stars / max) * 42))}px` }}
          />
        ))}
      </div>
      <p className="mt-2 text-xs text-brand-slate">30-day GitHub stars trend</p>
    </div>
  );
}

export default async function StatsPage() {
  const stats = await getStats();

  return (
    <section className="space-y-8 pb-8">
      <header className="rounded-3xl border border-brand-primary/20 bg-white/80 p-6">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand-slate">Community Pulse</p>
        <h1 className="mt-2 text-4xl font-black text-brand-ink">NeuroBridge Stats</h1>
        <p className="mt-2 text-sm text-brand-slate">
          Data source: GitHub, PyPIStats, npm. Refreshed hourly via Vercel cron.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-2xl border border-black/10 bg-white/85 p-5">
          <p className="text-xs uppercase tracking-wide text-brand-slate">GitHub Stars</p>
          <p className="mt-2 text-3xl font-black text-brand-primary">{formatNumber(stats.stars)}</p>
          <p className="mt-1 text-sm text-brand-slate">+{formatNumber(stats.starsGained30d)} in last 30 days</p>
          <Sparkline series={stats.stars30d} />
        </article>

        <article className="rounded-2xl border border-black/10 bg-white/85 p-5">
          <p className="text-xs uppercase tracking-wide text-brand-slate">Package Adoption</p>
          <p className="mt-2 text-3xl font-black text-brand-ink">{formatNumber(stats.pypiDownloads30d)}</p>
          <p className="text-sm text-brand-slate">PyPI downloads (30d)</p>
          <p className="mt-3 text-2xl font-black text-brand-ink">{formatNumber(stats.npmDownloads30d)}</p>
          <p className="text-sm text-brand-slate">npm downloads (30d)</p>
        </article>

        <article className="rounded-2xl border border-black/10 bg-white/85 p-5">
          <p className="text-xs uppercase tracking-wide text-brand-slate">Project Health</p>
          <p className="mt-2 text-3xl font-black text-brand-ink">{formatNumber(stats.openIssues)}</p>
          <p className="text-sm text-brand-slate">Open issues</p>
          <p className="mt-3 text-2xl font-black text-brand-ink">{formatNumber(stats.closedIssues)}</p>
          <p className="text-sm text-brand-slate">Closed issues</p>
          <p className="mt-3 text-2xl font-black text-brand-ink">{formatNumber(stats.contributors)}</p>
          <p className="text-sm text-brand-slate">Contributors</p>
        </article>
      </div>

      <article className="rounded-2xl border border-brand-primary/20 bg-brand-primary/5 p-5">
        <p className="text-xs uppercase tracking-wide text-brand-slate">HuggingFace Usage</p>
        <p className="mt-2 text-3xl font-black text-brand-primary">{formatNumber(stats.huggingFaceUsage30d)}</p>
        <p className="text-sm text-brand-slate">Space usage over the last 30 days</p>
      </article>

      <footer className="text-xs text-brand-slate">
        Repo: {stats.repo} • Last refresh: {new Date(stats.generatedAt).toLocaleString()}
      </footer>
    </section>
  );
}
