import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const dataDir = path.join(process.cwd(), ".data");

async function ensureDir(): Promise<void> {
  await fs.mkdir(dataDir, { recursive: true });
}

export async function readJsonFile<T>(fileName: string, fallback: T): Promise<T> {
  await ensureDir();
  const filePath = path.join(dataDir, fileName);
  try {
    const content = await fs.readFile(filePath, "utf8");
    return JSON.parse(content) as T;
  } catch {
    return fallback;
  }
}

export async function writeJsonFile<T>(fileName: string, value: T): Promise<void> {
  await ensureDir();
  const filePath = path.join(dataDir, fileName);
  await fs.writeFile(filePath, JSON.stringify(value, null, 2), "utf8");
}

export function hashPayload(value: string, size = 8): string {
  return crypto.createHash("sha256").update(value).digest("hex").slice(0, size);
}
