/**
 * Brand-color picks API. Stores per-college user-chosen hex values in
 * atlas/public/brand-audit/picks.json so the /brand-audit page can be
 * an interactive picker — user clicks a swatch, the choice persists,
 * and a follow-up tool reads picks.json to promote selections into
 * COLOR_OVERRIDES.
 *
 * Local-dev only: this route writes to the working copy, so it works
 * during `next dev` against a checkout. It is not part of the static
 * export.
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const PICKS_FILE = path.resolve(
  process.cwd(),
  "public",
  "brand-audit",
  "picks.json",
);

type PicksFile = {
  version: 1;
  updated_at: string;
  picks: Record<string, { hex: string; source: string; updated_at: string }>;
};

async function readPicks(): Promise<PicksFile> {
  try {
    const raw = await fs.readFile(PICKS_FILE, "utf-8");
    const parsed = JSON.parse(raw) as PicksFile;
    if (!parsed.picks) parsed.picks = {};
    return parsed;
  } catch {
    return { version: 1, updated_at: new Date().toISOString(), picks: {} };
  }
}

async function writePicks(file: PicksFile): Promise<void> {
  file.updated_at = new Date().toISOString();
  await fs.mkdir(path.dirname(PICKS_FILE), { recursive: true });
  await fs.writeFile(PICKS_FILE, JSON.stringify(file, null, 2), "utf-8");
}

function isValidHex(s: unknown): s is string {
  return typeof s === "string" && /^#?[0-9a-fA-F]{6}$/.test(s.trim());
}

function normHex(s: string): string {
  const t = s.trim();
  return (t.startsWith("#") ? t : `#${t}`).toLowerCase();
}

export async function GET() {
  const file = await readPicks();
  return NextResponse.json(file);
}

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid JSON" }, { status: 400 });
  }
  const { id, hex, source } = (body ?? {}) as {
    id?: string;
    hex?: string;
    source?: string;
  };
  if (!id || !/^[\w-]+$/.test(id)) {
    return NextResponse.json({ error: "missing or invalid id" }, { status: 400 });
  }
  if (!isValidHex(hex)) {
    return NextResponse.json({ error: "invalid hex (need #rrggbb)" }, { status: 400 });
  }
  const file = await readPicks();
  file.picks[id] = {
    hex: normHex(hex),
    source: typeof source === "string" ? source.slice(0, 40) : "manual",
    updated_at: new Date().toISOString(),
  };
  await writePicks(file);
  return NextResponse.json({ ok: true, pick: file.picks[id] });
}

export async function DELETE(req: Request) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");
  if (!id) {
    return NextResponse.json({ error: "missing id" }, { status: 400 });
  }
  const file = await readPicks();
  if (id in file.picks) {
    delete file.picks[id];
    await writePicks(file);
  }
  return NextResponse.json({ ok: true });
}
