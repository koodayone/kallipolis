import type { AuthUser, StorageAdapter } from "./types";

// Minimal KV interface — matches Cloudflare KVNamespace subset
interface KV {
  get(key: string, type: "text"): Promise<string | null>;
  put(key: string, value: string): Promise<void>;
}

// Cloudflare KV binding — available via getRequestContext() in production
function getKV(): KV {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const env = (globalThis as any).process?.env?.ATLAS_AUTH_KV;
  if (env) return env;
  throw new Error("ATLAS_AUTH_KV binding not available");
}

export class KVStorage implements StorageAdapter {
  async getUserByEmail(email: string): Promise<AuthUser | null> {
    const kv = getKV();
    const data = await kv.get(`user:${email.toLowerCase()}`, "text");
    if (!data) return null;
    return JSON.parse(data) as AuthUser;
  }

  async createUser(user: AuthUser): Promise<void> {
    const kv = getKV();
    await kv.put(
      `user:${user.email.toLowerCase()}`,
      JSON.stringify(user),
    );
  }
}
