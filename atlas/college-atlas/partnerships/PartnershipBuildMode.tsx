"use client";

import { useCallback, type RefObject } from "react";
import { motion } from "framer-motion";
import type { SchoolConfig } from "@/config/schoolConfig";
import type { ApiPartnershipOpportunity } from "@/college-atlas/partnerships/api";
import RisingSun from "@/ui/RisingSun";
import EntityScrollList from "@/ui/EntityScrollList";
import type { Column } from "@/ui/EntityScrollList";
import PartnershipRow from "./PartnershipRow";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const PARTNERSHIP_COLUMNS: Column[] = [
  { label: "Employer", width: "1fr" },
  { label: "Sector", width: "160px" },
];

type Props = {
  school: SchoolConfig;
  userName: string;
  loading: boolean;
  error: string | null;
  query: string;
  setQuery: (q: string) => void;
  inputRef: RefObject<HTMLInputElement | null>;
  filteredOpportunities: ApiPartnershipOpportunity[];
  expandedNames: Set<string>;
  onExpand: (opp: ApiPartnershipOpportunity) => void;
  onDraft: (opp: ApiPartnershipOpportunity) => void;
};

export default function PartnershipBuildMode({
  school,
  userName,
  loading,
  error,
  query,
  setQuery,
  inputRef,
  filteredOpportunities,
  expandedNames,
  onExpand,
  onDraft,
}: Props) {
  const renderPartnershipRow = useCallback(
    (opp: ApiPartnershipOpportunity, i: number) => (
      <PartnershipRow
        opp={opp}
        i={i}
        school={school}
        expandedNames={expandedNames}
        onExpand={onExpand}
        onDraft={onDraft}
      />
    ),
    [school, expandedNames, onExpand, onDraft],
  );

  const keyExtractor = useCallback((opp: ApiPartnershipOpportunity) => opp.name, []);

  if (error) {
    return (
      <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>
        {error}
      </p>
    );
  }

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
        <RisingSun style={{ width: "90px", height: "auto", opacity: 0.4 }} />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{ display: "flex", flexDirection: "column", gap: "24px" }}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px" }}>
        <RisingSun style={{ width: "90px", height: "auto" }} />
        <h1 style={{ fontFamily: FONT, fontSize: "28px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", textAlign: "center", margin: 0 }}>
          Who is our partner{userName ? `, ${userName}` : ""}?
        </h1>
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
      </div>
      <EntityScrollList
        items={filteredOpportunities}
        initialCap={50}
        batchSize={50}
        columns={PARTNERSHIP_COLUMNS}
        renderRow={renderPartnershipRow}
        keyExtractor={keyExtractor}
        entityName="partnership opportunities"
        school={school}
      />
    </motion.div>
  );
}
