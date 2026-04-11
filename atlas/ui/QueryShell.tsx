"use client";

import { useState, useEffect, useCallback, useRef, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import RisingSun from "@/ui/RisingSun";

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
  placeholder: string;
  examples: string[];
  queryFn: (query: string, college: string) => Promise<{ items: T[]; message: string }>;
  loadInitialData: () => Promise<void>;
  renderInitialContent: () => ReactNode;
  renderResultsContent: (results: T[]) => ReactNode;
  onQueryStart?: () => void;
  onReset?: () => void;
  rootRef?: React.RefObject<HTMLDivElement | null>;
};

export default function QueryShell<T>({
  school, onBack, placeholder, examples,
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
  const [helpOpen, setHelpOpen] = useState(false);
  const [helpClicked, setHelpClicked] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const helpRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadInitialData()
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => { if (data?.user?.name) setUserName(data.user.name.split(" ")[0]); })
      .catch(() => {});
  }, []);

  // Click-outside to close help panel
  useEffect(() => {
    if (!helpOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (helpRef.current && !helpRef.current.contains(e.target as Node)) {
        setHelpOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [helpOpen]);

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

  const handleExample = useCallback((text: string) => {
    setHelpOpen(false);
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

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    if (val.length > 0) setHelpOpen(false);
  }, []);

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
      <AtlasHeader
        school={school}
        onBack={onBack}
        title={school.name}
        rightSlot={<KallipolisBrand />}
      />
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
              <div ref={helpRef} style={{ width: "100%", position: "relative" }}>
                <div style={{ position: "relative" }}>
                  <input ref={inputRef} type="text" value={query}
                    onChange={handleInputChange}
                    onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                    placeholder={placeholder}
                    style={{
                      width: "100%", padding: "18px 48px 18px 24px", fontFamily: FONT, fontSize: "15px",
                      color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.10)",
                      borderRadius: helpOpen ? "16px 16px 0 0" : "16px",
                      outline: "none", transition: "border-color 0.2s, box-shadow 0.2s, border-radius 0.15s",
                    }}
                    onFocus={onInputFocus}
                    onBlur={onInputBlur}
                  />
                  <motion.button
                    onClick={() => { setHelpOpen((prev) => !prev); setHelpClicked(true); }}
                    style={{
                      position: "absolute", right: "16px", top: "50%", transform: "translateY(-50%)",
                      background: "none", border: "none", cursor: "pointer", padding: "4px",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      animation: !helpClicked && !helpOpen ? "helpGlow 2.5s ease-in-out infinite" : "none",
                    }}
                    aria-label="Show example queries"
                  >
                    {!helpClicked && (
                      <style>{`
                        @keyframes helpGlow {
                          0%, 100% { filter: drop-shadow(0 0 2px ${school.brandColorLight}30); }
                          50% { filter: drop-shadow(0 0 6px ${school.brandColorLight}70); }
                        }
                      `}</style>
                    )}
                    <motion.svg width="20" height="20" viewBox="0 0 16 16" fill="none"
                      initial={{ opacity: 0.4 }}
                      animate={{ opacity: helpClicked ? 0.55 : 1 }}
                      transition={{ duration: 1.5, ease: "easeOut" }}
                      whileHover={{ opacity: 0.85 }}
                    >
                      <circle cx="8" cy="8" r="7" strokeWidth="1.2"
                        stroke={helpOpen ? school.brandColorLight : "rgba(255,255,255,0.55)"}
                        style={{ transition: "stroke 1.8s ease-in-out" }}
                      />
                      <text x="8" y="11.5" textAnchor="middle"
                        fontSize="10" fontWeight="600" fontFamily={FONT}
                        fill={helpOpen ? school.brandColorLight : "rgba(255,255,255,0.55)"}
                        style={{ transition: "fill 1.8s ease-in-out" }}
                      >?</text>
                      {!helpOpen && (
                        <>
                          <motion.circle cx="8" cy="8" r="7" strokeWidth="1.2" fill="none"
                            stroke={school.brandColorLight}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: [0, 0.6, 0] }}
                            transition={{ duration: 2.5, ease: "easeInOut", times: [0, 0.4, 1] }}
                          />
                          <motion.text x="8" y="11.5" textAnchor="middle"
                            fontSize="10" fontWeight="600" fontFamily={FONT}
                            fill={school.brandColorLight}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: [0, 0.6, 0] }}
                            transition={{ duration: 2.5, ease: "easeInOut", times: [0, 0.4, 1] }}
                          >?</motion.text>
                        </>
                      )}
                    </motion.svg>
                  </motion.button>
                </div>

                <AnimatePresence>
                  {helpOpen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                      style={{ overflow: "hidden" }}
                    >
                      <div style={{
                        background: "rgba(255,255,255,0.04)",
                        border: "1px solid rgba(255,255,255,0.10)",
                        borderTop: "none",
                        borderRadius: "0 0 16px 16px",
                      }}>
                        <div style={{
                          padding: "12px 24px 4px",
                          fontFamily: FONT, fontSize: "10px", fontWeight: 600,
                          letterSpacing: "0.1em", textTransform: "uppercase",
                          color: school.brandColorLight, opacity: 0.5,
                        }}>
                          Try asking...
                        </div>
                        {examples.map((example, idx) => (
                          <button key={example}
                            onClick={() => handleExample(example)}
                            style={{
                              display: "block", width: "100%", textAlign: "left",
                              padding: "12px 24px", fontFamily: FONT, fontSize: "13px",
                              color: "rgba(255,255,255,0.45)", background: "transparent",
                              border: "none",
                              borderBottom: idx < examples.length - 1 ? "1px solid rgba(255,255,255,0.06)" : "none",
                              cursor: "pointer", transition: "color 0.15s, background 0.15s",
                            }}
                            onMouseEnter={(e) => { const el = e.currentTarget; el.style.color = "rgba(255,255,255,0.7)"; el.style.background = "rgba(255,255,255,0.03)"; }}
                            onMouseLeave={(e) => { const el = e.currentTarget; el.style.color = "rgba(255,255,255,0.45)"; el.style.background = "transparent"; }}
                          >
                            {example}
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
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
