"use client";

import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { GitHubStars } from "@/components/GitHubStars";
import { Button } from "@/components/ui/button";
import { trackEvent } from "@/lib/analytics";

export function Hero() {
  const reduceMotion = useReducedMotion();

  return (
    <section className="relative overflow-hidden rounded-3xl border border-black/5 bg-hero-glow p-6 sm:p-8 md:p-14">
      <motion.p
        initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 8 }}
        animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-4 inline-flex rounded-full bg-white/75 px-4 py-1 text-xs font-bold uppercase tracking-[0.2em] text-brand-slate"
      >
        NeuroBridge
      </motion.p>
      <motion.h1
        initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 12 }}
        animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.6 }}
        className="max-w-2xl text-3xl font-black leading-tight text-brand-ink sm:text-4xl md:text-6xl"
      >
        AI That Speaks Your Language
      </motion.h1>
      <motion.p
        initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 12 }}
        animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.6 }}
        className="mt-4 max-w-xl text-base text-brand-slate md:text-lg"
      >
        Transform generic AI output into profile-aware communication for ADHD, Autism, Dyslexia, Anxiety, and Dyscalculia.
      </motion.p>
      <motion.div
        initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 8 }}
        animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.6 }}
        className="mt-8 flex flex-wrap gap-3"
      >
        <Link href="/playground" className="w-full sm:w-auto"><Button className="w-full">Try it now <ArrowRight className="ml-1 h-4 w-4" /></Button></Link>
        <Link href="/newsletter" className="w-full sm:w-auto"><Button variant="secondary" className="w-full">Join newsletter</Button></Link>
        <a href="https://github.com" target="_blank" rel="noreferrer" className="w-full sm:w-auto" onClick={() => trackEvent("github_click", { source: "hero-cta" })}><Button variant="secondary" className="w-full">View on GitHub</Button></a>
      </motion.div>
      <motion.div initial={reduceMotion ? { opacity: 1 } : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.45, duration: 0.5 }}>
        <GitHubStars />
      </motion.div>
    </section>
  );
}
