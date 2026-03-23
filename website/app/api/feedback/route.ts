import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

import { enforceRateLimit } from "@/lib/apiSecurity";
import { readJsonFile, writeJsonFile } from "@/lib/serverStore";

const feedbackSchema = z.object({
  page: z.string().trim().max(200).optional(),
  profile: z.string().trim().max(64).optional(),
  rating: z.enum(["neutral", "happy", "love", "yes", "no"]),
  message: z.string().max(1000).optional(),
  created_at: z.string().datetime().optional()
});

export async function POST(request: NextRequest) {
  const limited = enforceRateLimit(request, 30);
  if (limited) {
    return limited;
  }

  const rawBody = (await request.json().catch(() => ({}))) as unknown;
  const parsed = feedbackSchema.safeParse(rawBody);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid request payload" }, { status: 400 });
  }
  const body = parsed.data;

  const item = {
    page: body.page || "unknown",
    profile: body.profile || "unknown",
    rating: body.rating,
    message: (body.message || "").slice(0, 1000),
    created_at: body.created_at || new Date().toISOString()
  };

  const feedback = await readJsonFile<Array<typeof item>>("feedback.json", []);
  feedback.push(item);
  await writeJsonFile("feedback.json", feedback);

  return NextResponse.json({ ok: true });
}
