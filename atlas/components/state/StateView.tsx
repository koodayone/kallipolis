"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import PageTransition from "@/components/transitions/PageTransition";
import CaliforniaMap from "@/components/state/CaliforniaMap";
import { College, Region, CALIFORNIA_REGIONS, CALIFORNIA_COLLEGES } from "@/lib/californiaColleges";

export default function StateView() {
  const router = useRouter();

  const [mapView, setMapView] = useState<"state" | "region">("state");
  const [activeRegionId, setActiveRegionId] = useState<string | null>(null);
  const [hoveredRegionId, setHoveredRegionId] = useState<string | null>(null);
  const [hoveredCollege, setHoveredCollege] = useState<College | null>(null);
  const [selectedCollege, setSelectedCollege] = useState<College | null>(null);

  const handleRegionClick = useCallback((id: string) => {
    setActiveRegionId(id);
    setMapView("region");
    setSelectedCollege(null);
    setHoveredCollege(null);
  }, []);

  const handleMapBack = useCallback(() => {
    setMapView("state");
    setActiveRegionId(null);
    setHoveredRegionId(null);
    setSelectedCollege(null);
    setHoveredCollege(null);
  }, []);

  const handleCollegeSelect = useCallback((college: College) => {
    setSelectedCollege((prev) => (prev?.id === college.id ? null : college));
  }, []);

  const activeRegion = CALIFORNIA_REGIONS.find((r) => r.id === activeRegionId) ?? null;
  const activeCollege = selectedCollege ?? hoveredCollege;
  const regionCollegeCount = activeRegionId
    ? CALIFORNIA_COLLEGES.filter((c) => c.regionId === activeRegionId).length
    : 0;

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
          background: "#0a0a0f",
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
            background: "rgba(10, 10, 15, 0.95)",
            backdropFilter: "blur(8px)",
            borderBottom: "1px solid rgba(255,255,255,0.07)",
            zIndex: 10,
          }}
        >
          <button
            onClick={() => router.back()}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: "6px 0",
              color: "#ffffff",
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "12px",
              fontWeight: 500,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              transition: "opacity 0.15s",
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.opacity = "0.65")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.opacity = "1")}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M10 12L6 8l4-4" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Atlas
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <img src="/kallipolis-logo.png" alt="Kallipolis" style={{ height: "28px", width: "auto", objectFit: "contain" }} />
            <span style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "16px", color: "#ffffff", lineHeight: 1 }}>
              Kallipolis
            </span>
          </div>
        </header>

        {/* Body */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
          {/* Left — map */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "32px 24px 24px",
              gap: "14px",
            }}
          >
            <div
              style={{
                width: "100%",
                maxWidth: "440px",
                maxHeight: "80vh",
                aspectRatio: "400 / 500",
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
                onBack={handleMapBack}
              />
            </div>

            <motion.span
              key={mapLabel}
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.6 }}
              transition={{ duration: 0.3 }}
              style={{
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "10px",
                fontWeight: 500,
                letterSpacing: "0.16em",
                textTransform: "uppercase",
                color: "#c9a84c",
              }}
            >
              {mapLabel}
            </motion.span>
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
                  <RegionPanel region={activeRegion} collegeCount={regionCollegeCount} />
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
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "40px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "11px", fontWeight: 500, letterSpacing: "0.16em", textTransform: "uppercase", color: "#c9a84c" }}>
          The State View
        </span>
        <div style={{ width: "32px", height: "1px", background: "#c9a84c", opacity: 0.5 }} />
      </div>

      <h1 style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "clamp(28px, 3.2vw, 44px)", lineHeight: 1.15, color: "#ffffff", margin: 0 }}>
        116 schools.<br />73 districts.<br />One intelligent network.
      </h1>

      <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
        <Section label="Statewide Vision" body="Kallipolis empowers California Community Colleges to serve 2 million students in every region of the state." />
        <Section label="Our Software" body="We unify data & spread intelligence across the ecosystem by deploying AI tailored to empower workforce development initiatives." />
      </div>

      <p style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "13px", color: "rgba(255,255,255,0.35)", margin: 0, letterSpacing: "0.02em" }}>
        Select a region on the map to explore.
      </p>
    </div>
  );
}

function RegionPanel({ region, collegeCount }: { region: Region; collegeCount: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "11px", fontWeight: 500, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(255,255,255,0.4)" }}>
        California Region
      </span>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <h2 style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "clamp(24px, 2.8vw, 38px)", lineHeight: 1.2, color: "#ffffff", margin: 0 }}>
          {region.name}
        </h2>
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "#c9a84c" }}>
          {region.collegeCount} colleges · {region.counties.length} {region.counties.length === 1 ? "county" : "counties"}
        </span>
      </div>

      <div style={{ height: "1px", background: "rgba(255,255,255,0.08)" }} />

      <p style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "13px", color: "rgba(255,255,255,0.35)", margin: 0, letterSpacing: "0.02em" }}>
        Hover a college marker to explore.
      </p>
    </div>
  );
}

function SchoolPanel({ college }: { college: College }) {
  const region = CALIFORNIA_REGIONS.find((r) => r.id === college.regionId);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "11px", fontWeight: 500, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(255,255,255,0.4)" }}>
        {region?.name ?? college.regionId}
      </span>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <h2 style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "clamp(22px, 2.4vw, 34px)", lineHeight: 1.2, color: "#ffffff", margin: 0 }}>
          {college.name}
        </h2>
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "#c9a84c" }}>
          {college.district}
        </span>
      </div>

      <div style={{ height: "1px", background: "rgba(255,255,255,0.08)" }} />

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <Link
          href="/"
          style={{ display: "inline-flex", alignItems: "center", gap: "8px", padding: "12px 24px", border: "1px solid #c9a84c", borderRadius: "2px", color: "#c9a84c", fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "12px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", textDecoration: "none", width: "fit-content", transition: "background 0.15s, color 0.15s" }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#c9a84c"; (e.currentTarget as HTMLElement).style.color = "#0a0a0f"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; (e.currentTarget as HTMLElement).style.color = "#c9a84c"; }}
        >
          Open Atlas
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M3 7h8M7 3l4 4-4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Link>
        <span style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif", fontSize: "11px", color: "rgba(255,255,255,0.25)" }}>
          Opens Foothill College atlas (placeholder)
        </span>
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
