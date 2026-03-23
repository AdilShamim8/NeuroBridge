import fs from "node:fs/promises";
import path from "node:path";

function parseChangelog(content: string): Array<{ version: string; date: string; items: string[] }> {
  const lines = content.split(/\r?\n/);
  const releases: Array<{ version: string; date: string; items: string[] }> = [];
  let current: { version: string; date: string; items: string[] } | null = null;

  for (const line of lines) {
    const releaseMatch = line.match(/^## \[(.+)\](?: - (\d{4}-\d{2}-\d{2}))?/);
    if (releaseMatch) {
      if (current) releases.push(current);
      current = {
        version: releaseMatch[1],
        date: releaseMatch[2] || "Unreleased",
        items: []
      };
      continue;
    }
    if (line.startsWith("- ") && current) {
      current.items.push(line.slice(2));
    }
  }

  if (current) releases.push(current);
  return releases;
}

export default async function ChangelogPage() {
  const changelogPath = path.join(process.cwd(), "..", "CHANGELOG.md");
  const content = await fs.readFile(changelogPath, "utf8");
  const releases = parseChangelog(content);

  return (
    <section className="space-y-8">
      <h1 className="text-4xl font-black text-brand-ink">Changelog</h1>
      <p className="text-brand-slate">Release timeline for NeuroBridge updates.</p>

      <div className="space-y-4">
        {releases.map((release) => (
          <article key={release.version} className="rounded-2xl border border-black/10 bg-white/85 p-6">
            <p className="text-xs font-bold uppercase tracking-wide text-brand-slate">{release.date}</p>
            <h2 className="mt-1 text-2xl font-black text-brand-primary">{release.version}</h2>
            <ul className="mt-3 space-y-2 text-sm text-brand-slate">
              {release.items.length ? release.items.map((item) => <li key={item}>• {item}</li>) : <li>No listed changes.</li>}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}
