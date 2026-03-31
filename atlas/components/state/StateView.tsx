"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import PageTransition from "@/components/transitions/PageTransition";
import CaliforniaMap, { FEATURED_COLLEGES } from "@/components/state/CaliforniaMap";
import RisingSun from "@/components/ui/RisingSun";
import { College, Region, CALIFORNIA_REGIONS, CALIFORNIA_COLLEGES } from "@/lib/californiaColleges";
import { getCollegeAtlasConfig } from "@/lib/collegeAtlasConfigs";
import AtlasMenu from "@/components/auth/AtlasMenu";
import type { SchoolConfig } from "@/lib/schoolConfig";

export default function StateView() {
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

  const [mapView, setMapView] = useState<"state" | "region">("state");
  const [activeRegionId, setActiveRegionId] = useState<string | null>(null);
  const [hoveredRegionId, setHoveredRegionId] = useState<string | null>(null);
  const [hoveredCollege, setHoveredCollege] = useState<College | null>(null);
  const [selectedCollege, setSelectedCollege] = useState<College | null>(null);
  const [mapOpacity, setMapOpacity] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [mapPanelHovered, setMapPanelHovered] = useState(false);
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

  const handleRegionClick = useCallback((_id: string) => {
    // Region zoom disabled — hover highlighting only
  }, []);

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

  const activeRegion = CALIFORNIA_REGIONS.find((r) => r.id === activeRegionId) ?? null;
  const activeCollege = selectedCollege ?? hoveredCollege;
  const regionColleges = activeRegionId
    ? CALIFORNIA_COLLEGES.filter((c) => c.regionId === activeRegionId)
    : [];
  const regionCollegeCount = regionColleges.length;
  const regionDistrictCount = new Set(regionColleges.map((c) => c.district)).size;

  // Right panel label under the map
  const mapLabel = "California · 116 Colleges";

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
        {/* Header */}
        <header
          style={{
            flexShrink: 0,
            height: "64px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 40px",
            background: "rgba(6, 13, 31, 0.95)",
            backdropFilter: "blur(8px)",
            borderBottom: "1px solid rgba(255,255,255,0.07)",
            zIndex: 10,
          }}
        >
          <button
            onClick={() => userCollegeId ? router.push(`/${userCollegeId}`) : router.back()}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: "8px",
              color: userSchool?.brandColorLight ?? "rgba(255,255,255,0.7)",
              transition: "opacity 0.15s",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.opacity = "0.7")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.opacity = "1")}
            aria-label="Back to Atlas"
          >
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={userSchool?.brandColor ?? "rgba(255,255,255,0.3)"} opacity="0.85" />
              <path d="M12 13v9l9-5.5v-9L12 13z" fill={userSchool?.brandColor ?? "rgba(255,255,255,0.3)"} opacity="0.55" />
              <path d="M12 13v9L3 16.5v-9L12 13z" fill={userSchool?.brandColor ?? "rgba(255,255,255,0.3)"} opacity="0.4" />
              <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="rgba(255,255,255,0.55)" strokeWidth="0.7" />
            </svg>
            <svg width="20" height="20" viewBox="0 0 16 16" fill="none">
              <path d="M10 12L6 8l4-4" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <img src="/kallipolis-logo.png" alt="Kallipolis" style={{ height: "28px", width: "auto", objectFit: "contain" }} />
              <span style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "16px", color: "#ffffff", lineHeight: 1 }}>
                Kallipolis
              </span>
            </div>
            <AtlasMenu navItems={[{ label: "Home View", href: userCollegeId ? `/${userCollegeId}` : "/", icon: (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={userSchool?.brandColor ?? "rgba(255,255,255,0.3)"} opacity="0.85" />
                <path d="M12 13v9l9-5.5v-9L12 13z" fill={userSchool?.brandColor ?? "rgba(255,255,255,0.3)"} opacity="0.55" />
                <path d="M12 13v9L3 16.5v-9L12 13z" fill={userSchool?.brandColor ?? "rgba(255,255,255,0.3)"} opacity="0.4" />
                <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="rgba(255,255,255,0.55)" strokeWidth="0.7" />
              </svg>
            ) }]} />
          </div>
        </header>

        {/* Body */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
          {/* Left — map + search */}
          <div
            onClick={() => setSelectedCollege(null)}
            onMouseEnter={() => setMapPanelHovered(true)}
            onMouseLeave={() => setMapPanelHovered(false)}
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
            {/* Search bar */}
            <div style={{ width: "100%", maxWidth: "440px", flexShrink: 0, position: "relative", zIndex: 5 }}>
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

              {/* Search results dropdown */}
              <AnimatePresence>
                {showSearchResults && (
                  <motion.div
                    key="search-dropdown"
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.12 }}
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      position: "absolute",
                      top: "calc(100% + 6px)",
                      left: 0,
                      right: 0,
                      maxHeight: "320px",
                      overflowY: "auto",
                      background: "rgba(10, 14, 28, 0.97)",
                      border: "1px solid rgba(255,255,255,0.10)",
                      borderRadius: "6px",
                      backdropFilter: "blur(12px)",
                      padding: "6px 0",
                    }}
                  >
                    <SearchResults results={searchResults} query={searchQuery} onSelect={handleSearchSelect} activeIndex={searchActiveIndex} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Map */}
            <div
              style={{
                flex: 1,
                width: "100%",
                maxWidth: "440px",
                aspectRatio: "400 / 500",
                marginTop: "8px",
                opacity: mapOpacity,
                transition: "opacity 0.18s ease",
              }}
            >
              <CaliforniaMap
                mapView={mapView}
                activeRegionId={activeRegionId}
                hoveredRegionId={hoveredRegionId}
                hoveredCollegeId={hoveredCollege?.id ?? null}
                selectedCollegeId={selectedCollege?.id ?? null}
                onRegionHover={setHoveredRegionId}
                onRegionClick={handleRegionClick}
                onCollegeHover={setHoveredCollege}
                onCollegeSelect={handleCollegeSelect}
              />
            </div>

            {/* Sun prompt */}
            <AnimatePresence>
              {mapPanelHovered && !showSearchResults && (
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
                  <div style={{ opacity: hoveredRegionId ? 1 : 0.45, transition: "opacity 0.4s ease-in-out" }}>
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
                      color: hoveredRegionId ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.55)",
                      whiteSpace: "nowrap",
                      transition: "color 0.3s ease-in-out",
                    }}>
                      {hoveredRegionId
                        ? (CALIFORNIA_REGIONS.find((r) => r.id === hoveredRegionId)?.name ?? "Select a region")
                        : "Select a region"}
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

          </div>

          {/* Right — info panel */}
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
            {/* Panel content — scrollable */}
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "40px 56px 150px",
              }}
            >
              <AnimatePresence mode="wait">
                {activeCollege ? (
                  <motion.div key={`school-${activeCollege.id}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.18 }} onClick={(e) => e.stopPropagation()}>
                    <SchoolPanel college={activeCollege} />
                  </motion.div>
                ) : (
                  <motion.div key="default" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.18 }}>
                    <DefaultPanel />
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
  activeIndex,
}: {
  results: College[];
  query: string;
  onSelect: (college: College) => void;
  activeIndex: number;
}) {
  const listRef = useRef<HTMLDivElement>(null);

  // Scroll active item into view
  useEffect(() => {
    if (activeIndex < 0 || !listRef.current) return;
    const row = listRef.current.children[activeIndex + 1] as HTMLElement | undefined; // +1 for the count label
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
      <span style={{
        fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
        fontSize: "10px",
        fontWeight: 600,
        letterSpacing: "0.14em",
        textTransform: "uppercase",
        color: "rgba(255,255,255,0.35)",
        padding: "0 0 12px",
      }}>
        {results.length} {results.length === 1 ? "result" : "results"}
      </span>
      {results.map((college, i) => (
        <SearchResultRow key={college.id} college={college} onSelect={onSelect} isActive={i === activeIndex} />
      ))}
    </div>
  );
}

function SearchResultRow({
  college,
  onSelect,
  isActive,
}: {
  college: College;
  onSelect: (college: College) => void;
  isActive: boolean;
}) {
  const config = getCollegeAtlasConfig(college.id);
  const accent = config?.brandColorLight ?? "#c9a84c";
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
      onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)"; }}
      onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
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

function DefaultPanel() {
  return null;
}

function RegionPanel({ region, collegeCount, districtCount }: { region: Region; collegeCount: number; districtCount: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <h2 style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "clamp(24px, 2.8vw, 38px)", lineHeight: 1.2, color: "#ffffff", margin: 0 }}>
          {region.name}
        </h2>
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)" }}>
          {collegeCount} {collegeCount === 1 ? "college" : "colleges"} · {districtCount} {districtCount === 1 ? "district" : "districts"}
        </span>
      </div>

      <div style={{ height: "1px", background: "rgba(255,255,255,0.08)" }} />
    </div>
  );
}

function SchoolPanel({ college }: { college: College }) {
  const region = CALIFORNIA_REGIONS.find((r) => r.id === college.regionId);
  const config = getCollegeAtlasConfig(college.id);
  const accent = config?.brandColorLight ?? "#c9a84c";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <h2 style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "clamp(22px, 2.4vw, 34px)", lineHeight: 1.2, color: "#ffffff", margin: 0 }}>
          {college.name}
        </h2>
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.4)" }}>
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
          Open Atlas
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M3 7h8M7 3l4 4-4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Link>
      </div>
    </div>
  );
}

function Section({ label, body }: { label: string; body: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px", paddingLeft: "16px", borderLeft: "2px solid rgba(201,168,76,0.35)" }}>
      <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "10px", fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "#c9a84c" }}>
        {label}
      </span>
      <p style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "14px", lineHeight: 1.65, color: "rgba(255,255,255,0.72)", margin: 0 }}>
        {body}
      </p>
    </div>
  );
}
