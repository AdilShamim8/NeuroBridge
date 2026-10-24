"use client";

import { BrainCircuit, Menu, X } from "lucide-react";
import type { Route } from "next";
import Link from "next/link";
import { useEffect, useState } from "react";

import { trackEvent } from "@/lib/analytics";
import { cn } from "@/lib/utils";

/** GitHub mark (lucide dropped brand icons in 1.x). Sized like lucide icons. */
function GithubMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className={className} fill="currentColor">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
    </svg>
  );
}

const links: { href: Route; label: string }[] = [
  { href: "/playground", label: "Playground" },
  { href: "/quiz", label: "Quiz" },
  { href: "/stats", label: "Stats" },
  { href: "/docs", label: "Docs" },
  { href: "/changelog", label: "Changelog" },
  { href: "/newsletter", label: "Newsletter" }
];

export function Nav() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handle = () => setScrolled(window.scrollY > 8);
    handle();
    window.addEventListener("scroll", handle);
    return () => window.removeEventListener("scroll", handle);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 mx-auto mt-2 w-[min(1100px,95vw)] rounded-2xl px-4 py-3 transition",
        scrolled ? "glass shadow-lg" : "bg-transparent"
      )}
    >
      <nav className="flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-brand-ink">
          <BrainCircuit className="h-6 w-6 text-brand-primary" />
          <span className="text-lg font-extrabold tracking-tight">NeuroBridge</span>
        </Link>

        <div className="hidden items-center gap-4 md:flex">
          {links.map((item) => (
            <Link key={item.href} href={item.href} className="text-sm font-medium text-brand-slate hover:text-brand-ink">
              {item.label}
            </Link>
          ))}
          <a
            href="https://github.com/AdilShamim8/NeuroBridge"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 rounded-xl px-3 py-2 text-sm font-semibold hover:bg-black/5"
            onClick={() => trackEvent("github_click", { source: "nav-desktop" })}
          >
            <GithubMark className="h-4 w-4" /> GitHub
          </a>
        </div>

        <button className="md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Toggle menu">
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {open && (
        <div className="mt-3 space-y-2 border-t border-black/10 pt-3 md:hidden">
          {links.map((item) => (
            <Link key={item.href} href={item.href} className="block rounded-lg px-2 py-1 text-sm font-medium" onClick={() => setOpen(false)}>
              {item.label}
            </Link>
          ))}
          <a
            href="https://github.com/AdilShamim8/NeuroBridge"
            target="_blank"
            rel="noreferrer"
            className="block rounded-lg px-2 py-1 text-sm font-medium"
            onClick={() => trackEvent("github_click", { source: "nav-mobile" })}
          >
            GitHub
          </a>
        </div>
      )}
    </header>
  );
}
