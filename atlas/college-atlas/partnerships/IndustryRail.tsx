"use client";

/* ── Industry rail — the SWP-sector channel selector ───────────────────────
   First row of the dashboard's sticky stack, above the lens tabs: holds the
   member set (district) and region constant and swaps the industry lens —
   the axis you used to navigate *to* (eleven separate URLs) becomes the axis
   you navigate *through*. One row of platonic forms (see industryForms): the
   active industry wears the active LENS accent (the same color the tabs and
   chips show), so color reads as "the current view" and SHAPE reads as the
   industry — never an eleven-hue palette. Each item is a real link to
   /<member>-<sector> with window.location.search preserved (the lens and
   selection survive the hop) so views stay deep-linkable. Renders only for a
   member-set landscape with ≥2 viewable sectors (e.g. SMCCD); single-instance
   landscapes (SVAMP) get no rail. */

import React from "react";
import { useRouter } from "next/navigation";
import { MONO } from "@/college-atlas/partnerships/reportChrome";
import { memberSectors, isLandscapeViewable } from "@/college-atlas/partnerships/landscapeInstances";
import { INDUSTRY_FORMS } from "@/college-atlas/partnerships/industryForms";

export default function IndustryRail({ instance, activeAccent }: { instance: string; activeAccent: string }) {
  const router = useRouter();
  const sectors = memberSectors(instance).filter((s) => isLandscapeViewable(s.instanceId));
  if (sectors.length < 2) return null;
  return (
    <div style={{ display: "flex", gap: 2, overflowX: "auto", paddingBottom: 10, marginBottom: 12, borderBottom: "1px solid rgba(255,255,255,.06)" }}>
      {sectors.map((s) => {
        const def = INDUSTRY_FORMS[s.sectorId];
        if (!def) return null;
        const on = s.instanceId === instance;
        const { Form } = def;
        return (
          <a
            key={s.instanceId}
            href={`/${s.instanceId}`}
            title={s.label}
            aria-label={s.label}
            aria-current={on ? "page" : undefined}
            onClick={(e) => {
              e.preventDefault();
              if (on) return;
              // Preserve the current surface (dashboard "" vs "/report") and the
              // selection params, so switching sectors keeps you on the same view.
              const prefix = `/${instance}`;
              const sub = window.location.pathname.startsWith(prefix) ? window.location.pathname.slice(prefix.length) : "";
              router.push(`/${s.instanceId}${sub}${window.location.search}`);
            }}
            onMouseEnter={(e) => { if (!on) (e.currentTarget as HTMLElement).style.color = "#cdd5e4"; }}
            onMouseLeave={(e) => { if (!on) (e.currentTarget as HTMLElement).style.color = "#5e6a83"; }}
            style={{ position: "relative", flex: "1 1 0", minWidth: 60, display: "flex", flexDirection: "column", alignItems: "center", gap: 6, padding: "4px 6px 9px", textDecoration: "none", color: on ? "#e8ecf4" : "#5e6a83", cursor: on ? "default" : "pointer", transition: "color .16s", WebkitTapHighlightColor: "transparent" }}
          >
            <span style={{ width: 19, height: 19, display: "flex", color: on ? activeAccent : "#5e6a83", transition: "color .16s" }}><Form /></span>
            <span style={{ fontFamily: MONO, fontSize: 8.5, fontWeight: 600, letterSpacing: ".07em", textTransform: "uppercase", whiteSpace: "nowrap" }}>{def.short}</span>
            {on && <span style={{ position: "absolute", left: "16%", right: "16%", bottom: -1, height: 2, background: activeAccent, borderRadius: 2 }} />}
          </a>
        );
      })}
    </div>
  );
}
