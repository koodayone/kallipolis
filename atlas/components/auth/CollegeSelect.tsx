"use client";

import { useState, useRef, useEffect } from "react";
import { CALIFORNIA_COLLEGES } from "@/lib/californiaColleges";

const sorted = [...CALIFORNIA_COLLEGES]
  .filter((c) => c.logoStacked) // only colleges with atlas support
  .sort((a, b) => a.name.localeCompare(b.name));

type Props = {
  value: string;
  onChange: (collegeId: string) => void;
};

export default function CollegeSelect({ value, onChange }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
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
        onFocus={() => setOpen(true)}
        style={{
          width: "100%",
          background: "rgba(255,255,255,0.05)",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: "6px",
          padding: "12px 16px",
          color: selected && !query ? "#ffffff" : query ? "#ffffff" : "rgba(255,255,255,0.4)",
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "14px",
          outline: "none",
          boxSizing: "border-box",
        }}
      />
      {open && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            maxHeight: "240px",
            overflowY: "auto",
            background: "#141a22",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            zIndex: 50,
          }}
        >
          {filtered.length === 0 ? (
            <div
              style={{
                padding: "12px 16px",
                color: "rgba(255,255,255,0.4)",
                fontSize: "13px",
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
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
                  padding: "10px 16px",
                  background:
                    college.id === value
                      ? "rgba(201,168,76,0.12)"
                      : "transparent",
                  border: "none",
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                  cursor: "pointer",
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  transition: "background 0.1s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.background = "rgba(255,255,255,0.06)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.background =
                    college.id === value
                      ? "rgba(201,168,76,0.12)"
                      : "transparent")
                }
              >
                <div style={{ color: "#ffffff", fontSize: "13px", fontWeight: 500 }}>
                  {college.name}
                </div>
                <div
                  style={{
                    color: "rgba(255,255,255,0.4)",
                    fontSize: "11px",
                    marginTop: "2px",
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
