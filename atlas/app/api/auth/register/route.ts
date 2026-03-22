import { NextRequest, NextResponse } from "next/server";
import { hashPassword } from "@/lib/auth/crypto";
import { createSessionToken, buildSessionCookie } from "@/lib/auth/jwt";
import { getStorage } from "@/lib/auth/storage";
import { CALIFORNIA_COLLEGES } from "@/lib/californiaColleges";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { name, email, password, collegeId } = body;

  if (!name || !email || !password || !collegeId) {
    return NextResponse.json(
      { error: "All fields are required" },
      { status: 400 },
    );
  }

  if (password.length < 8) {
    return NextResponse.json(
      { error: "Password must be at least 8 characters" },
      { status: 400 },
    );
  }

  if (!CALIFORNIA_COLLEGES.some((c) => c.id === collegeId)) {
    return NextResponse.json(
      { error: "Invalid college selection" },
      { status: 400 },
    );
  }

  const storage = await getStorage();
  const existing = await storage.getUserByEmail(email);
  if (existing) {
    return NextResponse.json(
      { error: "An account with this email already exists" },
      { status: 409 },
    );
  }

  const { hash, salt } = await hashPassword(password);
  const user = {
    id: crypto.randomUUID(),
    name: name.trim(),
    email: email.toLowerCase().trim(),
    passwordHash: hash,
    salt,
    collegeId,
    createdAt: new Date().toISOString(),
  };

  await storage.createUser(user);

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
