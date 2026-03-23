import fs from "node:fs/promises";
import path from "node:path";

export type DocItem = {
  slug: string;
  title: string;
  section: "core" | "integrations";
};

const docsDir = path.join(process.cwd(), "content", "docs");

const TITLE_OVERRIDES: Record<string, string> = {
  "getting-started": "Getting Started",
  profiles: "Profiles",
  configuration: "Configuration",
  memory: "Memory",
  quiz: "Quiz",
  streaming: "Streaming",
  "custom-profiles": "Custom Profiles",
  contributing: "Contributing",
  "integrations/openai": "OpenAI",
  "integrations/anthropic": "Anthropic",
  "integrations/langchain": "LangChain",
  "integrations/huggingface": "HuggingFace",
  "integrations/rest-api": "REST API"
};

function prettyTitle(slug: string): string {
  return (
    TITLE_OVERRIDES[slug] ||
    slug
      .split("/")
      .pop()
      ?.replace(/-/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase()) ||
    slug
  );
}

async function walkDocs(relative = ""): Promise<string[]> {
  const target = path.join(docsDir, relative);
  const entries = await fs.readdir(target, { withFileTypes: true });

  const files: string[] = [];
  for (const entry of entries) {
    if (entry.isDirectory()) {
      const nested = await walkDocs(path.join(relative, entry.name));
      files.push(...nested);
      continue;
    }
    if (entry.name.endsWith(".md") || entry.name.endsWith(".mdx")) {
      files.push(path.join(relative, entry.name).replace(/\\/g, "/"));
    }
  }

  return files;
}

export async function listDocs(): Promise<DocItem[]> {
  const files = await walkDocs("");
  const docs = files
    .map((file) => {
      const slug = file.replace(/\.mdx?$/, "");
      return {
        slug,
        title: prettyTitle(slug),
        section: slug.startsWith("integrations/") ? "integrations" : "core"
      } as DocItem;
    })
    .sort((a, b) => a.title.localeCompare(b.title));

  return docs;
}

export async function getDocSource(slug: string): Promise<string | null> {
  const mdxPath = path.join(docsDir, `${slug}.mdx`);
  const mdPath = path.join(docsDir, `${slug}.md`);

  try {
    return await fs.readFile(mdxPath, "utf8");
  } catch {
    try {
      return await fs.readFile(mdPath, "utf8");
    } catch {
      return null;
    }
  }
}

export function extractHeadings(source: string): Array<{ id: string; depth: number; text: string }> {
  const lines = source.split(/\r?\n/);
  const headings: Array<{ id: string; depth: number; text: string }> = [];

  for (const line of lines) {
    const match = line.match(/^(##|###)\s+(.+)$/);
    if (!match) {
      continue;
    }
    const depth = match[1].length;
    const text = match[2].trim();
    const id = text
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .trim()
      .replace(/\s+/g, "-");
    headings.push({ id, depth, text });
  }

  return headings;
}
