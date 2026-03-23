import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ProfileQuiz",
  description: "Take a private, no-pressure 15-question quiz to find your profile.",
  alternates: { canonical: "/quiz" },
  openGraph: {
    title: "NeuroBridge ProfileQuiz",
    description: "Find your cognitive profile in under two minutes.",
    images: ["/api/og?profile=Quiz"]
  }
};

export default function QuizLayout({ children }: { children: React.ReactNode }) {
  return children;
}
