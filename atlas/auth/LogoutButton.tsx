"use client";

import { useRouter } from "next/navigation";

export default function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
  }

  return (
    <button
      onClick={handleLogout}
      style={{
        background: "none",
        border: "none",
        cursor: "pointer",
        padding: "6px 0",
        fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
        fontSize: "11px",
        fontWeight: 500,
        letterSpacing: "0.12em",
        textTransform: "uppercase" as const,
        color: "rgba(255,255,255,0.5)",
        transition: "color 0.15s",
      }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#ffffff")}
      onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.5)")}
    >
      Log out
    </button>
  );
}
