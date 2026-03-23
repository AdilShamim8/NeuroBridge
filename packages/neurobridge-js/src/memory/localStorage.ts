import { ProfileConfig } from "../types";

const PROFILE_KEY_PREFIX = "neurobridge:profile:";

export class LocalStorageMemory {
  public saveProfile(userId: string, profile: ProfileConfig): void {
    if (typeof window === "undefined" || !window.localStorage) {
      return;
    }
    window.localStorage.setItem(`${PROFILE_KEY_PREFIX}${userId}`, JSON.stringify(profile));
  }

  public loadProfile(userId: string): ProfileConfig | null {
    if (typeof window === "undefined" || !window.localStorage) {
      return null;
    }
    const raw = window.localStorage.getItem(`${PROFILE_KEY_PREFIX}${userId}`);
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as ProfileConfig;
    } catch {
      return null;
    }
  }
}
