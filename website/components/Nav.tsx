"use client";

import { BrainCircuit, Github, Menu, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { trackEvent } from "@/lib/analytics";
import { cn } from "@/lib/utils";

const links = [
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
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 rounded-xl px-3 py-2 text-sm font-semibold hover:bg-black/5"
            onClick={() => trackEvent("github_click", { source: "nav-desktop" })}
          >
            <Github className="h-4 w-4" /> GitHub
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
            href="https://github.com"
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
