"use client";

type EventProps = Record<string, string | number | boolean>;

declare global {
  interface Window {
    plausible?: (eventName: string, options?: { props?: EventProps }) => void;
  }
}

export function trackEvent(eventName: string, props?: EventProps): void {
  if (typeof window === "undefined") {
    return;
  }
  if (typeof window.plausible !== "function") {
    return;
  }
  window.plausible(eventName, props ? { props } : undefined);
}
