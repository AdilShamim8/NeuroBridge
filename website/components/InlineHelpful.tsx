"use client";

import { useState } from "react";

type InlineHelpfulProps = {
  page: "playground" | "quiz";
  profile: string;
};

export function InlineHelpful({ page, profile }: InlineHelpfulProps) {
  const [done, setDone] = useState(false);

  async function send(rating: "yes" | "no") {
    await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ page, profile, rating })
    });
    setDone(true);
  }

  if (done) {
    return <p className="text-xs text-brand-slate">Thanks for sharing.</p>;
  }

  return (
    <div className="rounded-xl border border-brand-secondary/30 bg-emerald-50 p-3 text-sm">
      <p className="font-semibold text-brand-ink">Was this helpful?</p>
      <div className="mt-2 flex gap-2">
        <button className="rounded-lg border border-black/10 bg-white px-3 py-1" onClick={() => send("yes")}>Yes</button>
        <button className="rounded-lg border border-black/10 bg-white px-3 py-1" onClick={() => send("no")}>No</button>
      </div>
    </div>
  );
}
