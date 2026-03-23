import Link from "next/link";
import type { Metadata } from "next";

import { DocsShell } from "@/components/DocsShell";
import { DocViewTracker } from "@/components/DocViewTracker";
import { listDocs } from "@/lib/docs";

export const metadata: Metadata = {
  title: "Documentation",
  description: "NeuroBridge docs for setup, profiles, integrations, and API.",
  alternates: { canonical: "/docs" },
  openGraph: {
    title: "NeuroBridge Docs",
    description: "Explore setup guides, integrations, and profile behavior.",
    images: ["/api/og?profile=Docs"]
  }
};

export default async function DocsIndexPage() {
  const docs = await listDocs();
  const coreDocs = docs.filter((item) => item.section === "core");
  const integrationDocs = docs.filter((item) => item.section === "integrations");

  return (
    <DocsShell docs={docs} headings={[]}>
      <DocViewTracker slug="index" />
      <section>
        <h1 className="text-4xl font-black text-brand-ink">Documentation</h1>
        <p className="mt-2 text-brand-slate">Browse guides and examples written in MDX.</p>

        <h2 className="mt-8 text-lg font-black text-brand-ink">Core</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {coreDocs.map((doc) => (
            <Link
              key={doc.slug}
              href={`/docs/${doc.slug}`}
              className="rounded-xl border border-black/10 bg-white/80 p-4 text-sm capitalize hover:border-brand-primary/40"
            >
              {doc.title}
            </Link>
          ))}
        </div>

        <h2 className="mt-8 text-lg font-black text-brand-ink">Integrations</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {integrationDocs.map((doc) => (
            <Link
              key={doc.slug}
              href={`/docs/${doc.slug}`}
              className="rounded-xl border border-black/10 bg-white/80 p-4 text-sm capitalize hover:border-brand-primary/40"
            >
              {doc.title}
            </Link>
          ))}
        </div>
      </section>
    </DocsShell>
  );
}
