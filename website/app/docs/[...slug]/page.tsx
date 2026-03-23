import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { MDXRemote } from "next-mdx-remote/rsc";

import { DocsShell } from "@/components/DocsShell";
import { DocViewTracker } from "@/components/DocViewTracker";
import { mdxComponents } from "@/components/mdx";
import { extractHeadings, getDocSource, listDocs } from "@/lib/docs";

type Props = { params: { slug: string[] } };

function toSlug(parts: string[]): string {
  return parts.join("/");
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = toSlug(params.slug || []);
  const source = await getDocSource(slug);
  const firstTitle = source?.match(/^#\s+(.+)$/m)?.[1]?.trim() || "Documentation";
  return {
    title: `${firstTitle} | Docs`,
    description: `NeuroBridge documentation for ${firstTitle}.`,
    alternates: { canonical: `/docs/${slug}` },
    openGraph: {
      title: `${firstTitle} | NeuroBridge Docs`,
      description: `Guidance for ${firstTitle} in NeuroBridge.`,
      images: [`/api/og?profile=${encodeURIComponent(firstTitle)}`]
    }
  };
}

export default async function DocPage({ params }: Props) {
  const slug = toSlug(params.slug || []);
  const source = await getDocSource(slug);
  if (!source) {
    notFound();
  }

  const docs = await listDocs();
  const headings = extractHeadings(source);

  return (
    <DocsShell docs={docs} headings={headings}>
      <DocViewTracker slug={slug} />
      <article className="prose prose-slate max-w-none rounded-2xl bg-white/80 p-8 leading-8">
        <MDXRemote source={source} components={mdxComponents} />
      </article>
    </DocsShell>
  );
}
