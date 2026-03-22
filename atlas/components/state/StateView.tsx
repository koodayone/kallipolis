"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import PageTransition from "@/components/transitions/PageTransition";
import CaliforniaMap from "@/components/state/CaliforniaMap";
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

  const transitionMap = useCallback((fn: () => void) => {
    setMapOpacity(0);
    const t = setTimeout(() => {
      fn();
      setMapOpacity(1);
    }, 200);
    return () => clearTimeout(t);
  }, []);

  const handleRegionClick = useCallback((id: string) => {
    transitionMap(() => {
      setActiveRegionId(id);
      setMapView("region");
      setSelectedCollege(null);
      setHoveredCollege(null);
    });
  }, [transitionMap]);

  const handleMapBack = useCallback(() => {
    transitionMap(() => {
      setMapView("state");
      setActiveRegionId(null);
      setHoveredRegionId(null);
      setSelectedCollege(null);
      setHoveredCollege(null);
    });
  }, [transitionMap]);

  const handleCollegeSelect = useCallback((college: College) => {
    setSelectedCollege((prev) => (prev?.id === college.id ? null : college));
  }, []);

  const activeRegion = CALIFORNIA_REGIONS.find((r) => r.id === activeRegionId) ?? null;
  const activeCollege = selectedCollege ?? hoveredCollege;
  const regionColleges = activeRegionId
    ? CALIFORNIA_COLLEGES.filter((c) => c.regionId === activeRegionId)
    : [];
  const regionCollegeCount = regionColleges.length;
  const regionDistrictCount = new Set(regionColleges.map((c) => c.district)).size;

  // Right panel label under the map
  const mapLabel = mapView === "region" && activeRegion
    ? `${activeRegion.name} · ${regionCollegeCount} colleges`
    : "California · 116 Colleges";

  return (
    <PageTransition>
      <div
        style={{
          width: "100vw",
          height: "100vh",
          background: "#041e54",
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
            background: "rgba(4, 30, 84, 0.95)",
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
          {/* Left — map */}
          <div
            style={{
              flex: 1,
              position: "relative",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "32px 24px 24px",
              gap: "14px",
            }}
          >
            {/* Back affordance — anchored to top of panel */}
            <AnimatePresence>
              {mapView === "region" && (
                <motion.button
                  key="back"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  onClick={handleMapBack}
                  style={{
                    position: "absolute",
                    top: "20px",
                    left: "24px",
                    display: "flex",
                    alignItems: "center",
                    gap: "5px",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: "4px 0",
                    fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                    fontSize: "11px",
                    fontWeight: 500,
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: "rgba(255,255,255,0.5)",
                    transition: "color 0.15s",
                    zIndex: 10,
                  }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#ffffff")}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.5)")}
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M8 2L4 6l4 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  All regions
                </motion.button>
              )}
            </AnimatePresence>
            {/* Sun prompt — state view idle/hover, Nevada geographic area */}
            <AnimatePresence>
              {mapView === "state" && (
                <motion.div
                  key="sun-prompt"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  style={{
                    position: "absolute",
                    right: "20%",
                    top: "17%",
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

            <div
              style={{
                width: "100%",
                maxWidth: "440px",
                maxHeight: "80vh",
                aspectRatio: "400 / 500",
                paddingTop: mapView === "region" ? "16px" : "0",
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

          </div>

          {/* Right — info panel */}
          <div
            style={{
              width: "50%",
              flexShrink: 0,
              borderLeft: "1px solid rgba(255,255,255,0.07)",
              padding: "56px 56px 48px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              overflowY: "auto",
            }}
          >
            <AnimatePresence mode="wait">
              {activeCollege ? (
                <motion.div key={`school-${activeCollege.id}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.18 }}>
                  <SchoolPanel college={activeCollege} />
                </motion.div>
              ) : mapView === "region" && activeRegion ? (
                <motion.div key={`region-${activeRegion.id}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.18 }}>
                  <RegionPanel region={activeRegion} collegeCount={regionCollegeCount} districtCount={regionDistrictCount} />
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
    </PageTransition>
  );
}

// ── Panels ────────────────────────────────────────────────────────────────────

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
      {(college.logoLongform ?? college.logoStacked) && (
        <img
          src={college.logoLongform ?? college.logoStacked}
          alt={college.name}
          style={{
            height: "44px",
            width: "auto",
            maxWidth: "100%",
            objectFit: "contain",
            objectPosition: "left center",
          }}
        />
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <h2 style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "clamp(22px, 2.4vw, 34px)", lineHeight: 1.2, color: "#ffffff", margin: 0 }}>
          {college.name}
        </h2>
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.4)" }}>
          {college.district}
        </span>
      </div>

      <div style={{ height: "1px", background: "rgba(255,255,255,0.08)" }} />

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
