"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const inputStyle: React.CSSProperties = {
  width: "100%",
  height: "52px",
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: "8px",
  padding: "0 18px",
  color: "#ffffff",
  fontFamily: FONT,
  fontSize: "14px",
  outline: "none",
  boxSizing: "border-box",
  transition: "border-color 0.2s, background 0.2s",
};

function handleFocus(e: React.FocusEvent<HTMLInputElement>) {
  e.currentTarget.style.borderColor = "rgba(201,168,76,0.6)";
  e.currentTarget.style.background = "rgba(255,255,255,0.06)";
}
function handleBlur(e: React.FocusEvent<HTMLInputElement>) {
  e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
  e.currentTarget.style.background = "rgba(255,255,255,0.04)";
}

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
      {/* Logotype */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "64px" }}>
        <img
          src="/kallipolis-logo.png"
          alt="Kallipolis"
          style={{ height: "56px", width: "auto", objectFit: "contain" }}
        />
        <span
          style={{
            fontFamily: "var(--font-days-one), sans-serif",
            fontSize: "34px",
            fontWeight: 400,
            letterSpacing: "0.04em",
            color: "#ffffff",
            lineHeight: 1,
          }}
        >
          Kallipolis
        </span>
      </div>

      {/* Card */}
      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: "16px",
          padding: "32px 28px",
        }}
      >
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={inputStyle}
            onFocus={handleFocus}
            onBlur={handleBlur}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={inputStyle}
            onFocus={handleFocus}
            onBlur={handleBlur}
          />

          {error && (
            <span style={{ color: "#e55", fontSize: "13px", fontFamily: FONT }}>
              {error}
            </span>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              height: "52px",
              marginTop: "8px",
              background: loading ? "rgba(201,168,76,0.5)" : "#c9a84c",
              color: "#0f1f3d",
              border: "none",
              borderRadius: "8px",
              fontFamily: FONT,
              fontSize: "15px",
              fontWeight: 600,
              letterSpacing: "0.02em",
              cursor: loading ? "default" : "pointer",
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = "#d4b65c"; }}
            onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background = "#c9a84c"; }}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <div style={{ textAlign: "center", marginTop: "12px" }}>
            <Link
              href="/register"
              style={{
                color: "rgba(255,255,255,0.45)",
                fontSize: "13px",
                fontFamily: FONT,
                textDecoration: "none",
                transition: "color 0.15s",
              }}
              onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#ffffff")}
              onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.45)")}
            >
              Create an account
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
