"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { adaptText } from "@/lib/api";

const profiles = ["adhd", "autism", "dyslexia", "anxiety", "dyscalculia"] as const;

export function DemoSection() {
  const [input, setInput] = useState("AI output can feel dense and overwhelming for many readers.");
  const [profile, setProfile] = useState<(typeof profiles)[number]>("adhd");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);

  const chars = useMemo(() => input.length, [input]);

  async function handleAdapt() {
    setLoading(true);
    try {
      const result = await adaptText({ text: input, profile, output_format: "markdown" });
      setOutput(result.adapted_text);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!input.trim()) {
      setOutput("");
      return;
    }
    const timer = setTimeout(() => {
      void handleAdapt();
    }, 350);
    return () => clearTimeout(timer);
  }, [input, profile]);

  return (
    <section className="mt-16 grid gap-4 lg:grid-cols-2">
      <Card>
        <p className="text-sm font-bold text-brand-slate">Live mini-demo</p>
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          className="mt-3 min-h-[140px] w-full rounded-xl border border-black/10 p-3"
        />
        <div className="mt-2 text-right text-xs text-brand-slate">{chars} chars</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {profiles.map((item) => (
            <button
              key={item}
              className={`badge-pill border ${profile === item ? "border-brand-primary bg-brand-primary text-white" : "border-black/10"}`}
              onClick={() => setProfile(item)}
            >
              {item.toUpperCase()}
            </button>
          ))}
        </div>
        <Button className="mt-4 w-full" onClick={handleAdapt} disabled={loading}>
          {loading ? "Updating..." : "Adapt now"}
        </Button>
      </Card>
      <Card>
        <p className="text-sm font-bold text-brand-slate">Adapted output</p>
        <div className="mt-3 min-h-[220px] whitespace-pre-wrap rounded-xl bg-brand-mist/60 p-4 text-sm text-brand-ink">
          {output || "Your adapted output will appear here."}
        </div>
      </Card>
    </section>
  );
}
