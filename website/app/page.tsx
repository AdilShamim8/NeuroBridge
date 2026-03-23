import { DemoSection } from "@/components/DemoSection";
import { Hero } from "@/components/Hero";
import { IntegrationLogos } from "@/components/IntegrationLogos";
import { ProblemSection } from "@/components/ProblemSection";
import { ProfileCards } from "@/components/ProfileCards";
import { AnimatedCounter } from "@/components/AnimatedCounter";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI That Speaks Your Language",
  description: "Try NeuroBridge live and adapt AI output for ADHD, Autism, Dyslexia, Anxiety, and Dyscalculia.",
  alternates: { canonical: "/" },
  openGraph: {
    title: "NeuroBridge",
    description: "Try profile-aware adaptation in your browser.",
    images: ["/api/og?profile=Home"]
  }
};

export default function HomePage() {
  return (
    <div className="pb-10">
      <Hero />

      <section className="mt-10 rounded-2xl border border-brand-primary/20 bg-white/70 p-6">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-brand-slate">Why this matters</p>
        <p className="mt-2 text-4xl font-black text-brand-primary">
          <AnimatedCounter target={1_500_000_000} /> people underserved by AI today
        </p>
      </section>

      <ProblemSection />
      <DemoSection />
      <ProfileCards />
      <IntegrationLogos />

      <section className="mt-16 rounded-3xl border border-black/5 bg-brand-ink p-8 text-white">
        <p className="text-sm uppercase tracking-[0.2em] text-white/70">Community quote</p>
        <p className="mt-3 max-w-3xl text-2xl font-semibold">
          "NeuroBridge turned AI from technically impressive into actually usable for my daily workflow."
        </p>
      </section>
    </div>
  );
}
