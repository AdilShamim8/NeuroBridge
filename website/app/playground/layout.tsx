import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Playground",
  description: "Paste AI output and adapt it live with NeuroBridge profiles.",
  alternates: { canonical: "/playground" },
  openGraph: {
    title: "NeuroBridge Playground",
    description: "Live adaptation demo for profile-aware AI communication.",
    images: ["/api/og?profile=Playground"]
  }
};

export default function PlaygroundLayout({ children }: { children: React.ReactNode }) {
  return children;
}
