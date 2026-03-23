"use client";

import { useState } from "react";

export function NewsletterForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setStatus("");
    try {
      const response = await fetch("/api/newsletter/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload?.error || "Subscription failed");
      }
      setStatus("Check your inbox to confirm subscription.");
      setEmail("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Subscription failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md">
      <div className="flex flex-wrap gap-2">
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
          className="h-11 flex-1 rounded-xl border border-black/10 bg-white px-3 text-sm"
        />
        <button
          onClick={submit}
          disabled={loading}
          className="h-11 rounded-xl bg-brand-primary px-4 text-sm font-semibold text-white"
        >
          {loading ? "Sending..." : "Get updates"}
        </button>
      </div>
      <p className="mt-1 text-xs text-brand-slate">No spam. Unsubscribe any time.</p>
      {status ? <p className="mt-1 text-xs text-brand-ink">{status}</p> : null}
    </div>
  );
}
