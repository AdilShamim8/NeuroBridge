import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

import { enforceRateLimit } from "@/lib/apiSecurity";
import { hashPayload, readJsonFile, writeJsonFile } from "@/lib/serverStore";

type SharedItem = {
  hash: string;
  input: string;
  profile: string;
  adapted: string;
  created_at: string;
};

const sharedCreateSchema = z.object({
  input: z.string().trim().min(1).max(1000),
  profile: z.string().trim().min(1).max(64).optional(),
  adapted: z.string().trim().min(1).max(3000)
});

const hashQuerySchema = z.object({
  hash: z.string().regex(/^[a-f0-9]{64}$/)
});

export async function POST(request: NextRequest) {
  const limited = enforceRateLimit(request, 30);
  if (limited) {
    return limited;
  }

  const rawBody = (await request.json().catch(() => ({}))) as unknown;
  const parsed = sharedCreateSchema.safeParse(rawBody);
  if (!parsed.success) {
    return NextResponse.json({ error: "input and adapted are required" }, { status: 400 });
  }
  const body = parsed.data;

  const input = body.input.slice(0, 1000);
  const adapted = body.adapted.slice(0, 3000);
  const profile = (body.profile || "adhd").toLowerCase();

  const hash = hashPayload(`${input}|${profile}|${adapted}|${Date.now()}`);
  const records = await readJsonFile<Record<string, SharedItem>>("shared.json", {});
  records[hash] = {
    hash,
    input,
    profile,
    adapted,
    created_at: new Date().toISOString()
  };
  await writeJsonFile("shared.json", records);

  return NextResponse.json({ hash, url: `/shared/${hash}` });
}

export async function GET(request: NextRequest) {
  const parsed = hashQuerySchema.safeParse({ hash: request.nextUrl.searchParams.get("hash") || "" });
  if (!parsed.success) {
    return NextResponse.json({ error: "hash is required" }, { status: 400 });
  }
  const hash = parsed.data.hash;

  const records = await readJsonFile<Record<string, SharedItem>>("shared.json", {});
  const found = records[hash];
  if (!found) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }

  return NextResponse.json(found);
}
