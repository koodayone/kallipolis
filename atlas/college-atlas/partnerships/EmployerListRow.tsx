"use client";

/**
 * One employer in a searchable directory rail — shared by the report's
 * Employers lens and the dashboard's Employers state so the two stay in
 * lockstep. Collapsed: name + "NAICS <code> · <industry title>". Selected:
 * the website, description, and SOC role chips inline-expand. The NAICS code
 * is mono (a formal identifier), the industry title brighter sans (the concept)
 * — the pairing teaches the crosswalk.
 */

import React from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { hexA } from "@/college-atlas/partnerships/chartKit";
import { ROLE_LABEL } from "@/college-atlas/partnerships/svampLabels";
import type { ApiSvampEmployer } from "@/college-atlas/partnerships/api";

export default function EmployerListRow({
  emp, selected, hovered, onSelect, onHover, accent, rowRef,
}: {
  emp: ApiSvampEmployer;
  selected: boolean;
  hovered: boolean;
  onSelect: () => void;
  onHover: (on: boolean) => void;
  accent: string;
  rowRef?: (el: HTMLButtonElement | null) => void;
}) {
  return (
    <button
      ref={rowRef}
      onClick={onSelect}
      onMouseEnter={() => onHover(true)}
      onMouseLeave={() => onHover(false)}
      style={{ display: "flex", alignItems: "stretch", gap: 12, width: "100%", textAlign: "left", padding: "12px 14px", border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)", cursor: "pointer", background: selected ? hexA(accent, 0.1) : hovered ? "rgba(255,255,255,0.04)" : "transparent", transition: "background .12s" }}
    >
      <div style={{ width: 3, borderRadius: 2, background: accent, opacity: selected ? 1 : 0.7, flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: FONT, fontSize: 13.5, fontWeight: 600, color: "#ffffff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{emp.name}</div>
        {/* NAICS code (mono identifier) → industry title (brighter sans concept);
            truncates collapsed, wraps full when selected. */}
        <div style={{ fontSize: 11, marginTop: 3, lineHeight: 1.45, whiteSpace: selected ? "normal" : "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {emp.naics4 && <span style={{ fontFamily: MONO, color: "rgba(255,255,255,0.4)" }}>NAICS {emp.naics4}</span>}
          {emp.naics4 && emp.naics_title && <span style={{ color: "rgba(255,255,255,0.28)" }}> · </span>}
          {emp.naics_title && <span style={{ fontFamily: FONT, color: "rgba(255,255,255,0.62)" }}>{emp.naics_title}</span>}
        </div>
        {selected && (
          <div style={{ marginTop: 10 }}>
            {emp.website && (
              <a href={emp.website} target="_blank" rel="noreferrer" onClick={(ev) => ev.stopPropagation()} style={{ fontFamily: MONO, fontSize: 11, color: accent }}>
                {emp.website.replace(/^https?:\/\//, "").replace(/\/$/, "")} ↗
              </a>
            )}
            {emp.description && (
              <div style={{ fontFamily: FONT, fontSize: 12.5, color: "rgba(255,255,255,0.7)", lineHeight: 1.55, marginTop: emp.website ? 7 : 0, whiteSpace: "normal" }}>{emp.description}</div>
            )}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 9 }}>
              {/* Top 3 roles (backend orders by OES industry share) — kept short
                  so the panel doesn't saturate; the rest are summarized as +N. */}
              {emp.socs.slice(0, 3).map((s) => (
                <span key={s} style={{ fontFamily: FONT, fontSize: 11, color: "#cfe0f0", background: hexA(accent, 0.14), border: `1px solid ${hexA(accent, 0.3)}`, borderRadius: 6, padding: "2px 8px" }}>
                  {ROLE_LABEL[s] ?? emp.soc_titles?.[s] ?? s}
                </span>
              ))}
              {emp.socs.length > 3 && (
                <span style={{ fontFamily: FONT, fontSize: 11, color: "rgba(255,255,255,0.4)", padding: "2px 4px" }}>
                  +{emp.socs.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </button>
  );
}
