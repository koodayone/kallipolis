import type { StorageAdapter } from "./types";

export async function getStorage(): Promise<StorageAdapter> {
  if (process.env.NODE_ENV === "development") {
    const { JsonFileStorage } = await import("./storage-json");
    return new JsonFileStorage();
  }
  const { KVStorage } = await import("./storage-kv");
  return new KVStorage();
}
