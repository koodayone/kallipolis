import { NextRequest, NextResponse } from "next/server";
import { verifyPassword } from "@/lib/auth/crypto";
import { createSessionToken, buildSessionCookie } from "@/lib/auth/jwt";
import { getStorage } from "@/lib/auth/storage";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { email, password } = body;

  if (!email || !password) {
    return NextResponse.json(
      { error: "Email and password are required" },
      { status: 400 },
    );
  }

  const storage = await getStorage();
  const user = await storage.getUserByEmail(email);

  if (!user) {
    return NextResponse.json(
      { error: "Invalid email or password" },
      { status: 401 },
    );
  }

  const valid = await verifyPassword(password, user.passwordHash, user.salt);
  if (!valid) {
    return NextResponse.json(
      { error: "Invalid email or password" },
      { status: 401 },
    );
  }

  const token = await createSessionToken({
    sub: user.id,
    email: user.email,
    name: user.name,
    collegeId: user.collegeId,
  });

  const response = NextResponse.json({ collegeId: user.collegeId });
  response.headers.set("Set-Cookie", buildSessionCookie(token));
  return response;
}
