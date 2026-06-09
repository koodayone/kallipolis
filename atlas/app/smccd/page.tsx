"use client";

import { useEffect } from "react";

// /smccd is retired as a standalone surface. SMCCD Advanced Manufacturing now
// lives at the sector-consistent /smccd-adm (the faithful 49-SOC sector view,
// replacing the earlier curated 12-SOC instance). Redirect there.
export default function SmccdRedirect() {
  useEffect(() => {
    window.location.replace("/smccd-adm");
  }, []);
  return null;
}
