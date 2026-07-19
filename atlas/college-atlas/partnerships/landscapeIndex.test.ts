/**
 * Tests for memberIdForCollegeName — the name-join that resolves a college to its
 * single-college landscape member, used to redirect /[collegeId]/partnerships →
 * /landscape/<member>.
 *
 * The join is load-bearing for correctness, not just convenience: the frontend
 * collegeId and the backend member_id diverge (sandiegomesa→sdmesa), and a fuzzy
 * id match collapses San Diego Mesa/Miramar/City onto one member — silently
 * routing a college's partnerships page to a DIFFERENT college's landscape. The
 * name-join (SchoolConfig.name == backend member_label) is exact and safe; this
 * pins that safety.
 *
 * Coverage:
 *   - exact label match resolves to the member_id
 *   - the `+ " College"` suffix fallback (config names that omit the suffix the
 *     backend label carries, e.g. "Los Angeles Trade-Technical")
 *   - Mesa / Miramar / City resolve to DISTINCT members (the fuzzy-unsafe case)
 *   - college-kind only: a name matching a district/consortium label never resolves
 *   - null when the college has no landscape entry
 *
 * Also covers flagshipSectorFor — the landing-sector pick shared by MemberRedirect
 * and the /[collegeId]/partnerships redirect:
 *   - highest-priority live sector wins (adm before health/retail)
 *   - priority order respected when adm absent (ict before health)
 *   - null when the member has no live sectors
 */
import { describe, it, expect } from "vitest";
import { memberIdForCollegeName, flagshipSectorFor, type LandscapeIndexEntry } from "./landscapeIndex";

function entry(p: Partial<LandscapeIndexEntry>): LandscapeIndexEntry {
  return {
    id: "x-adm", member_id: "x", member_label: "X", member_kind: "college",
    colleges: ["x"], sector_id: "adm", sector_label: "Advanced Manufacturing",
    accent: "#000", region: "Bay", ...p,
  };
}

const INDEX: LandscapeIndexEntry[] = [
  entry({ member_id: "sdmesa", member_label: "San Diego Mesa College" }),
  entry({ member_id: "sdmiramar", member_label: "San Diego Miramar College" }),
  entry({ member_id: "sandiegocity", member_label: "San Diego City College" }),
  entry({ member_id: "lattc", member_label: "Los Angeles Trade-Technical College" }),
  // a district whose label could otherwise be name-matched — must be ignored
  entry({ member_id: "smccd", member_label: "San Mateo County CCD", member_kind: "district" }),
];

describe("memberIdForCollegeName", () => {
  it("resolves an exact label match", () => {
    expect(memberIdForCollegeName("San Diego Mesa College", INDEX)).toBe("sdmesa");
  });

  it("falls back to a `+ College` suffix when the config name omits it", () => {
    expect(memberIdForCollegeName("Los Angeles Trade-Technical", INDEX)).toBe("lattc");
  });

  it("keeps Mesa / Miramar / City distinct (the fuzzy-unsafe case)", () => {
    expect(memberIdForCollegeName("San Diego Mesa College", INDEX)).toBe("sdmesa");
    expect(memberIdForCollegeName("San Diego Miramar College", INDEX)).toBe("sdmiramar");
    expect(memberIdForCollegeName("San Diego City College", INDEX)).toBe("sandiegocity");
  });

  it("never resolves to a district/consortium (college-kind only)", () => {
    expect(memberIdForCollegeName("San Mateo County CCD", INDEX)).toBeNull();
  });

  it("returns null when no college landscape exists for the name", () => {
    expect(memberIdForCollegeName("Nonexistent College", INDEX)).toBeNull();
  });
});

describe("flagshipSectorFor", () => {
  const sectorsFor = (memberId: string, sids: string[]): LandscapeIndexEntry[] =>
    sids.map((s) => entry({ member_id: memberId, sector_id: s }));

  it("picks the highest-priority live sector (adm before health/retail)", () => {
    expect(flagshipSectorFor("m", sectorsFor("m", ["retail", "health", "adm"]))).toBe("adm");
  });

  it("respects priority order when adm is absent (ict before health)", () => {
    expect(flagshipSectorFor("m", sectorsFor("m", ["health", "ict", "retail"]))).toBe("ict");
  });

  it("returns null when the member has no live sectors", () => {
    expect(flagshipSectorFor("absent", sectorsFor("m", ["adm"]))).toBeNull();
  });
});
