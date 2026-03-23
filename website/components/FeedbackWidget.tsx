"use client";

import { useEffect, useState } from "react";

type FeedbackWidgetProps = {
  page: "playground" | "quiz";
  profile?: string;
};

const SESSION_KEY = "nb-feedback-seen";

export function FeedbackWidget({ page, profile }: FeedbackWidgetProps) {
  const [open, setOpen] = useState(false);
  const [hidden, setHidden] = useState(false);
  const [rating, setRating] = useState<"neutral" | "happy" | "love" | null>(null);
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    const seen = sessionStorage.getItem(SESSION_KEY);
    if (seen) {
      setHidden(true);
      return;
    }
    setOpen(true);
    sessionStorage.setItem(SESSION_KEY, "1");
  }, []);

  if (hidden || profile === "anxiety") {
    return null;
  }

  async function submit() {
    if (!rating) {
      return;
    }
    await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ page, profile: profile || "unknown", rating, message })
    });
    setStatus("Thanks for the feedback.");
    setTimeout(() => setHidden(true), 1200);
  }

  if (!open) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-[min(340px,92vw)] rounded-2xl border border-black/10 bg-white p-4 shadow-xl">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-brand-ink">How did NeuroBridge work for you?</p>
        <button className="rounded border border-black/10 px-2 py-1 text-xs" onClick={() => setHidden(true)} aria-label="Close feedback widget">
          Close
        </button>
      </div>

      <div className="mt-3 flex gap-2">
        <button className="rounded-lg border px-3 py-2 text-sm" onClick={() => setRating("neutral")}>😐</button>
        <button className="rounded-lg border px-3 py-2 text-sm" onClick={() => setRating("happy")}>😊</button>
        <button className="rounded-lg border px-3 py-2 text-sm" onClick={() => setRating("love")}>🤩</button>
      </div>

      {rating ? (
        <div className="mt-3 space-y-2">
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Tell us more (optional)"
            className="h-20 w-full rounded-lg border border-black/10 p-2 text-sm"
          />
          <button className="rounded-lg bg-brand-primary px-3 py-2 text-sm font-semibold text-white" onClick={submit}>
            Submit
          </button>
        </div>
      ) : null}
      {status ? <p className="mt-2 text-xs text-brand-slate">{status}</p> : null}
    </div>
  );
}
