"use client";

import { Index } from "flexsearch";
import { Menu, Search, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useMemo, useState } from "react";

type DocItem = {
  slug: string;
  title: string;
  section: "core" | "integrations";
};

type Heading = {
  id: string;
  depth: number;
  text: string;
};

type DocsShellProps = {
  docs: DocItem[];
  headings: Heading[];
  children?: ReactNode;
};

export function DocsShell({ docs, headings, children }: DocsShellProps) {
  const pathname = usePathname();
  const currentSlug = pathname?.startsWith("/docs/") ? pathname.replace(/^\/docs\//, "") : undefined;
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [detectedHeadings, setDetectedHeadings] = useState<Heading[]>(headings);

  useEffect(() => {
    if (headings.length) {
      setDetectedHeadings(headings);
      return;
    }
    const nodes = Array.from(document.querySelectorAll("article h2, article h3"));
    setDetectedHeadings(
      nodes.map((node) => ({
        id: node.id,
        depth: node.tagName === "H3" ? 3 : 2,
        text: node.textContent || ""
      }))
    );
  }, [headings, pathname]);

  const index = useMemo(() => {
    const idx = new Index({ tokenize: "forward" });
    docs.forEach((item) => idx.add(item.slug, item.title));
    return idx;
  }, [docs]);

  const results = useMemo(() => {
    if (!query.trim()) {
      return docs;
    }
    const ids = index.search(query, { limit: 20 }) as string[];
    const map = new Map(docs.map((item) => [item.slug, item]));
    return ids.map((id) => map.get(id)).filter(Boolean) as DocItem[];
  }, [docs, index, query]);

  const coreDocs = results.filter((item: DocItem) => item.section === "core");
  const integrationDocs = results.filter((item: DocItem) => item.section === "integrations");

  return (
    <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,720px)_220px]">
      <aside className="hidden lg:block">
        <DocsNav
          query={query}
          setQuery={setQuery}
          currentSlug={currentSlug}
          coreDocs={coreDocs}
          integrationDocs={integrationDocs}
        />
      </aside>

      <div className="lg:hidden">
        <button
          onClick={() => setOpen(true)}
          className="inline-flex min-h-12 items-center gap-2 rounded-xl border border-black/10 bg-white px-4 text-base font-semibold"
        >
          <Menu className="h-4 w-4" /> Browse docs
        </button>
      </div>

      <aside className="lg:hidden">
        <div className="rounded-2xl border border-black/10 bg-white/80 p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-brand-slate">On this page</p>
          <ul className="mt-2 space-y-2 text-sm">
            {detectedHeadings.map((item) => (
              <li key={item.id} className={item.depth === 3 ? "ml-3" : ""}>
                <a href={`#${item.id}`} className="text-brand-slate hover:text-brand-ink">
                  {item.text}
                </a>
              </li>
            ))}
            {!detectedHeadings.length ? <li className="text-brand-slate">No section headings.</li> : null}
          </ul>
        </div>
      </aside>

      {open ? (
        <div className="fixed inset-0 z-50 bg-black/30 lg:hidden" onClick={() => setOpen(false)}>
          <div
            className="absolute bottom-0 left-0 right-0 max-h-[75vh] overflow-y-auto rounded-t-2xl bg-white p-4"
            onClick={(event: { stopPropagation: () => void }) => event.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <p className="font-bold">Docs navigation</p>
              <button onClick={() => setOpen(false)} className="rounded-lg border border-black/10 p-2" aria-label="Close docs navigation">
                <span className="inline-flex items-center gap-1 text-sm font-semibold"><X className="h-4 w-4" /> Close</span>
              </button>
            </div>
            <DocsNav
              query={query}
              setQuery={setQuery}
              currentSlug={currentSlug}
              coreDocs={coreDocs}
              integrationDocs={integrationDocs}
              onNavigate={() => setOpen(false)}
            />
          </div>
        </div>
      ) : null}

      <section className="min-w-0">{children}</section>

      <aside className="hidden lg:block">
        <div className="sticky top-20 rounded-2xl border border-black/10 bg-white/80 p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-brand-slate">On this page</p>
          <ul className="mt-2 space-y-2 text-sm">
            {detectedHeadings.map((item) => (
              <li key={item.id} className={item.depth === 3 ? "ml-3" : ""}>
                <a href={`#${item.id}`} className="text-brand-slate hover:text-brand-ink">
                  {item.text}
                </a>
              </li>
            ))}
            {!detectedHeadings.length ? <li className="text-brand-slate">No section headings.</li> : null}
          </ul>
        </div>
      </aside>
    </div>
  );
}

type DocsNavProps = {
  query: string;
  setQuery: (value: string) => void;
  currentSlug?: string;
  coreDocs: DocItem[];
  integrationDocs: DocItem[];
  onNavigate?: () => void;
};

function DocsNav({ query, setQuery, currentSlug, coreDocs, integrationDocs, onNavigate }: DocsNavProps) {
  return (
    <div className="sticky top-20 rounded-2xl border border-black/10 bg-white/80 p-4">
      <label className="mb-2 flex items-center gap-2 rounded-lg border border-black/10 bg-white px-3 py-2 text-xs text-brand-slate">
        <Search className="h-4 w-4" />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search docs"
          className="w-full bg-transparent outline-none"
        />
      </label>

      <p className="mt-3 text-[11px] font-bold uppercase tracking-wide text-brand-slate">Core</p>
      <ul className="mt-1 space-y-1">
        {coreDocs.map((item) => (
          <li key={item.slug}>
            <Link
              href={`/docs/${item.slug}`}
              onClick={onNavigate}
              className={`block rounded-lg px-2 py-1 text-sm ${currentSlug === item.slug ? "bg-brand-mist text-brand-ink" : "text-brand-slate hover:bg-black/5"}`}
            >
              {item.title}
            </Link>
          </li>
        ))}
      </ul>

      <p className="mt-4 text-[11px] font-bold uppercase tracking-wide text-brand-slate">Integrations</p>
      <ul className="mt-1 space-y-1">
        {integrationDocs.map((item) => (
          <li key={item.slug}>
            <Link
              href={`/docs/${item.slug}`}
              onClick={onNavigate}
              className={`block rounded-lg px-2 py-1 text-sm ${currentSlug === item.slug ? "bg-brand-mist text-brand-ink" : "text-brand-slate hover:bg-black/5"}`}
            >
              {item.title}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
