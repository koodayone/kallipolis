"use client";

// Member-root landing: /landscape/<member> (no sector) opens the member's view
// on its flagship sector, where the industry rail takes over for switching —
// mirroring how /smccd redirects to /smccd-adm. The default sector is the first
// one the member is actually live in, in priority order (the CTE-core /
// tech-forward industries first), resolved from the landscape index. Falls back
// to the State Atlas for an unknown member.

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchLandscapeIndex } from "@/college-atlas/partnerships/landscapeIndex";

// Flagship-first: land on Advanced Manufacturing where present, then the other
// priority sectors, before the broader-access industries.
const DEFAULT_SECTOR_PRIORITY = [
  "adm", "biotech", "ecu", "atl", "ict", "health", "business", "public_safety", "edhd", "agwet", "retail",
];

export default function MemberRedirect() {
  const params = useParams<{ member: string }>();
  const member = (params?.member as string) ?? "";
  const router = useRouter();

  useEffect(() => {
    if (!member) return;
    let alive = true;
    fetchLandscapeIndex().then((idx) => {
      if (!alive) return;
      const live = new Set(idx.filter((e) => e.member_id === member).map((e) => e.sector_id));
      const target = DEFAULT_SECTOR_PRIORITY.find((s) => live.has(s)) ?? [...live][0];
      router.replace(target ? `/landscape/${member}/${target}${window.location.search}` : "/");
    });
    return () => { alive = false; };
  }, [member, router]);

  return (
    <div style={{ position: "fixed", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", color: "#5e6a83", fontFamily: "monospace", fontSize: 13, letterSpacing: ".04em" }}>
      Loading…
    </div>
  );
}
