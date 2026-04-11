"use client";

import { useState, useRef, useEffect } from "react";
import { CALIFORNIA_COLLEGES } from "@/state-atlas/californiaColleges";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const sorted = [...CALIFORNIA_COLLEGES]
  .filter((c) => c.logoStacked)
  .sort((a, b) => a.name.localeCompare(b.name));

type Props = {
  value: string;
  onChange: (collegeId: string) => void;
};

export default function CollegeSelect({ value, onChange }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [focused, setFocused] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const selected = CALIFORNIA_COLLEGES.find((c) => c.id === value);
  const filtered = query
    ? sorted.filter(
        (c) =>
          c.name.toLowerCase().includes(query.toLowerCase()) ||
          c.district.toLowerCase().includes(query.toLowerCase()),
      )
    : sorted;

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setFocused(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <input
        type="text"
        placeholder={selected ? selected.name : "Search for your college..."}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => { setOpen(true); setFocused(true); }}
        onBlur={() => setFocused(false)}
        style={{
          width: "100%",
          height: "52px",
          background: focused ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.04)",
          border: focused
            ? "1px solid rgba(201,168,76,0.6)"
            : "1px solid rgba(255,255,255,0.12)",
          borderRadius: "8px",
          padding: "0 18px",
          color: selected && !query ? "#ffffff" : query ? "#ffffff" : "rgba(255,255,255,0.4)",
          fontFamily: FONT,
          fontSize: "14px",
          outline: "none",
          boxSizing: "border-box",
          transition: "border-color 0.2s, background 0.2s",
        }}
      />
      {open && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            left: 0,
            right: 0,
            maxHeight: "240px",
            overflowY: "auto",
            background: "#162035",
            border: "1px solid rgba(201,168,76,0.4)",
            borderRadius: "8px",
            zIndex: 50,
          }}
        >
          {filtered.length === 0 ? (
            <div
              style={{
                padding: "14px 18px",
                color: "rgba(255,255,255,0.4)",
                fontSize: "13px",
                fontFamily: FONT,
              }}
            >
              No colleges found
            </div>
          ) : (
            filtered.map((college) => (
              <button
                key={college.id}
                type="button"
                onClick={() => {
                  onChange(college.id);
                  setQuery("");
                  setOpen(false);
                }}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "12px 18px",
                  background:
                    college.id === value
                      ? "rgba(201,168,76,0.1)"
                      : "transparent",
                  border: "none",
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                  cursor: "pointer",
                  fontFamily: FONT,
                  transition: "background 0.1s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.background = "rgba(255,255,255,0.06)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.background =
                    college.id === value
                      ? "rgba(201,168,76,0.1)"
                      : "transparent")
                }
              >
                <div style={{ color: "#ffffff", fontSize: "15px", fontWeight: 500 }}>
                  {college.name}
                </div>
                <div
                  style={{
                    color: "rgba(255,255,255,0.5)",
                    fontSize: "12px",
                    marginTop: "3px",
                  }}
                >
                  {college.district}
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
