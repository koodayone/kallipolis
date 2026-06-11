"use client";

/* ── Industry platonic forms ────────────────────────────────────────────────
   One reduced geometric archetype per SWP priority industry — the demand-side
   analog of the lens forms (book/hard-hat/tower) and the surface forms
   (dashboard/report). Color answers state (active vs resting); SHAPE answers
   identity, so the eleven are told apart by form, never by an eleven-hue
   palette. Used by IndustryRail (the sector switcher) and keyed by the
   sectors.py sector id. 24-viewBox, 1.5 stroke, round joins — sized by the
   caller (~18px in the rail). `short` is the rail's terse label. */

import React from "react";

const Svg: React.FC<{ sw?: number; children: React.ReactNode }> = ({ sw = 1.5, children }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    {children}
  </svg>
);

export const INDUSTRY_FORMS: Record<string, { short: string; Form: React.FC }> = {
  // Advanced Manufacturing — machined nut / gear
  adm: { short: "Adv Mfg", Form: () => (<Svg><polygon points="12,4.2 18.8,8.1 18.8,15.9 12,19.8 5.2,15.9 5.2,8.1" /><circle cx="12" cy="12" r="2.7" /></Svg>) },
  // Life Sciences / Biotech — double helix
  biotech: { short: "Biotech", Form: () => (<Svg><path d="M9 4.5 Q15.5 8 9 12 Q2.5 16 9 19.5" /><path d="M15 4.5 Q8.5 8 15 12 Q21.5 16 15 19.5" /><path d="M9.6 6.4h4.8M8.4 12h7.2M9.6 17.6h4.8" /></Svg>) },
  // Health — care cross
  health: { short: "Health", Form: () => (<Svg sw={2.3}><path d="M12 5.5V18.5M5.5 12H18.5" /></Svg>) },
  // ICT / Digital Media — node network
  ict: { short: "ICT", Form: () => (<Svg><circle cx="12" cy="6.5" r="2" /><circle cx="6" cy="17" r="2" /><circle cx="18" cy="17" r="2" /><path d="M12 8.4 6.8 15.2M12 8.4 17.2 15.2M8 17h8" /></Svg>) },
  // Advanced Transportation & Logistics — motion chevrons
  atl: { short: "Transport", Form: () => (<Svg sw={1.7}><path d="M5.5 7 10.5 12 5.5 17M12 7 17 12 12 17" /></Svg>) },
  // Ag, Water & Environmental — leaf + vein
  agwet: { short: "Ag/Water", Form: () => (<Svg><path d="M6 18 C6 10.5 11.5 5 18 6 C18.5 13.5 13 19 6 18 Z" /><path d="M6.5 17.5 C10 14 14 10 17.5 6.5" /></Svg>) },
  // Business & Entrepreneurship — ascending bars
  business: { short: "Business", Form: () => (<Svg><rect x="5.5" y="14" width="3.4" height="4.5" rx="1" /><rect x="10.3" y="10" width="3.4" height="8.5" rx="1" /><rect x="15.1" y="5.8" width="3.4" height="12.7" rx="1" /></Svg>) },
  // Energy, Construction & Utilities — bolt
  ecu: { short: "Energy", Form: () => (<Svg><path d="M13.4 4 6.8 13H11.4L10.6 20 17.2 11H12.6Z" /></Svg>) },
  // Education & Human Development — open book
  edhd: { short: "Education", Form: () => (<Svg><path d="M12 7.2 C9.2 5.4 5.6 5.4 4 6.2 V17.8 C5.6 17 9.2 17 12 18.8 C14.8 17 18.4 17 20 17.8 V6.2 C18.4 5.4 14.8 5.4 12 7.2 Z" /><path d="M12 7.2V18.8" /></Svg>) },
  // Public Safety — shield
  public_safety: { short: "Safety", Form: () => (<Svg><path d="M12 3.8 19 6.8 V11.5 C19 15.8 16 19 12 20.8 C8 19 5 15.8 5 11.5 V6.8 Z" /></Svg>) },
  // Retail, Hospitality & Tourism — shopping bag
  retail: { short: "Retail", Form: () => (<Svg><path d="M6.5 8.5H17.5L18.6 19.2H5.4Z" /><path d="M9 8.5V6.6 A3 3 0 0 1 15 6.6 V8.5" /></Svg>) },
};
