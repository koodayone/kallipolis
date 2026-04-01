"use client";

import { useState, useEffect, useCallback, useRef, type ReactNode } from "react";
import { motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import LeafHeader from "@/components/ui/LeafHeader";
import RisingSun from "@/components/ui/RisingSun";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

export function findScrollParent(el: HTMLElement | null): HTMLElement | null {
  while (el) {
    if (el.scrollHeight > el.clientHeight && getComputedStyle(el).overflowY !== "visible") return el;
    el = el.parentElement;
  }
  return null;
}

export type QueryShellProps<T> = {
  school: SchoolConfig;
  onBack: () => void;
  parentShape: "dodecahedron" | "cube" | "tetrahedron";
  placeholder: string;
  suggestions: string[];
  queryFn: (query: string, college: string) => Promise<{ items: T[]; message: string }>;
  loadInitialData: () => Promise<void>;
  renderInitialContent: () => ReactNode;
  renderResultsContent: (results: T[]) => ReactNode;
  onQueryStart?: () => void;
  onReset?: () => void;
  rootRef?: React.RefObject<HTMLDivElement>;
};

export default function QueryShell<T>({
  school, onBack, parentShape, placeholder, suggestions,
  queryFn, loadInitialData, renderInitialContent, renderResultsContent,
  onQueryStart, onReset, rootRef,
}: QueryShellProps<T>) {
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState<T[]>([]);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryMessage, setQueryMessage] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadInitialData()
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => { if (data?.user?.name) setUserName(data.user.name.split(" ")[0]); })
      .catch(() => {});
  }, []);

  const executeQuery = useCallback(async (queryText: string) => {
    if (!queryText.trim()) return;
    onQueryStart?.();
    setSubmitted(true);
    setQueryLoading(true);
    setQueryMessage(null);
    try {
      const resp = await queryFn(queryText, school.name);
      setResults(resp.items);
      setQueryMessage(resp.message);
    } catch (e: unknown) {
      setResults([]);
      setQueryMessage(e instanceof Error ? e.message : "Something went wrong. Please try again.");
    } finally {
      setQueryLoading(false);
    }
  }, [queryFn, school.name, onQueryStart]);

  const handleSubmit = useCallback(() => {
    executeQuery(query);
  }, [executeQuery, query]);

  const handleChip = useCallback((text: string) => {
    setQuery(text);
    executeQuery(text);
  }, [executeQuery]);

  const handleReset = useCallback(() => {
    setQuery("");
    setSubmitted(false);
    setResults([]);
    setQueryMessage(null);
    onReset?.();
    setTimeout(() => inputRef.current?.focus(), 100);
  }, [onReset]);

  const onInputFocus = useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    e.currentTarget.style.borderColor = `${school.brandColorLight}50`;
    e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`;
  }, [school.brandColorLight]);

  const onInputBlur = useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)";
    e.currentTarget.style.boxShadow = "none";
  }, []);

  return (
    <div ref={rootRef}>
      <LeafHeader school={school} onBack={onBack} parentShape={parentShape} />
      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "32px 40px 80px" }}>
        {error && <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>{error}</p>}
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
            <RisingSun style={{ width: "90px", height: "auto", opacity: 0.4 }} />
          </div>
        )}

        {/* ── Initial State ── */}
        {!submitted && !loading && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
            style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", paddingTop: "40px" }}>
              <RisingSun style={{ width: "90px", height: "auto" }} />
              <h1 style={{ fontFamily: FONT, fontSize: "28px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", textAlign: "center" }}>
                What&apos;s up{userName ? `, ${userName}` : ""}?
              </h1>
              <div style={{ width: "100%" }}>
                <input ref={inputRef} type="text" value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                  placeholder={placeholder}
                  style={{
                    width: "100%", padding: "18px 24px", fontFamily: FONT, fontSize: "15px",
                    color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.10)", borderRadius: "16px",
                    outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                  }}
                  onFocus={onInputFocus}
                  onBlur={onInputBlur}
                />
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", justifyContent: "center" }}>
                {suggestions.map((s) => (
                  <button key={s} onClick={() => handleChip(s)}
                    style={{
                      fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)",
                      background: "transparent", border: `1px solid ${school.brandColorLight}35`,
                      borderRadius: "100px", padding: "8px 18px", cursor: "pointer",
                      transition: "background 0.15s, color 0.15s, border-color 0.15s",
                    }}
                    onMouseEnter={(e) => { const el = e.currentTarget as HTMLElement; el.style.background = `${school.brandColorLight}15`; el.style.borderColor = `${school.brandColorLight}40`; el.style.color = school.brandColorLight; }}
                    onMouseLeave={(e) => { const el = e.currentTarget as HTMLElement; el.style.background = "transparent"; el.style.borderColor = `${school.brandColorLight}35`; el.style.color = "rgba(255,255,255,0.55)"; }}
                  >{s}</button>
                ))}
              </div>
            </div>

            {renderInitialContent()}
          </motion.div>
        )}

        {/* ── Results State ── */}
        {submitted && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <input ref={inputRef} type="text" value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                placeholder={placeholder}
                style={{
                  flex: 1, padding: "14px 20px", fontFamily: FONT, fontSize: "14px",
                  color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.10)", borderRadius: "12px",
                  outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                onFocus={onInputFocus}
                onBlur={onInputBlur}
              />
              <button onClick={handleReset}
                style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", background: "none", border: "none", cursor: "pointer", padding: "8px", transition: "color 0.15s" }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.8)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.4)"; }}
              >Clear</button>
            </div>

            {queryLoading && (
              <div style={{ display: "flex", justifyContent: "center", paddingTop: "40px" }}>
                <RisingSun style={{ width: "64px", height: "auto", opacity: 0.4 }} />
              </div>
            )}

            {!queryLoading && queryMessage && (
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>{queryMessage}</p>
            )}

            {!queryLoading && renderResultsContent(results)}
          </motion.div>
        )}
      </div>
    </div>
  );
}
