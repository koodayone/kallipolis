"use client";

// /[collegeId]/partnerships now bounces to the college's single-college LANDSCAPE
// — the accordion + SOC-report view (PartnershipsView / OpportunityReport) is
// retired in favor of the member×sector landscape, which already serves every
// college (see PARTNERSHIPS-CONSOLIDATION-PLAN). Resolve collegeId → member_id by
// NAME (the frontend id and backend member_id diverge; memberIdForCollege joins on
// SchoolConfig.name == member_label), pick the member's flagship sector, and
// hard-navigate — window.location.replace re-enters through the _redirects shell
// (the generated /landscape/<member>/<sector> route isn't pre-rendered, so a
// client router.replace would 404 its RSC payload). Falls back to the college atlas
// home if the college has no landscape (shouldn't happen — all featured colleges resolve).

import { useEffect } from "react";
import { useParams } from "next/navigation";
import {
  fetchLandscapeIndex,
  memberIdForCollege,
  flagshipSectorFor,
} from "@/college-atlas/partnerships/landscapeIndex";

export default function PartnershipsRoute() {
  const { collegeId } = useParams<{ collegeId: string }>();

  useEffect(() => {
    let alive = true;
    fetchLandscapeIndex().then((idx) => {
      if (!alive) return;
      const member = memberIdForCollege(collegeId, idx);
      const sector = member ? flagshipSectorFor(member, idx) : null;
      window.location.replace(
        member && sector ? `/landscape/${member}/${sector}` : `/${collegeId}`,
      );
    });
    return () => {
      alive = false;
    };
  }, [collegeId]);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#060d1f",
        color: "#5e6a83",
        fontFamily: "monospace",
        fontSize: 13,
        letterSpacing: ".04em",
      }}
    >
      Loading…
    </div>
  );
}
