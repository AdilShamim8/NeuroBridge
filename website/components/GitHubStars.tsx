"use client";

import { useEffect, useState } from "react";

import { trackEvent } from "@/lib/analytics";

export function GitHubStars() {
  const [display, setDisplay] = useState(0);
  const [target, setTarget] = useState(1247);

  useEffect(() => {
    void fetch("/api/github/stars")
      .then((response) => response.json())
      .then((payload: { stars?: number }) => {
        const next = Number(payload.stars || 1247);
        setTarget(next);
      })
      .catch(() => setTarget(1247));
  }, []);

  useEffect(() => {
    const duration = 800;
    const start = performance.now();
    let frame = 0;

    const tick = (time: number) => {
      const progress = Math.min(1, (time - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.floor(target * eased));
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target]);

  return (
    <a
      href="https://github.com"
      target="_blank"
      rel="noreferrer"
      className="badge-pill mt-4 inline-flex border border-black/10 bg-white/80 text-brand-ink"
      onClick={() => trackEvent("github_click", { source: "hero-stars" })}
    >
      ⭐ {display.toLocaleString()} stars
    </a>
  );
}
