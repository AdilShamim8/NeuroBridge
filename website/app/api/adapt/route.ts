import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

import { enforceRateLimit } from "@/lib/apiSecurity";

const adaptSchema = z.object({
  text: z.string().trim().min(1).max(50_000),
  profile: z
    .enum(["adhd", "autism", "dyslexia", "anxiety", "dyscalculia", "custom"])
    .optional()
    .default("adhd"),
  output_format: z.enum(["markdown", "html", "plain", "json", "tts"]).optional().default("markdown"),
  user_id: z.string().trim().regex(/^[A-Za-z0-9_-]{1,128}$/).optional()
});

function mockAdapt(text: string, profile: string) {
  const softened = text
    .replace(/\bASAP\b/gi, "when you have time")
    .replace(/\bimmediately\b/gi, "when ready")
    .replace(/\bcritical\b/gi, "important");

  const chunks = softened
    .split(/(?<=[.!?])\s+/)
    .reduce<string[]>((acc, sentence, index) => {
      const slot = Math.floor(index / 2);
      if (!acc[slot]) {
        acc[slot] = sentence;
      } else {
        acc[slot] = `${acc[slot]} ${sentence}`;
      }
      return acc;
    }, [])
    .join("\n\n");

  return {
    raw_text: text,
    adapted_text: chunks,
    modules_run: ["Chunker", profile === "anxiety" ? "UrgencyFilter" : "ToneRewriter"],
    processing_ms: 6,
    profile
  };
}

export async function POST(req: NextRequest) {
  const limited = enforceRateLimit(req, 30);
  if (limited) {
    return limited;
  }

  const rawBody = (await req.json().catch(() => ({}))) as unknown;
  const parsed = adaptSchema.safeParse(rawBody);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid request payload" }, { status: 400 });
  }
  const payload = parsed.data;
  const text = payload.text;
  const profile = payload.profile.toLowerCase();

  const backendUrl = process.env.NEUROBRIDGE_API_URL;
  if (!backendUrl) {
    return NextResponse.json(mockAdapt(text, profile));
  }

  try {
    const response = await fetch(`${backendUrl.replace(/\/$/, "")}/api/v1/adapt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        profile,
        output_format: payload.output_format,
        user_id: payload.user_id
      })
    });

    const result = await response.json();
    if (!response.ok) {
      return NextResponse.json({ error: result?.detail || "Backend adaptation failed" }, { status: response.status });
    }
    return NextResponse.json(result);
  } catch {
    return NextResponse.json({ error: "Unable to reach NeuroBridge API." }, { status: 502 });
  }
}
