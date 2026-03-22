"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: "6px",
  padding: "12px 16px",
  color: "#ffffff",
  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
  fontSize: "14px",
  outline: "none",
  boxSizing: "border-box",
};

export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Login failed");
        return;
      }
      router.push(`/${data.collegeId}`);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "#041e54",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 24px",
        overflow: "auto",
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "48px" }}>
        <img
          src="/kallipolis-logo.png"
          alt="Kallipolis"
          style={{ height: "36px", width: "auto", objectFit: "contain" }}
        />
        <span
          style={{
            fontFamily: "var(--font-days-one), sans-serif",
            fontSize: "22px",
            color: "#ffffff",
            lineHeight: 1,
          }}
        >
          Kallipolis
        </span>
      </div>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px", width: "100%", maxWidth: "400px" }}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={inputStyle}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={inputStyle}
        />

        {error && (
          <span style={{ color: "#e55", fontSize: "13px", fontFamily: "var(--font-inter), Inter, system-ui, sans-serif" }}>
            {error}
          </span>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "12px 24px",
            background: loading ? "rgba(201,168,76,0.5)" : "#c9a84c",
            color: "#111827",
            border: "none",
            borderRadius: "6px",
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "14px",
            fontWeight: 600,
            cursor: loading ? "default" : "pointer",
            transition: "opacity 0.15s",
          }}
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <div style={{ textAlign: "center", marginTop: "8px" }}>
          <Link
            href="/register"
            style={{
              color: "rgba(255,255,255,0.5)",
              fontSize: "13px",
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              textDecoration: "none",
              transition: "color 0.15s",
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#ffffff")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.5)")}
          >
            Create an account
          </Link>
        </div>
      </form>
    </div>
  );
}
