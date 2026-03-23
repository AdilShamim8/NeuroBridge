import { NextRequest, NextResponse } from "next/server";

const limiter = new Map<string, { count: number; resetAt: number }>();

export function getClientIp(req: NextRequest): string {
  const forwarded = req.headers.get("x-forwarded-for");
  if (forwarded) {
    return forwarded.split(",")[0]?.trim() || "unknown";
  }
  return "unknown";
}

export function enforceRateLimit(req: NextRequest, maxPerMinute = 30): NextResponse | null {
  const ip = getClientIp(req);
  const now = Date.now();
  const current = limiter.get(ip);

  if (!current || now > current.resetAt) {
    limiter.set(ip, { count: 1, resetAt: now + 60_000 });
    return null;
  }

  if (current.count >= maxPerMinute) {
    return NextResponse.json({ error: "Rate limit exceeded. Try again in a minute." }, { status: 429 });
  }

  current.count += 1;
  return null;
}
