import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { verifySessionToken, COOKIE_NAME } from "@/auth/jwt";

export default async function RootPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(COOKIE_NAME)?.value;

  if (!token) redirect("/login");

  const payload = await verifySessionToken(token);
  if (!payload) redirect("/login");

  redirect(`/${payload.collegeId}`);
}
