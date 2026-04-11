import { readFile, writeFile, mkdir } from "fs/promises";
import { join, dirname } from "path";
import type { AuthUser, StorageAdapter } from "./types";

const DATA_DIR = join(process.cwd(), ".data");
const USERS_FILE = join(DATA_DIR, "users.json");

async function readUsers(): Promise<Record<string, AuthUser>> {
  try {
    const data = await readFile(USERS_FILE, "utf8");
    return JSON.parse(data);
  } catch {
    return {};
  }
}

async function writeUsers(users: Record<string, AuthUser>): Promise<void> {
  await mkdir(dirname(USERS_FILE), { recursive: true });
  await writeFile(USERS_FILE, JSON.stringify(users, null, 2), "utf8");
}

export class JsonFileStorage implements StorageAdapter {
  async getUserByEmail(email: string): Promise<AuthUser | null> {
    const users = await readUsers();
    return users[email.toLowerCase()] ?? null;
  }

  async createUser(user: AuthUser): Promise<void> {
    const users = await readUsers();
    users[user.email.toLowerCase()] = user;
    await writeUsers(users);
  }
}
