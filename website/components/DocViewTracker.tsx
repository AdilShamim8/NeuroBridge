"use client";

import { useEffect } from "react";

import { trackEvent } from "@/lib/analytics";

type DocViewTrackerProps = {
  slug: string;
};

export function DocViewTracker({ slug }: DocViewTrackerProps) {
  useEffect(() => {
    if (!slug) return;
    trackEvent("doc_page_viewed", { slug });
  }, [slug]);

  return null;
}
