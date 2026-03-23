"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { NewsletterForm } from "@/components/NewsletterForm";
import { trackEvent } from "@/lib/analytics";

export function Footer() {
  return (
    <footer className="mx-auto mt-20 w-[min(1100px,95vw)] rounded-2xl border border-black/10 bg-white/70 p-6">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="space-y-2">
          <p className="text-sm text-brand-slate">Built for cognitive accessibility in AI systems.</p>
          <NewsletterForm />
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/changelog"><Badge>Changelog</Badge></Link>
          <Link href="/newsletter"><Badge>Newsletter</Badge></Link>
          <a href="https://github.com" target="_blank" rel="noreferrer" onClick={() => trackEvent("github_click", { source: "footer" })}><Badge>GitHub</Badge></a>
          <a href="https://discord.com" target="_blank" rel="noreferrer"><Badge>Discord</Badge></a>
          <a href="https://npmjs.com" target="_blank" rel="noreferrer"><Badge>npm</Badge></a>
          <a href="https://pypi.org" target="_blank" rel="noreferrer"><Badge>PyPI</Badge></a>
        </div>
      </div>
    </footer>
  );
}
