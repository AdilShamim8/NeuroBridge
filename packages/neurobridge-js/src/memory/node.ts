// @ts-ignore Runtime Node built-ins; type resolution depends on local Node typings.
import { mkdirSync, readFileSync, writeFileSync } from "fs";
// @ts-ignore Runtime Node built-ins; type resolution depends on local Node typings.
import { dirname } from "path";

import { ProfileConfig } from "../types";

export class NodeFileMemory {
  public constructor(private readonly filePath = ".neurobridge-js-memory.json") {}

  public saveProfile(userId: string, profile: ProfileConfig): void {
    const data = this.readData();
    data[userId] = profile;
    this.writeData(data);
  }

  public loadProfile(userId: string): ProfileConfig | null {
    const data = this.readData();
    return (data[userId] as ProfileConfig | undefined) ?? null;
  }

  private readData(): Record<string, unknown> {
    try {
      const raw = readFileSync(this.filePath, "utf-8");
      return JSON.parse(raw) as Record<string, unknown>;
    } catch {
      return {};
    }
  }

  private writeData(data: Record<string, unknown>): void {
    mkdirSync(dirname(this.filePath), { recursive: true });
    writeFileSync(this.filePath, JSON.stringify(data, null, 2), "utf-8");
  }
}
