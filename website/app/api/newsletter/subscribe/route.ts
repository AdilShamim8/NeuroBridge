import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

import { enforceRateLimit } from "@/lib/apiSecurity";
import { readJsonFile, writeJsonFile } from "@/lib/serverStore";

const newsletterSchema = z.object({
  email: z.string().trim().email().max(254)
});

export async function POST(request: NextRequest) {
  const limited = enforceRateLimit(request, 30);
  if (limited) {
    return limited;
  }

  const rawBody = (await request.json().catch(() => ({}))) as unknown;
  const parsed = newsletterSchema.safeParse(rawBody);
  if (!parsed.success) {
    return NextResponse.json({ error: "Valid email is required" }, { status: 400 });
  }
  const email = parsed.data.email.toLowerCase();

  const subscribers = await readJsonFile<Array<{ email: string; status: string; created_at: string }>>(
    "newsletter.json",
    []
  );

  if (!subscribers.some((entry) => entry.email === email)) {
    subscribers.push({
      email,
      status: "pending_confirmation",
      created_at: new Date().toISOString()
    });
    await writeJsonFile("newsletter.json", subscribers);
  }

  const provider = process.env.BUTTONDOWN_API_KEY || process.env.RESEND_API_KEY;
  return NextResponse.json({
    ok: true,
    providerConfigured: Boolean(provider),
    message:
      "Confirmation email queued. Once confirmed, you'll receive: Welcome to NeuroBridge - here's what's coming in v0.2.0"
  });
}
