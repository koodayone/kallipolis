import { NextResponse } from "next/server";
import { buildLogoutCookie } from "@/auth/jwt";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.headers.set("Set-Cookie", buildLogoutCookie());
  return response;
}
