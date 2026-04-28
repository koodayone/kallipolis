"use client";

import { useEffect, useMemo, useRef, useState, type RefObject, Fragment } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { SchoolConfig } from "@/config/schoolConfig";
import type { ApiPartnershipOpportunity } from "@/college-atlas/partnerships/api";
import PartnershipRow from "./PartnershipRow";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const UNCLASSIFIED = "Unclassified";

type Props = {
  school: SchoolConfig;
  loading: boolean;
  error: string | null;
  query: string;
  setQuery: (q: string) => void;
  inputRef: RefObject<HTMLInputElement | null>;
  filteredOpportunities: ApiPartnershipOpportunity[];
  savedCountsByEmployer: Record<string, number>;
  onDraft: (opp: ApiPartnershipOpportunity) => void;
};

// The partnerships Build mode is an action directory: scan employers
// grouped by SWP sector, click Draft Partnership on the one you want,
// and the picker takes over from there. No row-level expansion;
// employer context lives in the picker, not in this list.
export default function PartnershipBuildMode({
  school,
  loading,
  error,
  query,
  setQuery,
  inputRef,
  filteredOpportunities,
  savedCountsByEmployer,
  onDraft,
}: Props) {
  // Sector accordion state — local to Build mode. Default-collapsed; the
  // search-content branch auto-expands matching sectors so results are
  // visible without clicking.
  const [expandedSectors, setExpandedSectors] = useState<Set<string>>(new Set());

  const handleSectorToggle = (sector: string) => {
    setExpandedSectors((prev) => {
      const next = new Set(prev);
      if (next.has(sector)) next.delete(sector);
      else next.add(sector);
      return next;
    });
  };

  // When the search query is non-empty, ensure all matching sectors are open
  // so the search results are visible.
  const isSearching = query.trim().length > 0;

  if (error) {
    return (
      <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>
        {error}
      </p>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{ display: "flex", flexDirection: "column", gap: "24px" }}
    >
      {/* Search */}
      <div style={{ width: "100%", position: "relative" }}>
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"
          style={{ position: "absolute", left: "18px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
          <circle cx="7.5" cy="7.5" r="5.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
          <path d="M11.5 11.5L15.5 15.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search employers..."
          style={{
            width: "100%", padding: "18px 24px 18px 48px", fontFamily: FONT, fontSize: "15px",
            color: "#f0eef4", background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.10)", borderRadius: "6px",
            outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
          }}
          onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
          onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
        />
      </div>

      {loading && (
        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", textAlign: "center", padding: "40px 0" }}>
          Loading employers…
        </p>
      )}

      {!loading && (
        <SectorGroupedList
          opportunities={filteredOpportunities}
          school={school}
          expandedSectors={expandedSectors}
          forceAllExpanded={isSearching}
          onSectorToggle={handleSectorToggle}
          savedCountsByEmployer={savedCountsByEmployer}
          onDraft={onDraft}
        />
      )}
    </motion.div>
  );
}

/* ── Sector Grouped List ──────────────────────────────────────────────── */

// Mirrors the employers view's sector-grouping pattern so the institutional
// vocabulary (Doing-What-Matters / SWP sectors and the regional priority
// dot) reads identically across the two surfaces. The row content differs
// (no expansion, single Draft CTA), but the grouping shell is the same.
function SectorGroupedList({
  opportunities, school, expandedSectors, forceAllExpanded,
  onSectorToggle, savedCountsByEmployer, onDraft,
}: {
  opportunities: ApiPartnershipOpportunity[];
  school: SchoolConfig;
  expandedSectors: Set<string>;
  forceAllExpanded: boolean;
  onSectorToggle: (sector: string) => void;
  savedCountsByEmployer: Record<string, number>;
  onDraft: (opp: ApiPartnershipOpportunity) => void;
}) {
  const { sectors, groups, prioritySet } = useMemo(() => {
    const groups: Record<string, ApiPartnershipOpportunity[]> = {};
    const prioritySet = new Set<string>();
    for (const opp of opportunities) {
      const key = opp.swp_sectors[0] ?? UNCLASSIFIED;
      (groups[key] ??= []).push(opp);
      for (const p of opp.priority_sectors_matched) prioritySet.add(p);
    }
    for (const k of Object.keys(groups)) {
      groups[k].sort((a, b) => a.name.localeCompare(b.name));
    }
    const sectors = Object.keys(groups).sort((a, b) => {
      if (a === UNCLASSIFIED) return 1;
      if (b === UNCLASSIFIED) return -1;
      return a.localeCompare(b);
    });
    return { sectors, groups, prioritySet };
  }, [opportunities]);

  if (opportunities.length === 0) {
    return (
      <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
        No employers match that search.
      </p>
    );
  }

  return (
    <div>
      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
        {opportunities.length} {opportunities.length === 1 ? "employer" : "employers"}
      </p>
      <div style={{
        display: "grid", gridTemplateColumns: "24px 1fr auto",
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <span style={{
            fontFamily: FONT, fontSize: "10px", fontWeight: 600,
            letterSpacing: "0.1em", textTransform: "uppercase",
            color: school.brandColorLight, opacity: 0.6,
          }}>
            Sector
          </span>
          {prioritySet.size > 0 && (
            <span style={{ display: "inline-flex", alignItems: "baseline", gap: "5px" }}>
              <span style={{
                width: "5px", height: "5px", borderRadius: "50%",
                background: school.brandColorLight, opacity: 0.7,
                position: "relative", top: "-1px",
              }} />
              <span style={{
                fontFamily: FONT, fontSize: "10px", fontWeight: 500,
                letterSpacing: "0.1em", textTransform: "uppercase",
                color: school.brandColorLight, opacity: 0.4,
              }}>
                Regional priority
              </span>
            </span>
          )}
        </span>
        <span style={{
          fontFamily: FONT, fontSize: "10px", fontWeight: 600,
          letterSpacing: "0.1em", textTransform: "uppercase",
          color: school.brandColorLight, opacity: 0.6,
          textAlign: "right",
        }}>
          Employers
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        {sectors.map((sector, idx) => (
          <SectorGroup
            key={sector}
            sector={sector}
            opportunities={groups[sector]}
            index={idx}
            isOpen={forceAllExpanded || expandedSectors.has(sector)}
            isPriority={prioritySet.has(sector)}
            school={school}
            onToggle={() => onSectorToggle(sector)}
            savedCountsByEmployer={savedCountsByEmployer}
            onDraft={onDraft}
          />
        ))}
      </div>
    </div>
  );
}

/* ── Sector Group ─────────────────────────────────────────────────────── */

function SectorGroup({
  sector, opportunities, index, isOpen, isPriority, school,
  onToggle, savedCountsByEmployer, onDraft,
}: {
  sector: string;
  opportunities: ApiPartnershipOpportunity[];
  index: number;
  isOpen: boolean;
  isPriority: boolean;
  school: SchoolConfig;
  onToggle: () => void;
  savedCountsByEmployer: Record<string, number>;
  onDraft: (opp: ApiPartnershipOpportunity) => void;
}) {
  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);
  const count = opportunities.length;
  const brandColor = school.brandColorLight;
  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(index * 0.01, 0.2) }}
        onClick={onToggle}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px 1fr auto",
          padding: "18px 16px", gap: "12px", alignItems: "center",
          background: isOpen ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.035)",
          border: "none", borderBottom: `1px solid ${isOpen ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.05)"}`,
          borderTop: isOpen ? `2px solid ${brandColor}80` : "2px solid transparent",
          cursor: "pointer", transition: "background 0.15s, border-color 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.055)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.035)"; }}
      >
        <svg width="14" height="14" viewBox="0 0 12 12" fill="none"
          style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
          <span style={{
            fontFamily: FONT, fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em",
            textTransform: "uppercase", color: "rgba(255,255,255,0.98)",
            lineHeight: 1.4,
          }}>
            {sector}
          </span>
          {isPriority && (
            <span
              title="Regional priority sector"
              style={{
                display: "inline-block", width: "7px", height: "7px",
                borderRadius: "50%", background: brandColor, flexShrink: 0,
                boxShadow: `0 0 6px ${brandColor}80`,
              }}
            />
          )}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.45)" }}>
          {count} {count === 1 ? "employer" : "employers"}
        </span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
          >
            <div>
              {opportunities.map((opp, i) => (
                <Fragment key={opp.name}>
                  <PartnershipRow
                    opp={opp}
                    i={i}
                    school={school}
                    savedCount={savedCountsByEmployer[opp.name] ?? 0}
                    onDraft={onDraft}
                  />
                </Fragment>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
