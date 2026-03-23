import type { Metadata } from "next";
import Script from "next/script";

import { Footer } from "@/components/Footer";
import { Nav } from "@/components/Nav";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://neurobridge.dev"),
  title: {
    default: "NeuroBridge",
    template: "%s | NeuroBridge"
  },
  description: "AI accessibility layer for neurodivergent communication",
  alternates: {
    canonical: "/"
  },
  openGraph: {
    title: "NeuroBridge",
    description: "AI that adapts to cognitive profiles.",
    url: "https://neurobridge.dev",
    siteName: "NeuroBridge",
    images: ["/api/og?profile=NeuroBridge"],
    type: "website"
  },
  twitter: {
    card: "summary_large_image",
    title: "NeuroBridge",
    description: "AI that adapts to cognitive profiles.",
    images: ["/api/og?profile=NeuroBridge"]
  }
};

const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "NeuroBridge",
  url: "https://neurobridge.dev",
  logo: "https://neurobridge.dev/icon.png",
  sameAs: ["https://github.com"],
  description: "Cognitive accessibility middleware for AI output."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://cdn.jsdelivr.net/npm/open-dyslexic@1.0.3/open-dyslexic-regular.min.css"
          rel="stylesheet"
        />
      </head>
      <body>
        <Script
          defer
          data-domain={process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN || "neurobridge.dev"}
          src={process.env.NEXT_PUBLIC_PLAUSIBLE_SRC || "https://plausible.io/js/script.js"}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
        />
        <Nav />
        <main className="mx-auto w-[min(1100px,95vw)] py-8">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
