import fs from "node:fs/promises";
import path from "node:path";

function parseReleases(content: string): Array<{ version: string; date: string; items: string[] }> {
  const lines = content.split(/\r?\n/);
  const releases: Array<{ version: string; date: string; items: string[] }> = [];
  let current: { version: string; date: string; items: string[] } | null = null;

  for (const line of lines) {
    const releaseMatch = line.match(/^## \[(.+)\](?: - (\d{4}-\d{2}-\d{2}))?/);
    if (releaseMatch) {
      if (current) releases.push(current);
      current = { version: releaseMatch[1], date: releaseMatch[2] || new Date().toISOString().slice(0, 10), items: [] };
      continue;
    }
    if (line.startsWith("- ") && current) {
      current.items.push(line.slice(2));
    }
  }

  if (current) releases.push(current);
  return releases;
}

export async function GET() {
  const changelogPath = path.join(process.cwd(), "..", "CHANGELOG.md");
  const content = await fs.readFile(changelogPath, "utf8");
  const releases = parseReleases(content);

  const items = releases
    .map((release) => {
      const description = release.items.join("; ") || "No details provided.";
      return `
        <item>
          <title>${release.version}</title>
          <link>https://neurobridge.dev/changelog</link>
          <guid>https://neurobridge.dev/changelog#${release.version}</guid>
          <pubDate>${new Date(release.date).toUTCString()}</pubDate>
          <description><![CDATA[${description}]]></description>
        </item>`;
    })
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>NeuroBridge Changelog</title>
    <link>https://neurobridge.dev/changelog</link>
    <description>Release updates and digests for subscribers.</description>
    ${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8"
    }
  });
}
