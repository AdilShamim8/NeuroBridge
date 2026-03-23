import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Docs",
  description: "Product and API documentation for NeuroBridge.",
  alternates: { canonical: "/docs" }
};

export default async function DocsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
