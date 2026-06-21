"""The role-selection workbench (step 1, validation-first).

Given a HYPOTHESIS role — (member, title, sector, SOCs) — evidence the five tests
that make a role well-chosen, so a human can JUDGE it before committing it to the
report generator. Data arms the judgment; it does not auto-select the role.

  1. Authoritative — S is O*NET's occupation-match for T. Treated here as the role
     definition's assertion (you bring SOCs from O*NET's title search); full
     auto-verification against onetonline is a later refinement.
  2. Desirable     — S are COE/SWP middle-skill priority occupations (L1 demand).
  3. Deliverable   — the member's programs supply S (L1 feeders).
  4. Attractive    — recognizable employers hire for S (L1 employers).
  5. Live          — current postings carry T. Agentic + browser-side: the
                     find-live-postings skill drives tools/jobs/scrape_jobs.cjs
                     (public CareerOneStop site, keyless — the gated Jobs API needs NLx).

Tests 2-4 are a projection of one build_lens (backend/data); test 5 is the
find-live-postings skill's job (a public scrape + the agentic title-match), which
the backend can't run in-container — so the workbench surfaces 1-4 and points to it.
"""

from __future__ import annotations

from partnerships.lens import Play, build_lens


def role_workbench(member_id: str, play: Play, *, zip_code: str = "94022", radius: int = 25) -> dict:
    """Five-test evidence for a hypothesis role. Returns a dict the CLI renders as a
    per-SOC scorecard; tests 2-4 from L1, test 5 from CareerOneStop (or pending)."""
    lens = build_lens(member_id, play=play)

    occs = []
    for o in lens.occupations:
        occs.append({
            "soc": o.soc, "title": o.title,
            "desirable": {"openings": o.annual_openings, "wage": o.median_wage,
                          "growth": round(o.growth_rate, 3)},
            "deliverable": [{"college": f.college, "top6": f.top6, "awards": f.awards,
                             "is_member": f.is_member} for f in o.feeders],
            "attractive": [e.name for e in o.employers[:5]],
            # Test 5 is agentic + browser-side (the find-live-postings skill drives
            # tools/jobs/scrape_jobs.cjs); the backend surfaces tests 1-4 and points to it.
            "live": f"node tools/jobs/scrape_jobs.cjs {o.soc} {zip_code} {radius} → find-live-postings skill",
        })
    return {
        "member": lens.scope.member.id, "title": play.title,
        "region": lens.scope.regions[0] if lens.scope.regions else None,
        "live_status": "test 5: run the find-live-postings skill (public CareerOneStop scrape)",
        "occupations": occs,
    }


def _scorecard(wb: dict) -> str:
    lines = [f"\nROLE: {wb['title']}   ({wb['member']} · {wb['region']})",
             f"  test 1 Authoritative: SOCs asserted as O*NET's match for the title",
             f"  live-postings: {wb['live_status']}\n"]
    for o in wb["occupations"]:
        d = o["desirable"]
        lines.append(f"  {o['soc']}  {o['title']}")
        lines.append(f"    2 Desirable    {d['openings']} openings/yr · ${d['wage']:,} · {d['growth'] * 100:+.1f}%")
        feeders = o["deliverable"]
        delv = ", ".join(f"{f['college'].split()[0]} (TOP {f['top6']}, {f['awards']})"
                         + ("*" if f["is_member"] else "") for f in feeders[:4]) or "— none"
        lines.append(f"    3 Deliverable  {delv}")
        lines.append(f"    4 Attractive   {', '.join(o['attractive']) or '— none'}")
        live = o["live"]
        if isinstance(live, list):
            shown = "; ".join(f"{x['employer']}: {x['title']}" for x in live[:3]) or "— NO POSTINGS (role weak here)"
            lines.append(f"    5 Live         {shown}")
        elif isinstance(live, dict):
            lines.append(f"    5 Live         [unavailable: {live.get('error', 'unknown')}]")
        else:
            lines.append(f"    5 Live         [{live}]")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    member = sys.argv[1] if len(sys.argv) > 1 else "svamp"
    title = sys.argv[2] if len(sys.argv) > 2 else "Manufacturing Technician"
    sector = sys.argv[3] if len(sys.argv) > 3 else "adm"
    socs = tuple((sys.argv[4] if len(sys.argv) > 4 else "17-3026,51-9141,17-3024").split(","))
    play = Play(id=title.lower().replace(" ", "-"), title=title, sector=sector, socs=socs)
    print(_scorecard(role_workbench(member, play)))
