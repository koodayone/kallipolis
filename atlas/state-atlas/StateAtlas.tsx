"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import PageTransition from "@/ui/PageTransition";
import dynamic from "next/dynamic";
const CaliforniaMap = dynamic(() => import("@/state-atlas/CaliforniaMap"), { ssr: false });
import { FEATURED_COLLEGES } from "@/state-atlas/CaliforniaMap";
import KallipolisBrand from "@/ui/KallipolisBrand";
import AtlasHeader from "@/ui/AtlasHeader";
import RisingSun from "@/ui/RisingSun";
import { College, CALIFORNIA_REGIONS, CALIFORNIA_COLLEGES } from "@/state-atlas/californiaColleges";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import AtlasMenu from "@/auth/AtlasMenu";
import type { SchoolConfig } from "@/config/schoolConfig";

export default function StateAtlas() {
  const router = useRouter();
  const [userSchool, setUserSchool] = useState<SchoolConfig | null>(null);
  const [userCollegeId, setUserCollegeId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => {
        if (data.user?.collegeId) {
          setUserCollegeId(data.user.collegeId);
          setUserSchool(getCollegeAtlasConfig(data.user.collegeId) ?? null);
        }
      })
      .catch(() => {});
  }, []);

  const [hoveredRegionId, setHoveredRegionId] = useState<string | null>(null);
  const [hoveredCollege, setHoveredCollege] = useState<College | null>(null);
  const [selectedCollege, setSelectedCollege] = useState<College | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const [searchFocused, setSearchFocused] = useState(false);
  const [searchActiveIndex, setSearchActiveIndex] = useState(-1);
  const searchRef = useRef<HTMLInputElement>(null);

  const featuredCollegesSorted = useMemo(() =>
    CALIFORNIA_COLLEGES.filter((c) => FEATURED_COLLEGES.has(c.id)).sort((a, b) => a.name.localeCompare(b.name)),
    []
  );

  const searchResults = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (q.length === 0) return featuredCollegesSorted;
    return featuredCollegesSorted.filter((c) =>
      c.name.toLowerCase().includes(q) ||
      c.district.toLowerCase().includes(q) ||
      CALIFORNIA_REGIONS.find((r) => r.id === c.regionId)?.name.toLowerCase().includes(q)
    );
  }, [searchQuery, featuredCollegesSorted]);

  // Reset active index when results change
  useEffect(() => { setSearchActiveIndex(-1); }, [searchResults]);

  const showSearchResults = searchFocused || searchQuery.trim().length > 0;

  const handleCollegeSelect = useCallback((college: College) => {
    setSelectedCollege((prev) => (prev?.id === college.id ? null : college));
  }, []);

  const handleSearchSelect = useCallback((college: College) => {
    setSearchQuery("");
    setSearchActiveIndex(-1);
    searchRef.current?.blur();
    setSelectedCollege(college);
  }, []);

  const handleSearchKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSearchResults || searchResults.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSearchActiveIndex((prev) => (prev < searchResults.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSearchActiveIndex((prev) => (prev > 0 ? prev - 1 : searchResults.length - 1));
    } else if (e.key === "Enter" && searchActiveIndex >= 0) {
      e.preventDefault();
      handleSearchSelect(searchResults[searchActiveIndex]);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setSearchQuery("");
      setSearchActiveIndex(-1);
      searchRef.current?.blur();
    }
  }, [showSearchResults, searchResults, searchActiveIndex, handleSearchSelect]);

  const activeCollege = selectedCollege ?? hoveredCollege;

  return (
    <PageTransition>
      <div
        style={{
          width: "100vw",
          height: "100vh",
          background: "#060d1f",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <AtlasHeader
          position="static"
          school={userSchool ?? undefined}
          title="State Atlas"
          onBack={() => userCollegeId ? router.push(`/${userCollegeId}`) : router.back()}
          rightSlot={
            <>
              <KallipolisBrand />
              <AtlasMenu navItems={[{ label: "Home Atlas", href: userCollegeId ? `/${userCollegeId}` : "/", icon: (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={userSchool?.brandColorNeon ?? "rgba(255,255,255,0.3)"} opacity="0.85" />
                  <path d="M12 13v9l9-5.5v-9L12 13z" fill={userSchool?.brandColorNeon ?? "rgba(255,255,255,0.3)"} opacity="0.55" />
                  <path d="M12 13v9L3 16.5v-9L12 13z" fill={userSchool?.brandColorNeon ?? "rgba(255,255,255,0.3)"} opacity="0.4" />
                  <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="rgba(255,255,255,0.55)" strokeWidth="0.7" />
                </svg>
              ) }]} />
            </>
          }
        />

        {/* Body */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
          {/* Left — map */}
          <div
            onClick={() => setSelectedCollege(null)}
            style={{
              flex: 1,
              position: "relative",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              padding: "24px 40px 24px",
              overflow: "hidden",
            }}
          >
            {/* Map */}
            <div
              style={{
                flex: 1,
                width: "100%",
                maxWidth: "440px",
                aspectRatio: "400 / 500",
              }}
            >
              <CaliforniaMap
                hoveredRegionId={hoveredRegionId}
                hoveredCollegeId={hoveredCollege?.id ?? null}
                selectedCollegeId={selectedCollege?.id ?? null}
                dimMarkers={false}
                onRegionHover={setHoveredRegionId}
                onCollegeHover={setHoveredCollege}
                onCollegeSelect={handleCollegeSelect}
              />
            </div>

            {/* Sun prompt */}
            <AnimatePresence>
              {(
                <motion.div
                  key="sun-prompt"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  style={{
                    position: "absolute",
                    right: "18%",
                    top: "15%",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    pointerEvents: "none",
                  }}
                >
                  <div style={{ opacity: activeCollege || hoveredRegionId ? 1 : 0.45, transition: "opacity 0.4s ease-in-out" }}>
                    <RisingSun />
                  </div>
                  <div style={{ position: "relative", height: "16px", width: "0", marginTop: "10px" }}>
                    <span style={{
                      position: "absolute",
                      left: "50%",
                      transform: "translateX(-50%)",
                      fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                      fontSize: "11px",
                      fontWeight: 500,
                      letterSpacing: "0.14em",
                      textTransform: "uppercase",
                      color: activeCollege || hoveredRegionId ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.55)",
                      whiteSpace: "nowrap",
                      transition: "color 0.3s ease-in-out",
                    }}>
                      {activeCollege
                        ? activeCollege.name
                        : hoveredRegionId
                        ? (CALIFORNIA_REGIONS.find((r) => r.id === hoveredRegionId)?.name ?? "Select a college")
                        : "Select a college"}
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

          </div>

          {/* Right — search + info panel */}
          <div
            onClick={() => setSelectedCollege(null)}
            style={{
              width: "50%",
              flexShrink: 0,
              borderLeft: "1px solid rgba(255,255,255,0.07)",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            {/* Search bar */}
            <div style={{ flexShrink: 0, padding: "24px 40px 0" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "0 20px",
                  height: "48px",
                  background: searchFocused ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
                  border: `1px solid ${searchFocused ? "rgba(201,168,76,0.4)" : "rgba(255,255,255,0.08)"}`,
                  borderRadius: "6px",
                  transition: "all 0.2s ease",
                }}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, opacity: searchFocused ? 0.8 : 0.4, transition: "opacity 0.2s" }}>
                  <circle cx="7" cy="7" r="5" stroke="rgba(255,255,255,0.9)" strokeWidth="1.3" />
                  <path d="M11 11l3.5 3.5" stroke="rgba(255,255,255,0.9)" strokeWidth="1.3" strokeLinecap="round" />
                </svg>
                <input
                  ref={searchRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleSearchKeyDown}
                  onFocus={() => setSearchFocused(true)}
                  onBlur={() => setTimeout(() => setSearchFocused(false), 150)}
                  placeholder="Search colleges…"
                  style={{
                    flex: 1,
                    background: "none",
                    border: "none",
                    outline: "none",
                    fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                    fontSize: "13px",
                    fontWeight: 400,
                    color: "#ffffff",
                    letterSpacing: "0.01em",
                  }}
                />
                {searchQuery.length > 0 && (
                  <button
                    onClick={() => { setSearchQuery(""); searchRef.current?.focus(); }}
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      padding: "4px",
                      color: "rgba(255,255,255,0.4)",
                      display: "flex",
                      alignItems: "center",
                      transition: "color 0.15s",
                    }}
                    onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.8)")}
                    onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.4)")}
                  >
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                      <path d="M3.5 3.5l7 7M10.5 3.5l-7 7" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
                    </svg>
                  </button>
                )}
              </div>
            </div>

            {/* College list or school panel */}
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                margin: "16px 40px 24px",
                maxHeight: "calc(100vh - 240px)",
                overflowY: "auto",
              }}
            >
              <AnimatePresence mode="wait">
                {activeCollege ? (
                  <motion.div key={`school-${activeCollege.id}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.18 }}>
                    <SchoolPanel college={activeCollege} />
                  </motion.div>
                ) : (
                  <motion.div key="college-list" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.18 }}
                    style={{
                      borderRadius: "6px",
                      border: "1px solid rgba(255,255,255,0.06)",
                      background: "rgba(255,255,255,0.02)",
                      padding: "6px 0",
                    }}
                  >
                    <SearchResults results={searchResults} query={searchQuery} onSelect={handleSearchSelect} activeIndex={searchActiveIndex} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}

// ── Panels ────────────────────────────────────────────────────────────────────

function SearchResults({
  results,
  query,
  onSelect,
  onHover,
  activeIndex,
}: {
  results: College[];
  query: string;
  onSelect: (college: College) => void;
  onHover?: (college: College | null) => void;
  activeIndex: number;
}) {
  const listRef = useRef<HTMLDivElement>(null);

  // Scroll active item into view
  useEffect(() => {
    if (activeIndex < 0 || !listRef.current) return;
    const row = listRef.current.children[activeIndex] as HTMLElement | undefined;
    if (row) row.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  if (results.length === 0) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "16px", paddingTop: "8px" }}>
        <span style={{
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "13px",
          color: "rgba(255,255,255,0.4)",
        }}>
          No colleges matching &ldquo;{query}&rdquo;
        </span>
      </div>
    );
  }

  return (
    <div ref={listRef} style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      {results.map((college, i) => (
        <SearchResultRow key={college.id} college={college} onSelect={onSelect} onHover={onHover} isActive={i === activeIndex} />
      ))}
    </div>
  );
}

function SearchResultRow({
  college,
  onSelect,
  onHover,
  isActive,
}: {
  college: College;
  onSelect: (college: College) => void;
  onHover?: (college: College | null) => void;
  isActive: boolean;
}) {
  const config = getCollegeAtlasConfig(college.id);
  const accent = config?.brandColorNeon ?? "#c9a84c";
  const region = CALIFORNIA_REGIONS.find((r) => r.id === college.regionId);

  return (
    <button
      onClick={() => onSelect(college)}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "16px",
        padding: "14px 16px",
        background: isActive ? "rgba(255,255,255,0.06)" : "transparent",
        border: "none",
        borderRadius: "2px",
        cursor: "pointer",
        textAlign: "left",
        width: "100%",
        transition: "background 0.12s ease",
      }}
      onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)"; onHover?.(college); }}
      onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = "transparent"; onHover?.(null); }}
    >
      {/* Brand accent bar */}
      <div style={{
        width: "3px",
        height: "36px",
        borderRadius: "2px",
        background: accent,
        opacity: 0.7,
        flexShrink: 0,
      }} />

      {/* Text */}
      <div style={{ display: "flex", flexDirection: "column", gap: "3px", minWidth: 0 }}>
        <span style={{
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "14px",
          fontWeight: 600,
          color: "#ffffff",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}>
          {college.name}
        </span>
        <span style={{
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "11px",
          fontWeight: 400,
          color: "rgba(255,255,255,0.4)",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}>
          {college.district}{region ? ` · ${region.name}` : ""}
        </span>
      </div>
    </button>
  );
}

function SchoolPanel({ college }: { college: College }) {
  const config = getCollegeAtlasConfig(college.id);
  const accent = config?.brandColorNeon ?? "#c9a84c";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px", paddingTop: "48px", paddingLeft: "16px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <h2 style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "clamp(26px, 2.8vw, 40px)", lineHeight: 1.2, color: "#ffffff", margin: 0 }}>
          {college.name}
        </h2>
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "13px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)" }}>
          {college.district}
        </span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <Link
          href={`/${college.id}`}
          style={{ display: "inline-flex", alignItems: "center", gap: "8px", padding: "12px 24px", border: `1px solid ${accent}`, borderRadius: "2px", color: accent, fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", textDecoration: "none", width: "fit-content", transition: "background 0.15s, color 0.15s" }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = accent; (e.currentTarget as HTMLElement).style.color = "#0a0a0f"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; (e.currentTarget as HTMLElement).style.color = accent; }}
        >
          Open College Atlas
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill="currentColor" opacity="0.85" />
            <path d="M12 13v9l9-5.5v-9L12 13z" fill="currentColor" opacity="0.55" />
            <path d="M12 13v9L3 16.5v-9L12 13z" fill="currentColor" opacity="0.4" />
            <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="currentColor" strokeWidth="0.7" opacity="0.6" />
          </svg>
        </Link>
      </div>
    </div>
  );
}

