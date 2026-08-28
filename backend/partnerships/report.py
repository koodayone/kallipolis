"""L2b — the report adapter: a LensModel + an editorial Spec → report HTML.

This is the back half of the two-artifact architecture (see
[memory: project_artifact_architecture]). The DATA sections — regional demand,
the employer evidence, the program→occupation crosswalk — are generated straight
from L1 (`lens.build_lens`), so the report can never disagree with the dashboard
(principle #1). The WORDS — title, lede, the O*NET KSA grid, the live-posting
links — are editorial and live in the `ReportSpec` ("data is inherited, words are
authored"). KSA is here, not in L1, because it is not in the graph.

The output HTML follows the `tools/report-render/` CSS contract (`.title`,
`.subtitle`, `h1`, `p`, `table.dem`, `table.live`, `.xwrap` SVG, `.footer`), so
`build_docx.py` + `shoot_pdf.cjs` turn it into the editable .docx and the PDF.

    build_lens(member, play=…)  ─▶  LensModel ─┐
                                               ├─ build_report_html ─▶ HTML ─▶ harness ─▶ .docx/.pdf
    ReportSpec (editorial)  ───────────────────┘

The demand table and crosswalk are general over any N occupations. The KSA grid
(`table.cmpgrid`) renders only for a 3-occupation play — build_docx's cmpgrid is
3-column — and is skipped otherwise; it is optional editorial content regardless.
"""

from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass, field

from occupations.competencies import get_competencies
from ontology.regions import COE_REGION_DISPLAY, COE_REGION_TO_COUNTIES
from ontology.supply import COE_DEMAND_VINTAGE
from partnerships.lens import LensModel, LensOccupation, Play, build_lens

# Per-occupation accent palette (teal / blue / red / purple / amber), cycled.
_ACCENTS = ["#2a9d8f", "#2e74b5", "#cc3333", "#6f5499", "#c98a1b"]
# The demand rule. Amber, not red, for three measured reasons. (1) Red sits 9 degrees
# from Foothill's brand crimson in the band below it — amber is 49 degrees away, and the
# member band is the one thing the rule must never be confused with. (2) Green was the
# other candidate and fails: 24 degrees from #93bfb8 already in the band ramp, so it
# would read as another college's supply, and it wrongly connotes "target met" when
# supply usually sits BELOW this line. (3) Amber is the conventional threshold signal;
# red says "error", and a region under its openings line has a gap, not a fault.
# Hue 40 at 4.69:1 on white — a true yellow cannot be used here at all, because yellow's
# intrinsic luminance puts it at 1.40:1 and any yellow dark enough to clear 4.5:1 has
# turned olive (#7a7a00). 4.5:1 is the bar because the 10px bold label is not "large
# text". Greyscale value 0.44 against the navy bands' 0.22, so print separation holds.
_RULE = "#9e6900"

#: Chart plate sizes, (width, height). Width is 1:1 with the page's 648px content
#: column so nothing is downscaled. Height is the tuning knob for pagination: a page
#: holds 904px of content, so a chart plus its caption and table has to stay well under
#: that or the whole block jumps a page and leaves the remainder blank.
_SUPPLY_CHART = (648, 340)
_ENROLL_CHART = (648, 300)

_SEP = " · "        # status/date separator, hoisted: f-strings cannot hold escapes
_CAREERONESTOP = "https://www.careeronestop.org/Toolkit/Jobs/find-jobs-details.aspx?keyword="


# ── The editorial layer ───────────────────────────────────────────────────────
@dataclass(frozen=True)
class LivePosting:
    employer: str
    title: str
    url: str


@dataclass(frozen=True)
class CompetencyColumn:
    """O*NET KSA for one occupation — the cmpgrid column (editorial, O*NET-sourced)."""
    soc: str
    description: str
    knowledge: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)
    technology: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReportSpec:
    """The authored half of a report. The play + member identify the lens; the
    rest is prose/selection a human (or LLM draft) writes — never data."""
    org_name: str                                  # masthead partnership name
    org_short: str                                 # short name for the "All X programs" total
    lede: str                                      # the subtitle paragraph
    byline: str = ""                                # author · site · date line
    demand_note: str = ""                           # extra prose under the demand heading
    alignment_note: str = ""                        # extra prose under the alignment heading
    competency_note: str = ""
    award_note: str = ""
    enrollment_note: str = ""
    live_postings: dict[str, list[LivePosting]] = field(default_factory=dict)   # {soc -> [postings]}
    competencies: list[CompetencyColumn] = field(default_factory=list)    # {soc columns}
    # Editorial program selection for the crosswalk + trend tables: an ordered
    # list of (college, TOP6) the author curates as the representative pathway
    # programs. Empty → every data program that feeds the play (minus excludes).
    # "Data proposes (all feeders), the author confirms (this list)."
    programs: tuple[tuple[str, str], ...] = ()
    program_excludes: frozenset[str] = frozenset()
    # The TOP6 this report EVALUATES, e.g. "121000". Set only on program evaluations —
    # its presence is what marks a def an evaluation rather than a role report, and it
    # names the program in one field rather than two. Drives the "Awards Offered"
    # section; a role report leaves it empty and never enters that path.
    program_top: str = ""
    charter_gaps: tuple[str, ...] = ()              # charter members with no feeding program — the labeled gap
    dashboard_url: str = ""                          # the tailored dashboard link in Sources (def-overridable)
    extra_sources: list[str] = field(default_factory=list)


# ── Section builders (data from the lens, words from the spec) ─────────────────
def _block(*parts: str) -> str:
    """Group a heading, its intro and the visual it introduces into ONE unit that print
    keeps together.

    Page breaks were landing between a section heading and the thing it describes —
    "College Program Alignment & Supply" and its sentence stranded at the foot of a page
    with the crosswalk overleaf. Per-element `break-inside: avoid` could not fix that: it
    keeps each element whole but says nothing about keeping NEIGHBOURS together.

    Keep blocks small. An atomic block taller than the space left on a page jumps whole
    and leaves that space blank, so this trades sliced content for white space at exactly
    the rate the blocks are oversized — which is why the chart heights above are a
    parameter and why the competency grid is deliberately NOT blocked (it is taller than
    a page and could never be honoured).
    """
    inner = "\n".join(p for p in parts if p)
    return f'<div class="blk">{inner}</div>' if inner else ""


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _region_name(lens: LensModel) -> str:
    """The report's labor-market geography, named from the lens rather than assumed.

    This was the literal string "Bay Area" in every report, which silently misstated
    the geography of any non-Bay member. The COE region is the demand grain, so the
    lens scope is the authority."""
    regions = [r for r in (lens.scope.regions or ()) if r]
    if not regions:
        return "regional"
    return " and ".join(COE_REGION_DISPLAY.get(r, r) for r in regions)


def _demand_provenance(lens: LensModel) -> str:
    """The geography and vintage behind every demand figure, as a caption under the
    demand table — not inline in the prose, where a 12-county list wrecks the sentence.

    Counties make the region concrete for a reader who has to know whether their
    service area is in it. The vintage reuses ontology.supply.COE_DEMAND_VINTAGE,
    derived from the demand file's own header and already the provenance string the
    MCP surface reports, so the report cannot drift from the data or the other
    surfaces. COE publishes no GDP-growth assumption with these projections, so none
    is stated."""
    regions = [r for r in (lens.scope.regions or ()) if r]
    counties = [c for r in regions for c in COE_REGION_TO_COUNTIES.get(r, ())]
    parts = []
    if counties:
        parts.append(f"Covers the {_region_name(lens)} region — "
                     f"{', '.join(counties[:-1])}, and {counties[-1]} counties.")
    v = COE_DEMAND_VINTAGE
    parts.append(f"Figures are {v.split('—', 1)[1].strip()}." if "—" in v else f"Vintage: {v}.")
    return " ".join(parts)


def _short_college(name: str) -> str:
    """The crosswalk badge label: drop only a TRAILING ' College'.

    A bare `.replace(" College", "")` strips EVERY occurrence, which renames the three
    CCC colleges carrying ' College' mid-name — most visibly "City College of San
    Francisco" -> "City of San Francisco", i.e. the municipality rather than the college
    (also West Hills College Coalinga / Lemoore). Suffix-only is the intended shortening.
    """
    return name[: -len(" College")] if name.endswith(" College") else name


def _linkify(text: str) -> str:
    """Escape text, then convert [label](url) markdown links to <a> tags and
    **bold** markdown to <b> — lets the author embed trust-building links and
    emphasis in prose (the def's note/byline fields)."""
    import re as _re
    out, last = [], 0
    pat = _re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)|\*\*([^*]+)\*\*")
    for m in pat.finditer(text or ""):
        out.append(_esc(text[last:m.start()]))
        if m.group(1) is not None:
            out.append(f'<a href="{_esc(m.group(2))}" target="_blank" rel="noopener">'
                       f'{_esc(m.group(1))}</a>')
        else:
            out.append(f'<b>{_esc(m.group(3))}</b>')
        last = m.end()
    out.append(_esc(text[last:]))
    return "".join(out)


def _pct(x: float) -> str:
    return f"{'+' if x >= 0 else '−'}{abs(x) * 100:.1f}%"


def _demand_table(occs: list[LensOccupation]) -> str:
    rows = "".join(
        f'<tr><td>{_esc(o.soc)}</td><td>{_esc(o.title)}</td>'
        f'<td class="n">{o.annual_openings:,}</td>'
        f'<td class="n">{_pct(o.growth_rate)}</td>'
        f'<td class="n">${o.median_wage:,}</td></tr>'
        for o in occs
    )
    total = sum(o.annual_openings for o in occs)
    return (
        '<table class="dem"><tbody>'
        '<tr><th>SOC</th><th>Occupation</th><th class="n">Openings / yr</th>'
        '<th class="n">5-yr growth</th><th class="n">Median salary</th></tr>'
        f'{rows}'
        f'<tr class="tot"><td></td><td>Total regional demand</td>'
        f'<td class="n">≈ {total:,}</td><td class="n">—</td><td class="n">—</td></tr>'
        '</tbody></table>'
    )


def _employer_table(occs: list[LensOccupation], postings: dict[str, list[LivePosting]]) -> str:
    """The employer evidence: for each occupation, one OR MORE live postings from
    recognizable employers (editorial, from the spec) — the occupation cell spans its
    rows. Falls back to the L1 top firm (no link) when a SOC has no curated posting."""
    body = []
    for i, o in enumerate(occs):
        plist = postings.get(o.soc) or [None]   # [None] -> one fallback row
        acc = f"lc{(i % 3) + 1}"
        for j, post in enumerate(plist):
            cell = (f'<a target="_blank" rel="noopener" href="{_esc(post.url)}">{_esc(post.title)} ↗</a>'
                    if post else "—")
            # No posting -> no employer name. The old fallback printed the lens's top-ranked
            # regional hirer (BLS OEWS staffing patterns), which put two different claims in one
            # column — "this employer posted this job" beside "BLS says this employer hires this
            # occupation" — told apart only by a missing link. A blank row is the honest render of
            # a NONE verdict: the occupation is in scope, no posting evidence was found.
            emp = post.employer if post else "—"
            lsoc = (f'<td class="lsoc" rowspan="{len(plist)}">{_esc(o.title)}'
                    f'<span>SOC {_esc(o.soc)}</span></td>' if j == 0 else "")
            body.append(f'<tr class="{acc}">{lsoc}'
                        f'<td class="lemp">{_esc(emp)}</td>'
                        f'<td class="ltit">{cell}</td></tr>')
    return (
        '<table class="live"><colgroup><col style="width:40%"><col style="width:17%">'
        '<col style="width:43%"></colgroup><thead><tr>'
        '<th class="lsoc">Occupation</th><th>Employer</th><th>Live posting</th>'
        f'</tr></thead><tbody>{"".join(body)}</tbody></table>'
    )


def _competency_grid(cols: list[CompetencyColumn], occs) -> str:
    """The O*NET KSA grid, aligned by SHARING. Each KSA section is a union of its
    elements across the occupations: one row per DISTINCT element, the columns that
    hold it lined up horizontally and the rest blank — ordered most-shared → unique,
    so the shared core reads across the top rows and the distinctions fall below.
    Headers carry the occupation TITLE over the SOC code. Generalizes to N columns
    (1–4): equal-width via table-layout:fixed, header colors cycle the palette.
    build_docx's cmpgrid mirrors this (its column count is derived from the widest
    row); export.sh's verify_docx pass gates link parity so a docx-drift can't ship."""
    if not cols:
        return ""
    title = {o.soc: o.title for o in occs}
    hclass = ["c1h", "c2h", "c3h", "c4h"]

    # SINGLE SOC: transpose — full-width header + Description, then K/S/A/T as four
    # side-by-side columns (cross-occupation "align by sharing" is moot for one SOC).
    if len(cols) == 1:
        c = cols[0]
        ttl = _esc(title.get(c.soc, c.soc))
        onet = (f'<div class="onetlink"><a href="https://www.onetonline.org/link/summary/'
                f'{_esc(c.soc)}.00" target="_blank" rel="noopener">O*NET Occupation Summary</a></div>')
        ksat = [("Knowledge", c.knowledge), ("Skills", c.skills),
                ("Abilities", c.abilities), ("Technology", c.technology)]
        n = len(ksat)
        ksat_head = "".join(f"<td>{name}</td>" for name, _ in ksat)
        rows = "".join(
            "<tr>" + "".join(f'<td>{_esc(lst[i]) if i < len(lst) else ""}</td>' for _, lst in ksat) + "</tr>"
            for i in range(max((len(lst) for _, lst in ksat), default=0)))
        return (
            '<table class="cmpgrid"><colgroup><col><col><col><col></colgroup><tbody>'
            f'<tr><th class="c1h" colspan="{n}"><div class="ctitle">{ttl}</div>'
            f'<div class="ccode">SOC {_esc(c.soc)}</div></th></tr>'
            f'<tr class="sec"><td colspan="{n}">Description</td></tr>'
            f'<tr class="descrow"><td colspan="{n}">{_esc(c.description)}{onet}</td></tr>'
            f'<tr class="sec">{ksat_head}</tr>'
            f'{rows}'
            '</tbody></table>'
        )

    head = "".join(
        f'<th class="{hclass[i % len(hclass)]}"><div class="ctitle">{_esc(title.get(c.soc, c.soc))}</div>'
        f'<div class="ccode">SOC {_esc(c.soc)}</div></th>'
        for i, c in enumerate(cols)
    )

    def section(name, attr):
        lists = [getattr(c, attr) for c in cols]
        order, seen = [], set()
        for lst in lists:
            for el in lst:
                if el not in seen:
                    seen.add(el)
                    order.append(el)
        if not order:
            return ""
        present = {el: [el in lst for lst in lists] for el in order}
        first = {el: i for i, el in enumerate(order)}
        # shared-by-all first, then shared-by-two, then unique (stable on first-seen)
        order.sort(key=lambda el: (-sum(present[el]), first[el]))
        out = [f'<tr class="sec"><td colspan="{len(cols)}">{name}</td></tr>']
        for el in order:
            cells = "".join(f'<td>{_esc(el) if present[el][i] else ""}</td>' for i in range(len(cols)))
            out.append(f"<tr>{cells}</tr>")
        return "".join(out)

    desc = "".join(
        f'<td>{_esc(c.description)}'
        f'<div class="onetlink"><a href="https://www.onetonline.org/link/summary/{_esc(c.soc)}.00" '
        f'target="_blank" rel="noopener">O*NET Occupation Summary</a></div></td>'
        for c in cols)
    return (
        # The occupation header goes in a real <thead> so print's
        # `thead{display:table-header-group}` repeats it on every continuation page.
        # This grid is genuinely taller than a page, so it MUST split — and split
        # without headers the reader cannot tell which column is which occupation.
        '<table class="cmpgrid"><thead>'
        f'<tr>{head}</tr>'
        '</thead><tbody>'
        f'<tr class="sec"><td colspan="{len(cols)}">Description</td></tr>'
        f'<tr class="descrow">{desc}</tr>'
        f'{section("Knowledge", "knowledge")}'
        f'{section("Skills", "skills")}'
        f'{section("Abilities", "abilities")}'
        f'{section("Technology", "technology")}'
        '</tbody></table>'
    )


_DISPLAY_NAMES = None


def _program_display(college: str, top6: str):
    """The college's human-facing program name + verified URL for (college, top6),
    from program_display_names.json — or None to fall back to the state CIP name."""
    global _DISPLAY_NAMES
    if _DISPLAY_NAMES is None:
        import json
        from pathlib import Path
        try:
            path = Path(__file__).resolve().parent / "program_display_names.json"
            _DISPLAY_NAMES = json.loads(path.read_text()).get("names", {})
        except Exception:
            _DISPLAY_NAMES = {}
    return _DISPLAY_NAMES.get(f"{college}|{top6}")


def _awards_offered_section(college: str, top6: str) -> str:
    """"Awards Offered" — the credential menu for ONE program, from COCI.

    Answers the reviewer ask the rest of the report structurally cannot: every other
    award figure here is a CONFERRAL (DataMart — what was awarded), and the question was
    what the program OFFERS. The two genuinely differ. Foothill's Respiratory Care B.S.
    was approved 2024-05-30 and has conferred nothing inside our five-year window, so it
    appears nowhere else in the document.

    Program evaluations only. A role report argues need -> who is meeting it -> what we
    offer; opening with the college's own catalog inverts that. An evaluation's subject
    IS the program, so its menu belongs at the top. The trigger is the def's `program_top`.

    Unit counts come from the COLLEGE CATALOG, cached per award in
    program_display_names.json and cross-checked against a total or course sum on the
    page. NEVER from COCI's CERT UNITS / MAJOR UNITS: those are the figures as of
    APPROVAL and drift as programs are revised inside their band. Across Foothill's eight
    awards they matched the catalog 3 times, and the three that agreed are the three most
    recently approved — Respiratory Therapy's A.S. is 100 units on the catalog against
    COCI's 93, and its Interventional Pulmonology certificate is 12 against COCI's 16.
    Publishing COCI's number would contradict the catalog we link in the same sentence.

    The calendar word is not decoration. Foothill runs quarters (its terms are
    Fall/Winter/Spring and its associate minimum is 90 units, where a semester college
    requires 60) while this report's DataMart tier labels are semester-normalised, so an
    unqualified "12 units" beside "certificate, 8-16 semester units" would read as
    agreement when 12 quarter units IS 8 semester units.

    Where no verified figure is cached, falls back to COCI's approved BAND, which is
    calendar-explicit and stays true because leaving it forces re-approval.

    No status column and no approval date: the table already shows only what is on offer,
    so a column reading "Active" on every row, or a stamp saying when the state approved
    it, is metadata rather than answer. A teachout IS flagged — that is a caveat about
    availability, not metadata, and a credential closed to new students must never read
    as plainly on offer.
    """
    from ontology.coci import awards_for

    awards = awards_for(college, top6)
    if not awards:
        return ""
    disp = _program_display(college, top6)
    body = []
    curated = (disp or {}).get("award_units") or {}
    cal = (disp or {}).get("calendar") or ""
    for i, a in enumerate(awards):
        note = " (teaching out)" if a.is_teachout else ""
        # The catalog's exact figure when we have verified one; COCI's approved BAND
        # only as the fallback. COCI's own unit fields are never shown — they matched
        # the catalog in 3 of 8 Foothill awards, and the three that agreed are the
        # three most recently approved.
        n = curated.get(a.title)
        if n is not None:
            u = f"{n:g} {cal} units".replace("  ", " ").strip()
        else:
            u = a.band or "—"
        body.append(
            f'<tr class="lc{(i % 3) + 1}">'
            f'<td class="lsoc">{_esc(a.title)}{_esc(note)}</td>'
            f'<td class="lemp">{_esc(a.tier)}</td>'
            f'<td class="ltit">{_esc(u)}</td></tr>')
    link = "."
    if disp and disp.get("url"):
        link = (f', published on the '
                f'<a target="_blank" rel="noopener" href="{_esc(disp["url"])}">'
                f'{_esc(college)} catalog ↗</a>.')
    return _block(
        '<h1>Awards Offered</h1>'
        '<table class="live"><colgroup><col style="width:44%"><col style="width:22%">'
        '<col style="width:34%"></colgroup><thead><tr>'
        '<th class="lsoc">Award</th><th>Credential</th><th>Units</th>'
        f'</tr></thead><tbody>{"".join(body)}</tbody></table>'
        f'<p class="tnar">Approved awards under TOP {_esc(top6)} at {_esc(college)}. '
        f'Unit counts are the college\'s own requirements{link}</p>')


_BRAND_COLORS = None


def _brand_color(member_id: str) -> str:
    """The college's own color, from the SAME generator the atlas dashboard uses.

    `atlas/scripts/extract-college-colors.mjs` extracts a dominant colour per college
    logo and now writes two committed outputs: the .ts the atlas imports, and the JSON
    read here. The backend container does not ship atlas/, so it cannot read the .ts —
    one generator, two outputs, rather than a hand-maintained duplicate that drifts.

    Uses the LOGO-EXTRACTED base, not the COLOR_OVERRIDES in collegeAtlasConfigs.ts.
    Those are neon-lifted for the dark atlas UI — SchoolConfig.brandColorLight is
    documented as "readable accent on dark backgrounds" — and are too hot for white
    paper: Foothill is #b1122b here against #f0425a there.
    """
    global _BRAND_COLORS
    if _BRAND_COLORS is None:
        import json
        from pathlib import Path
        try:
            p = Path(__file__).resolve().parent / "college_colors.json"
            _BRAND_COLORS = json.loads(p.read_text()).get("colors", {})
        except Exception:
            _BRAND_COLORS = {}
    return _BRAND_COLORS.get(member_id, "")


def _crosswalk_svg(programs, occs: list[LensOccupation]) -> str:
    """College-grouped program→occupation funnel: one badge per partner college on the
    left — its human-facing program name (linked to the verified program page when known)
    over the state TOP/CIP label — the occupations on the right, an edge wherever a program
    feeds an occupation. Same program list as the trend tables: one coalition, two views.
    Badges ordered strongest-first (awards, then enrollment)."""
    socs = [o.soc for o in occs]
    accent = {soc: _ACCENTS[i % len(_ACCENTS)] for i, soc in enumerate(socs)}

    def tot(p):
        a = p.awards
        return sum(v for v in a.values() if v) if isinstance(a, dict) else (a or 0)

    def enr(p):
        e = p.enrollment
        return sum(v for v in e.values() if v) if isinstance(e, dict) else (e or 0)

    feed = sorted(programs, key=lambda p: (-tot(p), -enr(p)))

    def _wrap(text, width):
        words, lines, cur = (text or "").split(), [], ""
        for w in words:
            if cur and len(cur) + 1 + len(w) > width:
                lines.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines.append(cur)
        return lines or [""]

    LBOX_W, RBOX_W, BOXH, GAP, LINEH = 344, 254, 60, 13, 16
    # occupation boxes grow to fit their (wrapped, untruncated) titles
    wrapped = [_wrap(o.title, 30) for o in occs]
    OBOXH = max((len(w) for w in wrapped), default=1) * LINEH + 30
    left_h = len(feed) * (BOXH + GAP) - GAP
    right_h = len(socs) * (OBOXH + GAP) - GAP
    H = max(left_h, right_h, 1) + 30
    W = 744

    def col_y(col_h, bh, i):
        return (H - col_h) / 2 + i * (bh + GAP)

    parts = [f'<svg viewBox="0 0 {W} {H:.0f}" xmlns="http://www.w3.org/2000/svg" '
             'font-family="Helvetica,Arial,sans-serif">']

    lx, rx = 6 + LBOX_W, 478
    # edges first (behind boxes): college badge mid-right → occupation mid-left
    for fi, p in enumerate(feed):
        fy = col_y(left_h, BOXH, fi) + BOXH / 2
        for soc in p.socs:
            if soc not in socs:
                continue
            si = socs.index(soc)
            ry = col_y(right_h, OBOXH, si) + OBOXH / 2
            cx = (lx + rx) / 2
            parts.append(
                f'<path d="M {lx} {fy:.0f} C {cx:.0f} {fy:.0f}, {cx:.0f} {ry:.0f}, {rx} {ry:.0f}" '
                f'fill="none" stroke="{accent[soc]}" stroke-width="1.8" opacity="0.5"/>'
            )

    # left college badges — college, human-facing program name (linked), TOP · CIP
    for fi, p in enumerate(feed):
        y = col_y(left_h, BOXH, fi)
        disp = _program_display(p.college, p.top6)
        name = (disp.get("name") if disp else None) or p.program
        url = disp.get("url") if disp else None
        parts.append(
            f'<rect x="6" y="{y:.0f}" width="{LBOX_W}" height="{BOXH}" rx="6" '
            'fill="#f7f8fb" stroke="#d4dae6"/>'
            f'<text x="20" y="{y + 21:.0f}" font-size="14" font-weight="700" fill="#22304e">'
            f'{_esc(_short_college(p.college))}</text>'
        )
        # full program name — compress to the badge width only if it would overflow
        # (never truncate: the docx native-table crosswalk reads this text verbatim,
        # so a [:44] clip would cut the Word program link mid-word too).
        navail = LBOX_W - 28
        ntlen = (f' textLength="{navail}" lengthAdjust="spacingAndGlyphs"'
                 if len(name) * 12.5 * 0.56 > navail else "")
        if url:
            parts.append(
                f'<a href="{_esc(url)}" target="_blank" rel="noopener">'
                f'<text x="20" y="{y + 39:.0f}" font-size="12.5" fill="#2e6cb0" '
                f'text-decoration="underline"{ntlen}>{_esc(name)}</text></a>'
            )
        else:
            parts.append(
                f'<text x="20" y="{y + 39:.0f}" font-size="12.5" fill="#3a4a6b"{ntlen}>'
                f'{_esc(name)}</text>'
            )
        # full CIP — compress to the badge width only if it would overflow (never truncate / stretch)
        avail = LBOX_W - 28
        tlen = (f' textLength="{avail}" lengthAdjust="spacingAndGlyphs"'
                if (13 + len(p.program)) * 9.5 * 0.56 > avail else "")
        parts.append(
            f'<text x="20" y="{y + 53:.0f}" font-size="9.5" fill="#9aa1b2"{tlen}>'
            f'TOP {_esc(p.top6)} &#183; {_esc(p.program)}</text>'
        )

    # right occupation boxes — full title wrapped + vertically centered, no truncation
    for si, o in enumerate(occs):
        y = col_y(right_h, OBOXH, si)
        lines = wrapped[si]
        content_h = (len(lines) + 1) * LINEH
        ty = y + (OBOXH - content_h) / 2 + 12
        title_svg = "".join(
            f'<text x="{rx + 16}" y="{ty + j * LINEH:.0f}" font-size="13" font-weight="700" '
            f'fill="#fff">{_esc(ln)}</text>'
            for j, ln in enumerate(lines))
        parts.append(
            f'<rect x="{rx}" y="{y:.0f}" width="{RBOX_W}" height="{OBOXH}" rx="7" fill="{accent[o.soc]}"/>'
            f'{title_svg}'
            f'<text x="{rx + 16}" y="{ty + len(lines) * LINEH + 2:.0f}" font-size="11" '
            f'fill="#fff" opacity="0.92">SOC {_esc(o.soc)}</text>'
        )
    parts.append("</svg>")
    return f'<div class="xwrap">{"".join(parts)}</div>'


def _fmt_year(y: str) -> str:
    """'2024-2025' -> '2024–25' (the report's award-year display form)."""
    parts = y.split("-")
    return f"{parts[0]}–{parts[1][-2:]}" if len(parts) == 2 and len(parts[1]) >= 2 else y


# Supply palette: the member college in the strong navy, peers stepping down one
# navy→teal→grey family so the member reads first and the region reads as one mass.
# One ramp, never competing with the per-occupation _ACCENTS.
_BAND_FILL = ("#1f3864", "#2e74b5", "#4a90c4", "#7aa6d4", "#2a9d8f", "#93bfb8", "#c3cad6")


def _awards_demand_svg(programs, award_axis: list[str], annual_openings: int,
                       max_bands: int = 6, brand: str = "") -> str:
    """REGIONAL completions over time, stacked by college, against annual openings.

    The reviewer ask this answers: show the need to produce workers. The stack is one
    band per college in the report's supply scope (member at the bottom, in the strong
    fill); the dashed rule is the region's annual openings for the play's occupations.

    Why by COLLEGE and not by credential: the rule is a REGIONAL quantity, so the only
    coherent thing to compare it against is REGIONAL supply. Charting one college's
    completions under a regional demand line is a category error that reads as a
    dramatic shortfall regardless of the truth — Foothill's Manufacturing Technician
    is 17 completions against 410 openings (24x, alarming) while the region produces
    826 (0.5x, a surplus). Same data, opposite story. The member's share stays legible
    as the bottom band, which is the partnership argument anyway: how much of the
    region's answer is ours.

    Credential detail is NOT lost — it moved to where it reads better. Most members run
    one or two tiers, which is a weak stack but a perfectly good table, so the award
    trend table carries per-tier sub-rows beneath the member's total.

    NOTE the two sides have different vintages — the stack is DataMart actuals, the
    rule is a COE 2024-2029 projection — so the caption says so rather than implying
    one series predicts the other."""
    # Per-college series; a college may run several supporting programs in the play.
    by_college: dict[str, dict[str, int]] = {}
    members: set[str] = set()
    for p in programs:
        acc = by_college.setdefault(p.college, {})
        if p.is_member:
            members.add(p.college)
        for series in (getattr(p, "awards_by_tier", {}) or {}).values():
            for y, v in series.items():
                acc[y] = acc.get(y, 0) + (v or 0)
    by_college = {c: s for c, s in by_college.items() if sum(s.values()) > 0}
    if not by_college or not award_axis:
        return ""

    def _tot(c: str) -> int:
        return sum(by_college[c].get(y, 0) or 0 for y in award_axis)

    # Member(s) always shown and always at the bottom; peers by size. A 16-college
    # region cannot be 16 legible bands, so the tail rolls up — and the roll-up is
    # NAMED in the legend rather than silently dropped.
    mem = sorted((c for c in by_college if c in members), key=_tot, reverse=True)
    peers = sorted((c for c in by_college if c not in members), key=_tot, reverse=True)
    room = max(0, max_bands - len(mem))
    bands: list[tuple[str, dict[str, int]]] = [(c, by_college[c]) for c in mem + peers[:room]]
    rolled = peers[room:]
    if rolled:
        acc: dict[str, int] = {}
        for c in rolled:
            for y, v in by_college[c].items():
                acc[y] = acc.get(y, 0) + (v or 0)
        bands.append((f"{len(rolled)} other colleges", acc))

    totals = [sum(s.get(y, 0) or 0 for _, s in bands) for y in award_axis]
    barmax = max(totals, default=0)
    if barmax <= 0:
        return ""

    # Authored 1:1 with the page's 648px content width. At the old 744 the whole plate
    # was downscaled to fit, rendering every label 13% smaller than specified — the
    # chart is the report's central frame and was quietly the least legible thing on
    # the page. Taller too, for the same reason.
    (W, H), PADL, PADR, PADT, PADB = _SUPPLY_CHART, 60, 12, 44, 84
    plot_w, plot_h = W - PADL - PADR, H - PADT - PADB
    n = len(award_axis)

    def x_of(i: int) -> float:
        return PADL + (plot_w * i / (n - 1) if n > 1 else plot_w / 2)

    # A region's openings can still dwarf its supply (Veterinary Technology: 55 against
    # 1,130). Break the axis, but only when the ratio actually demands it, and DRAW the
    # break so the reader is never misled about the stack and the rule sharing a scale.
    # Three cases, not two. When the rule is far above the stack, break the axis. When
    # it is only modestly above, DON'T break — just raise the axis to include it, which
    # is the honest single scale. Scaling to the stack alone would push the rule off the
    # top of the viewBox, where it silently disappears (Respiratory Therapist: a 210
    # rule over a 138 axis rendered no rule at all).
    bar_top = barmax * 1.18
    broken = bool(annual_openings) and annual_openings > bar_top * 2.5
    top = bar_top if broken else max(bar_top, (annual_openings or 0) * 1.08)
    band_h = plot_h * (0.66 if broken else 1.0)
    break_y = PADT + plot_h - band_h - 9

    def y_of(v: float) -> float:
        return PADT + plot_h - (v / top) * band_h

    p_ = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
          'font-family="Helvetica,Arial,sans-serif">']

    # Title and axis labels carry what a caption used to say in prose. The two facts a
    # caption MUST carry for the chart to be honest — that the two series have different
    # vintages, and that the axis is broken — survive as the source line and the break
    # label, not a paragraph.
    p_.append(f'<text x="2" y="15" font-size="13" font-weight="700" fill="#12203a">'
              f'Regional supply against annual openings</text>')
    # Just the projection span from the vintage sentence — the full string is the demand
    # table's caption, too long for a chart corner. One authority, two altitudes.
    span = re.search(r"\d{4}[–-]\d{4}", COE_DEMAND_VINTAGE)
    src = f"DataMart actuals · COE {span.group()} projection" if span else "DataMart · COE"
    p_.append(f'<text x="{W}" y="15" font-size="9" fill="#8a93a5" text-anchor="end">'
              f'{_esc(src)}</text>')
    p_.append(f'<text x="15" y="{PADT + plot_h / 2:.1f}" font-size="10" fill="#5a6577" '
              f'text-anchor="middle" transform="rotate(-90 15 {PADT + plot_h / 2:.1f})">'
              f'Awards conferred a year</text>')
    p_.append(f'<text x="{PADL + plot_w / 2:.1f}" y="{H-PADB+32:.0f}" font-size="10" '
              f'fill="#5a6577" text-anchor="middle">Academic year</text>')

    for k in range(4):
        v = top * k / 3
        y = y_of(v)
        p_.append(f'<line x1="{PADL}" y1="{y:.1f}" x2="{W-PADR}" y2="{y:.1f}" stroke="#e7eaf1"/>')
        p_.append(f'<text x="{PADL-6}" y="{y+3.5:.1f}" font-size="9" fill="#8a93a5" '
                  f'text-anchor="end">{int(round(v)):,}</text>')

    lower = [0.0] * n
    for bi, (_name, s) in enumerate(bands):
        upper = [lower[i] + (s.get(y, 0) or 0) for i, y in enumerate(award_axis)]
        pts = " ".join(f"{x_of(i):.1f},{y_of(upper[i]):.1f}" for i in range(n))
        pts += " " + " ".join(f"{x_of(i):.1f},{y_of(lower[i]):.1f}" for i in range(n - 1, -1, -1))
        # The member owns the brand colour; peers step down the neutral ramp, so the
        # eye finds "us" in the stack before reading a single legend entry.
        fill = brand if (bi == 0 and brand and _name in members) else _BAND_FILL[bi % len(_BAND_FILL)]
        p_.append(f'<polygon points="{pts}" fill="{fill}" fill-opacity="0.94"/>')
        lower = upper

    # the regional total, drawn on top — the trend the chart exists to show
    tl = " ".join(f"{x_of(i):.1f},{y_of(totals[i]):.1f}" for i in range(n))
    p_.append(f'<polyline points="{tl}" fill="none" stroke="#0f1d33" stroke-width="1.8"/>')
    for i, t in enumerate(totals):
        anc = "start" if i == 0 else ("end" if i == n - 1 else "middle")
        dx = 3 if i == 0 else (-3 if i == n - 1 else 0)
        p_.append(f'<text x="{x_of(i)+dx:.1f}" y="{y_of(t)-6:.1f}" font-size="9.5" '
                  f'font-weight="700" fill="#0f1d33" text-anchor="{anc}">{int(t):,}</text>')
    for i, yr in enumerate(award_axis):
        anc = "start" if i == 0 else ("end" if i == n - 1 else "middle")
        p_.append(f'<text x="{x_of(i):.1f}" y="{H-PADB+15:.0f}" font-size="9.5" '
                  f'fill="#5a6577" text-anchor="{anc}">{_esc(_fmt_year(yr))}</text>')

    if annual_openings:
        if broken:
            # the break itself: a gap in the axis with the conventional double slash
            p_.append(f'<line x1="{PADL}" y1="{break_y:.1f}" x2="{W-PADR}" y2="{break_y:.1f}" '
                      'stroke="#ffffff" stroke-width="9"/>')
            for dx in (0, 6):
                p_.append(f'<line x1="{PADL-5+dx}" y1="{break_y+5:.1f}" x2="{PADL+2+dx}" '
                          f'y2="{break_y-5:.1f}" stroke="#8a93a5" stroke-width="1.2"/>')
            # name the break: the double slash is conventional but not universal, and an
            # unlabelled cut scale is the one way this chart could still mislead.
            p_.append(f'<text x="{PADL+12}" y="{break_y-3:.1f}" font-size="8.5" '
                      f'fill="#8a93a5">scale break</text>')
            dy = PADT + 12
        else:
            dy = y_of(annual_openings)
        p_.append(f'<line x1="{PADL}" y1="{dy:.1f}" x2="{W-PADR}" y2="{dy:.1f}" '
                  f'stroke="{_RULE}" stroke-width="1.6" stroke-dasharray="7 4"/>')
        # Park the label on the side with clearance. When supply has climbed past the
        # rule the stack owns the right-hand corner, and a right-anchored label lands on
        # top of the very crossing the chart exists to show.
        rise = totals[-1] > totals[0]
        lx_, anc_ = ((PADL + 4, "start") if rise else (W - PADR, "end"))
        p_.append(f'<text x="{lx_}" y="{dy-6:.1f}" font-size="10" font-weight="700" '
                  f'fill="{_RULE}" text-anchor="{anc_}">{annual_openings:,} openings a year</text>')

    # legend, wrapping onto a second row rather than running off the plate
    lx, ly = PADL, H - PADB + 42
    for bi, (name, _s) in enumerate(bands):
        w = 22 + 5.6 * len(name)
        if lx + w > W - PADR:
            lx, ly = PADL, ly + 13
        swatch = brand if (bi == 0 and brand and name in members) else _BAND_FILL[bi % len(_BAND_FILL)]
        p_.append(f'<rect x="{lx:.1f}" y="{ly}" width="9" height="9" fill="{swatch}"/>')
        p_.append(f'<text x="{lx+13:.1f}" y="{ly+8}" font-size="9" '
                  f'fill="#5a6577">{_esc(name)}</text>')
        lx += w
    p_.append('</svg>')
    return f'<div class="awchart">{"".join(p_)}</div>'


#: Instructional-core terms, in academic-year order. Summer is deliberately absent —
#: 7,150 programs report it against Fall's 12,260, it is irregular across colleges, and
#: a fourth column per year would not fit the plate.
_TERM_KINDS = ("Fall", "Winter", "Spring")
_ENROLL_YEARS = 3


def _term_axis(lens: LensModel) -> tuple[list[str], list[str]]:
    """The enrollment axis: (term keys, short headers) over the last complete academic years.

    Replaces a Fall-only axis. Fall census is the convention because Fall is Fall
    everywhere, but it assumes the term is present in the data AND that the program runs
    then, and both fail here. Foothill and De Anza — the two quarter colleges of one
    district — have NO Fall 2023 records at all, so the report rendered a "—" that read
    as an enrollment collapse; and Foothill's Community Health Worker program runs in
    WINTER only, so its own evaluation showed every peer's enrollment and none of its own.

    An academic year is Fall Y + Winter/Spring Y+1. Only complete years are shown: the
    pipeline effectively starts Fall 2021 (Fall 2020 reaches 5 colleges), and the current
    year is partial, so including either would compare unlike spans.
    """
    have = set(lens.enrollment_terms)
    years = sorted({int(t.split()[1]) - (0 if t.startswith("Fall") else 1)
                    for t in have if t.split()[0] in _TERM_KINDS})
    complete = [y for y in years
                if all(f"{k} {y if k == 'Fall' else y + 1}" in have for k in _TERM_KINDS)]
    keys, heads = [], []
    for y in complete[-_ENROLL_YEARS:]:
        for k in _TERM_KINDS:
            yy = y if k == "Fall" else y + 1
            keys.append(f"{k} {yy}")
            heads.append(f"{k[:3]} {str(yy)[2:]}")
    return keys, heads


def _enrollment_lines_svg(programs, term_keys: list[str], term_heads: list[str],
                          college_terms: dict, brand: str = "") -> str:
    """Enrollment over terms, ONE LINE PER COLLEGE. Deliberately not stacked.

    A stack is a visual total, and enrollment has no sound cross-college total when
    calendars differ — the same reason the trend table below carries none. Stacked, a
    Winter point would sum the one quarter college in the peer set while a Fall point
    sums all of them, and the silhouette would zigzag on calendar shape rather than on
    enrollment. Lines compare trajectories, which is what a trend is for.

    ONE rule for absence: skip the x-position and connect the neighbouring observations.
    Dots mark where a value actually exists, so the line is only ever a connector between
    real points — which is the standing contract of a line chart, since nothing is
    observed between Fall and Winter either.

    An earlier version broke the line at missing data (Foothill has no Fall 2023 record)
    and connected across terms a college does not have. That is two behaviours for two
    absences a reader cannot tell apart on sight, and the break read as a rendering
    defect rather than as a data gap. The gap stays disclosed where it is legible: the
    missing dot, the "—" cell in the table directly below, and the legend defining it.
    """
    if not programs or not term_keys:
        return ""
    n = len(term_keys)
    series = []
    for p in programs:
        vals = getattr(p, "enrollment", {}) or {}
        if not any(vals.get(k) for k in term_keys):
            continue
        series.append((p.college, vals))
    if not series:
        return ""
    # member first (brand colour, heavier stroke), then the largest peers
    member = [p.college for p in programs if p.is_member]
    series.sort(key=lambda cv: (cv[0] not in member,
                                -sum(cv[1].get(k, 0) or 0 for k in term_keys)))
    series = series[:6]
    top = max((v for _, vals in series for k in term_keys if (v := vals.get(k))), default=0)
    if top <= 0:
        return ""
    top *= 1.12

    (W, H), PADL, PADR, PADT, PADB = _ENROLL_CHART, 56, 12, 44, 96
    plot_w, plot_h = W - PADL - PADR, H - PADT - PADB
    x_of = lambda i: PADL + (plot_w * i / (n - 1) if n > 1 else plot_w / 2)
    y_of = lambda v: PADT + plot_h - (v / top) * plot_h

    p_ = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
          'font-family="Helvetica,Arial,sans-serif">']
    p_.append('<text x="2" y="15" font-size="13" font-weight="700" fill="#12203a">'
              'Enrollment by college</text>')
    p_.append(f'<text x="{W}" y="15" font-size="9" fill="#8a93a5" text-anchor="end">'
              'CCCCO DataMart · course section enrollments</text>')
    p_.append(f'<text x="13" y="{PADT + plot_h / 2:.1f}" font-size="10" fill="#5a6577" '
              f'text-anchor="middle" transform="rotate(-90 13 {PADT + plot_h / 2:.1f})">'
              f'Enrollments</text>')
    for k in range(4):
        v = top * k / 3
        y = y_of(v)
        p_.append(f'<line x1="{PADL}" y1="{y:.1f}" x2="{W-PADR}" y2="{y:.1f}" stroke="#e7eaf1"/>')
        p_.append(f'<text x="{PADL-6}" y="{y+3.5:.1f}" font-size="9" fill="#8a93a5" '
                  f'text-anchor="end">{int(round(v)):,}</text>')

    for si, (college, vals) in enumerate(series):
        colour = brand if (college in member and brand) else _BAND_FILL[(si + 1) % len(_BAND_FILL)]
        wide = college in member
        kinds = college_terms.get(college)
        pts_ = [(i, v) for i, key in enumerate(term_keys)
                if (v := vals.get(key) or 0)
                and not (kinds is not None and key.split()[0] not in kinds)]
        if len(pts_) > 1:
            path = " ".join(f"{x_of(i):.1f},{y_of(v):.1f}" for i, v in pts_)
            p_.append(f'<polyline points="{path}" fill="none" stroke="{colour}" '
                      f'stroke-width="{2.2 if wide else 1.5}" stroke-linejoin="round"/>')
        # A dot at every REAL observation, and only there. The line passes over ticks a
        # college has no term for and over any term it did not report, so the markers are
        # what tell a reader which x-positions carry a value.
        for i, v in pts_:
            p_.append(f'<circle cx="{x_of(i):.1f}" cy="{y_of(v):.1f}" '
                      f'r="{2.8 if wide else 2.2}" fill="{colour}"/>')

    # term ticks, then the academic year spanning its three terms
    for i, h in enumerate(term_heads):
        p_.append(f'<text x="{x_of(i):.1f}" y="{H-PADB+15:.0f}" font-size="9" '
                  f'fill="#5a6577" text-anchor="middle">{_esc(h.split()[0])}</text>')
    for g in range(0, n, len(_TERM_KINDS)):
        grp = list(range(g, min(g + len(_TERM_KINDS), n)))
        mid = (x_of(grp[0]) + x_of(grp[-1])) / 2
        yr = term_keys[grp[0]].split()[1]
        p_.append(f'<text x="{mid:.1f}" y="{H-PADB+31:.0f}" font-size="9.5" font-weight="700" '
                  f'fill="#46536b" text-anchor="middle">AY{yr[2:]}\u2013{str(int(yr)+1)[2:]}</text>')

    lx, ly = PADL, H - PADB + 46
    for si, (college, _v) in enumerate(series):
        colour = brand if (college in member and brand) else _BAND_FILL[(si + 1) % len(_BAND_FILL)]
        w = 26 + 5.6 * len(college)
        if lx + w > W - PADR:
            lx, ly = PADL, ly + 13
        p_.append(f'<line x1="{lx}" y1="{ly+4}" x2="{lx+14}" y2="{ly+4}" stroke="{colour}" '
                  f'stroke-width="{2.2 if college in member else 1.5}"/>')
        p_.append(f'<text x="{lx+18}" y="{ly+7}" font-size="9" fill="#5a6577">{_esc(college)}</text>')
        lx += w
    p_.append('</svg>')
    return f'<div class="enchart">{"".join(p_)}</div>'


def _trend_table(programs, axis: list[str], headers: list[str], value_attr: str,
                 total_label: str = "", college_terms: dict | None = None) -> str:
    """A `table.trend`: one row per (college, program), a value per axis key.

    Three cell states, deliberately distinct, because collapsing them states things that
    are not in evidence:
      value  the college reported this term
      n/a    the college has no such term at all — a semester college has no Winter
      —      the term exists for this college and the figure is absent or zero

    `total_label` empty renders NO total row. The enrollment table passes empty: summing
    enrollment across colleges on different calendars adds a quarter college's Fall to a
    semester college's Fall fine, but the Winter column would total one college and read
    as regional. Awards keep their total — a credential conferred in an academic year is
    the same unit at every college, calendar-independent.

    Column count is derived by build_docx from the header row, not fixed at 6."""
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    rows, totals = [], [0] * len(axis)
    for p in programs:
        series = getattr(p, value_attr)
        cells = []
        kinds = (college_terms or {}).get(p.college)
        for i, k in enumerate(axis):
            v = series.get(k) or 0
            totals[i] += v
            if not v and kinds is not None and k.split()[0] not in kinds:
                cells.append('<td class="num na">n/a</td>')      # no such term, not a gap
            else:
                cells.append('<td class="num zero">—</td>' if not v else f'<td class="num">{v:,}</td>')
        # Credential-mix sub-rows: the MEMBER college's award series decomposed by
        # tier, and only when there is more than one tier to show (a single-tier
        # program's breakdown just repeats its total). Peers keep one line each, so
        # the cross-college comparison and the regional total the table exists for
        # are untouched — the detail is spent on the college the report is about.
        tiers = getattr(p, "awards_by_tier", {}) if value_attr == "awards" else {}
        expand = p.is_member and len(tiers) > 1
        tr_open = '<tr class="sub">' if expand else "<tr>"
        rows.append(
            f'{tr_open}<td class="prog"><b>{_esc(p.college)}</b><br>'
            f'<span>TOP {_esc(p.top6)} · {_esc(p.program)}</span></td>{"".join(cells)}</tr>'
        )
        if expand:
            for tier, tseries in tiers.items():
                tcells = "".join(
                    '<td class="num zero">—</td>' if not (tv := tseries.get(k) or 0)
                    else f'<td class="num">{tv:,}</td>'
                    for k in axis
                )
                rows.append(
                    f'<tr class="tier"><td class="prog"><b>{_esc(tier)}</b></td>{tcells}</tr>'
                )
    tot = ""
    if total_label:
        cells_ = "".join('<td class="num zero">—</td>' if not t else f'<td class="num">{t:,}</td>'
                         for t in totals)
        tot = f'<tr class="tot"><td class="prog">{_esc(total_label)}</td>{cells_}</tr>'
    cols = '<col class="cprog">' + "<col>" * len(axis)
    return (
        f'<table class="trend"><colgroup>{cols}</colgroup>'
        f'<thead><tr><th class="prog">College · TOP code</th>{head}</tr></thead><tbody>'
        f'{"".join(rows)}{tot}</tbody></table>'
    )


def _footer(lens: LensModel, extra: list[str]) -> str:
    auth = "; ".join(f"{s.authority} ({s.role})" for s in lens.sources)
    extra_html = "".join(f"<div>{_esc(e)}</div>" for e in extra)
    return (
        f'<div class="footer"><b>Sources.</b> {_esc(auth)}.{extra_html}'
        '<div>Wages are regional occupational medians (demand-side), not graduate earnings.</div>'
        '</div>'
    )


def _sources_section(org_label: str, sector_label: str, dashboard_url: str,
                     title: str, socs: list[str], program_top: str = "") -> str:
    """Provenance, organized by report section: a tailored dashboard link, then one
    numbered, linked source group per section. Each section's claims trace to named,
    auditable sources — the same audit-trail logic as the clickable program names."""
    from urllib.parse import quote

    def a(label: str, url: str) -> str:
        return f'<a href="{_esc(url)}" target="_blank" rel="noopener">{_esc(label)}</a>'

    groups = []
    if program_top:
        # Undated on purpose: every other entry here is a named, linked authority, not a
        # snapshot stamp. The bundled export's vintage lives in ontology.coci.COCI_VINTAGE
        # for anyone auditing the data; the reader wants the system, not the file date.
        groups.append(("Awards Offered", [
            ("CCCCO Curriculum Inventory (COCI) — Approved Programs",
             "https://coci2.ccctechcenter.org/programs"),
        ]))
    groups += [
        ("Regional Occupational Demand", [
            (f'O*NET "{title}" Occupations Search Results',
             f"https://www.onetonline.org/find/quick?s={quote(title)}"),
            ("Centers of Excellence Occupational Demand Lookup",
             "https://datastudio.google.com/u/0/reporting/5060057c-b9ba-4081-9ed7-83356eaa7061"),
        ]),
        ("Occupational Competencies",
         [(f"O*NET Summary of {soc}", f"https://www.onetonline.org/link/summary/{soc}.00")
          for soc in socs]),
        ("College Program Alignment & Supply", [
            ("CCCCO DataMart — Program Awards",
             "https://datamart.cccco.edu/Outcomes/Program_Awards.aspx"),
            ("CCCCO DataMart — Credit Course Section Summary",
             "https://datamart.cccco.edu/Courses/Credit_Course_Summary.aspx"),
            ("CCCCO DataMart — Noncredit Course Section Summary",
             "https://datamart.cccco.edu/Courses/NCredit_Course_Summary.aspx"),
            ("Centers of Excellence TOP–CIP–SOC Crosswalk",
             "https://datastudio.google.com/u/0/reporting/62925aaa-3c91-48ab-941b-2473c0e17cb7"),
            ("RegionalCTE.org — TOP6 to Program Name Mappings",
             "https://regionalcte.org/browse"),
        ]),
    ]
    out = ['<h1 class="srcpage">Sources</h1>',
           f'<p class="srcdash"><i>{_esc(org_label)} {_esc(sector_label)} Dashboard:</i> '
           f'{a(dashboard_url, dashboard_url)}</p>']
    for name, links in groups:
        out.append(f'<p class="srcsec"><i>{_esc(name)} Section:</i></p>')
        out.append('<div class="srclist">' + "".join(
            f'<div class="srcitem">({i}) {a(lbl, url)}</div>'
            for i, (lbl, url) in enumerate(links, 1)) + "</div>")
    return "".join(out)


_CSS = """
*{box-sizing:border-box}
body{margin:0;background:#e9ebee;font-family:Calibri,"Segoe UI",Arial,sans-serif;color:#202124}
.page{width:816px;min-height:1056px;margin:28px auto;background:#fff;padding:76px 84px;box-shadow:0 4px 18px rgba(0,0,0,.18)}
.title{font-size:26px;font-weight:700;color:#1f3864;line-height:1.12;padding-bottom:7px;border-bottom:2px solid #2e74b5;white-space:nowrap}
.subtitle{font-size:12.5px;color:#3a3f47;margin-top:9px;line-height:1.5}
h1{font-size:15px;font-weight:700;color:#2e74b5;margin:18px 0 4px}
p{font-size:12.5px;line-height:1.5;margin:6px 0}
table{border-collapse:collapse;width:100%;margin:7px 0 3px;font-size:11.5px}
th{background:#4472c4;color:#fff;font-weight:600;text-align:left;padding:5px 9px}
td{border:1px solid #bfbfbf;padding:5px 9px;vertical-align:top}
.dem td.n,.dem th.n{text-align:right;white-space:nowrap}
tr.tot td{font-weight:700;background:#f3f6fb}
.live th{background:#eef1f6;color:#5a6577;font-size:8px;letter-spacing:.04em;text-transform:uppercase}
.live td{border:0;border-bottom:1px solid #eef1f6;vertical-align:middle}
.live .lsoc{font-weight:700;color:#2a3450}.live .lsoc span{display:block;font-size:7.5px;color:#9099ab}
.live tr.lc1 td.lsoc{border-left:4px solid #2a9d8f}.live tr.lc2 td.lsoc{border-left:4px solid #2e74b5}.live tr.lc3 td.lsoc{border-left:4px solid #cc3333}
.live .ltit a{color:#2e74b5;text-decoration:none}
.cmpgrid{table-layout:fixed}.cmpgrid th{font-size:10px}
.cmpgrid th.c1h{background:#2a9d8f}.cmpgrid th.c2h{background:#2e74b5}.cmpgrid th.c3h{background:#cc3333}.cmpgrid th.c4h{background:#7a5195}
.cmpgrid th{text-align:left;vertical-align:top;padding:6px 8px}
.cmpgrid th .ctitle{font-weight:700;font-size:10px;line-height:1.18;color:#fff}
.cmpgrid th .ccode{font-weight:400;font-size:8px;opacity:.85;margin-top:2px;color:#fff}
.cmpgrid td{font-size:10px}.cmpgrid tr.sec td{background:#eef1f6;font-weight:700;font-size:8px;letter-spacing:.06em;text-transform:uppercase;color:#5f6368}
.cmpgrid tr.descrow td{font-style:italic;color:#5f6368;font-size:11px;line-height:1.35}
.xwrap{margin:10px 0 4px}.xwrap svg{width:100%;height:auto;display:block}
.awchart{margin:12px 0 2px}.enchart{margin:12px 0 2px}.awchart svg{width:100%;height:auto;display:block}.enchart svg{width:100%;height:auto;display:block}
.cgap{font-size:11px;color:#7a5230;background:#fdf6ec;border-left:3px solid #e0a458;padding:7px 12px;margin:6px 0 2px;border-radius:0 4px 4px 0}.cgap b{color:#a8641a}
.srcdash{margin:4px 0 16px;font-size:13px}.srcsec{margin:16px 0 6px;font-size:13px}.srcdash i,.srcsec i{color:#222}
.srclist{margin:0}.srcitem{font-size:13px;line-height:1.55}.srcitem a,.srcdash a{color:#1155cc;text-decoration:underline}
.srcnote{font-size:11px;color:#777;margin-top:18px}
.descrow .onetlink{margin-top:8px}.descrow .onetlink a,.cmpgrid a{color:#1155cc;text-decoration:underline;font-size:11px;font-style:normal}
p a,.byline a{color:#1155cc;text-decoration:underline}
.trend{font-size:10px;table-layout:fixed}.trend col.cprog{width:230px}
.trend th,.trend td{border:1px solid #e7eaf1;padding:2px 4px;text-align:center;vertical-align:middle}
.trend thead th{background:#eef1f6;color:#5a6577;font-size:9px;font-weight:700}
.trend th.prog,.trend td.prog{text-align:left;padding-left:6px}
.trend td.prog b{font-size:10.5px;color:#2a3450}.trend td.prog span{color:#9099ab;font-size:8.5px}
.trend td.num{font-variant-numeric:tabular-nums;color:#33405a}.trend td.zero{color:#bcc3ce}.trend td.na{color:#ccd2db;font-style:italic}
.trend tr.tot td{background:#f2f6fc;font-weight:700;border-top:1.5px solid #c8d0de;color:#2a3450}
.trend tr.sub td{border-bottom:0}
.trend tr.tier td{border-top:0;background:#fbfcfe}
.trend tr.tier td.prog{padding-left:20px}
.trend tr.tier td.prog b{font-weight:400;font-size:9.5px;color:#66708a}
.trend tr.tier td.num{font-size:10px;color:#66708a}
.byline{font-size:11px;color:#70757c;margin:5px 0 0}
.tnar{font-size:11px;color:#46536b;margin:12px 0 3px;line-height:1.4}
.footer{margin-top:18px;padding-top:9px;border-top:1px solid #bfbfbf;font-size:9.5px;color:#5f6368;line-height:1.6;font-style:italic}
.footer b{font-style:normal;color:#202124}
/* Print: the body's grey is the on-screen "desk" the white .page floats on. The PDF
   harness renders with printBackground:true, so without resetting it here Chromium
   faithfully paints that grey wherever .page does not fill the sheet — a grey band
   below the content on the final page of every exported PDF. */
@media print{body{background:#fff}.page{margin:0;box-shadow:none;min-height:0}.awchart,.enchart,.xwrap{break-inside:avoid}.blk{break-inside:avoid}h1{break-after:avoid}table.dem,table.live,table.trend{break-inside:avoid}thead{display:table-header-group}tr{break-inside:avoid}h1.srcpage{break-before:page}}
"""


def _cols_from_bundle(occs: list[LensOccupation], n: int = 4) -> list[CompetencyColumn]:
    """The deterministic competency default: the top-N O*NET-pool elements per
    occupation (from occupations.competencies). The report-time curation skill
    refines this with role context and writes the result back as spec.competencies."""
    cols = []
    for o in occs:
        pool = get_competencies(o.soc)
        if not pool:
            continue
        desc = (o.description or "").split(". ")[0].strip()
        if desc and not desc.endswith("."):
            desc += "."
        cols.append(CompetencyColumn(
            soc=o.soc, description=desc,
            knowledge=pool.get("knowledge", [])[:n], skills=pool.get("skills", [])[:n],
            abilities=pool.get("abilities", [])[:n], technology=pool.get("technology", [])[:n]))
    return cols


# ── The proposer cascade: role (member + play) → a filled ReportSpec ──────────
def _org_label(member) -> str:
    """A masthead-friendly org name from the member identity."""
    if member.kind == "college":
        return member.name
    return member.name.upper() if len(member.name) <= 6 else member.name.title()


def _careeronestop_url(soc: str, zip_code: str = "94022") -> str:
    return f"{_CAREERONESTOP}{soc}.00&location={zip_code}&radius=25"


def propose_spec(member_id: str, play: Play, *, lens: LensModel | None = None,
                 author: str = "Kallipolis", date: str = "") -> ReportSpec:
    """Auto-fill a ReportSpec from the role (member + play) and L1 data — the
    proposer cascade. Everything downstream of the role selection is proposed:
    org/byline, the section prose, live-posting links (employer from L1, URL from
    the SOC pattern), the program selection (top program per college by supply),
    and the sources. The human confirms/edits; competencies fall through to the
    bundle default unless the curate-competencies skill fills spec.competencies."""
    lens = lens or build_lens(member_id, play=play)
    org = _org_label(lens.scope.member)
    title = play.title

    # Live postings: a DISTINCT top employer per occupation (related SOCs share a
    # staffing pattern, so the raw top is often the same firm 3×) + a CareerOneStop
    # link. Greedy: each occupation takes its highest-relevance firm not yet used.
    postings, used = {}, set()
    for o in lens.occupations:
        if not o.employers:
            continue
        pick = next((e for e in o.employers if e.name not in used), o.employers[0])
        used.add(pick.name)
        postings[o.soc] = [LivePosting(pick.name, title, _careeronestop_url(o.soc))]

    # Program selection: the highest-supply program per college that feeds the play
    # (one representative per college), ordered by supply.
    best: dict[str, tuple[int, tuple[str, str]]] = {}
    for p in lens.programs:
        supply = sum(p.awards.values()) + sum(p.enrollment.values())
        if p.college not in best or supply > best[p.college][0]:
            best[p.college] = (supply, (p.college, p.top6))
    programs = tuple(key for _, key in sorted(best.values(), key=lambda x: -x[0]))

    socs = [o.soc for o in lens.occupations]
    sources = [
        f'O*NET "{title}" occupations match (onetonline.org).',
        "O*NET summaries: " + ", ".join(socs) + " (onetonline.org).",
        "CCCCO DataMart: Program Awards, Credit & Non-Credit Course summaries.",
        "Centers of Excellence: occupational-demand lookup + TOP–CIP–SOC crosswalk.",
    ]

    byline = f"By {author} · [kallipolis.us](https://kallipolis.us/)"
    if date:
        byline += f" · {date}"
    # singular/plural-aware prose: a report may cover one SOC or several
    nsoc = len(play.socs)
    socn = ("this standard occupational classification" if nsoc == 1
            else "these standard occupational classifications")
    occref = f"the {title} role" if nsoc == 1 else "each occupation"
    occ_demands = "this occupation demands" if nsoc == 1 else "these occupations demand"
    total_openings = sum(o.annual_openings for o in lens.occupations)
    return ReportSpec(
        org_name=f"{org} Workforce Pathway",
        org_short=org,
        byline=byline,
        lede=f"This report examines how {org} member-college programs support the "
             f"{title} role and how it relates to meeting regional labor-market demand.",
        demand_note=f"The U.S. Department of Labor's O*NET system maps the title "
                    f"**{title}** to {socn}, supported by member-college programs. "
                    f"[According to the Centers of Excellence]"
                    f"(https://datastudio.google.com/u/0/reporting/5060057c-b9ba-4081-9ed7-83356eaa7061), "
                    f"{occ_demands} roughly **{total_openings:,} openings a year** in the "
                    f"{_region_name(lens)} labor market.",
        alignment_note=f"How member-college programs across the consortium support "
                       f"{occref}, derived from the TOP–CIP–SOC crosswalk published by "
                       f"the Centers of Excellence.",
        award_note="Award trends for each member-college program TOP code, "
                   "[per CCCCO DataMart](https://datamart.cccco.edu/Outcomes/Program_Awards.aspx)"
                   ". Empty cells indicate no data reported.",
        enrollment_note="Enrollment trends for each member-college program TOP code, "
                        "[per CCCCO DataMart](https://datamart.cccco.edu/Courses/Credit_Course_Summary.aspx)"
                        ".",
        live_postings=postings,
        programs=programs,
        extra_sources=sources,
    )


def report_slug(member: str, title: str) -> str:
    """The stable saved-report id for a (member, role) — the dialectic-surface URL key."""
    import re
    return re.sub(r"[^a-z0-9]+", "-", f"{member}-{title}".lower()).strip("-")


def scaffold_report_def(member: str, title: str, sector: str, socs, *,
                        partnership: str | None = None, author: str = "Kallipolis",
                        date: str = "", partner_min_awards: int = 50) -> dict:
    """The minimal draft report definition — the create-report scaffold and the one
    place the def schema is encoded.

    It carries only the IRREDUCIBLE intake: the PLAY (member / title / sector / socs),
    the partnership (charter + partner floor), and author/date. Everything downstream is
    *proposed, never required*: prose defaults (with trust links) come from propose_spec;
    the enrichments (`live_postings`, `competencies`) and the program-name cache are
    filled by the enrichment phase; hand-edits arrive via the dialectic surface and are
    consolidated back here. The def OVERRIDES propose_spec selectively — absent keys fall
    through to the proposed defaults, so a scaffold renders a complete (if un-curated)
    report immediately. This is the invariant: the def is the single source of truth, and
    nothing renders that isn't traceable to it or to the lens.

    Optional keys a curator adds later (documented, not scaffolded): dashboard_url,
    programs (explicit partner/​strategic override), lede + *_note prose overrides."""
    socs = [s for s in socs if s]
    if not (member and title and sector and socs):
        raise ValueError("scaffold needs member, title, sector, and at least one SOC")
    d: dict = {"member": member, "title": title, "sector": sector, "socs": list(socs),
               "author": author, "date": date}
    if partnership:
        d["partnership"] = partnership
        d["partner_min_awards"] = partner_min_awards
    return d


def select_partner_programs(programs, charter_colleges, min_awards: int = 50):
    """The partner-selection rule (SIZE ∪ CHARTER), at most ONE program per college.
    Each college is represented by its single STRONGEST relevant program (college ×
    TOP6), included if that program's 5-year award total clears the floor `min_awards`
    (SIZE) or the college is a charter member (CHARTER) — never its weaker secondaries.
    "Strongest" ranks by 5-yr awards THEN enrollment, so a charter member with missing
    award data but real enrollment (e.g. Evergreen Valley) is still carried by its
    enrollment. Strategic additions ride in via an explicit spec.programs override.
    Returns {(college, top6)}, one per college."""
    def aw(p):
        a = p.awards
        return sum(v for v in a.values() if v) if isinstance(a, dict) else (a or 0)
    def en(p):
        e = p.enrollment
        return sum(v for v in e.values() if v) if isinstance(e, dict) else (e or 0)
    strongest: dict = {}
    for p in programs:
        if aw(p) == 0 and en(p) == 0:
            continue                       # a truly empty program is no pipeline
        cur = strongest.get(p.college)
        if cur is None or (aw(p), en(p)) > (aw(cur), en(cur)):
            strongest[p.college] = p
    chosen = set()
    for college, best in strongest.items():
        if aw(best) >= min_awards or college in charter_colleges:
            chosen.add((best.college, best.top6))
    return chosen


def build_report_html(member_id: str, play: Play, spec: ReportSpec, *,
                      lens: LensModel | None = None) -> str:
    """Render a workforce-pathway report for `(member_id, play)` to HTML — DATA
    from L1, WORDS from `spec`. Output conforms to the report-render contract.
    Pass `lens` to reuse a build shared with `propose_spec`."""
    lens = lens or build_lens(member_id, play=play)
    occs = lens.occupations

    # keep the title on ONE line: shrink from 26px just enough to fit the 648px content
    # width (816 page − 2×84 padding); short titles stay at the full 26px.
    full_title = f"{spec.org_name} : {play.title}"
    tsize = min(26.0, 648 / (len(full_title) * 0.55))

    sections = [
        f'<div class="title" style="font-size:{tsize:.1f}px">{_esc(spec.org_name)} : {_esc(play.title)}</div>',
        f'<div class="byline">{_linkify(spec.byline)}</div>' if spec.byline else '',
        f'<div class="subtitle">{_esc(spec.lede)}</div>',
        # Program evaluations open with the program's own credential menu — the subject of
        # the document. Role reports leave `program_top` empty and this renders nothing.
        _awards_offered_section(lens.scope.member.name, spec.program_top) if spec.program_top else '',
        _block('<h1>Regional Occupational Demand</h1>',
               f'<p>{_linkify(spec.demand_note)}</p>' if spec.demand_note else '',
               _demand_table(occs),
               f'<p class="tnar">{_esc(_demand_provenance(lens))}</p>'),
        # No "under the <role> designation" clause: postings are found by SOC, not by the
        # role title or TOP, so naming the play here overstated what the search did — and it
        # read as role-report copy inside a program evaluation.
        _block('<h1>Employer Evidence</h1>',
               '<p>Prominent employers in the region have opened live job postings listed '
               'on CareerOneStop, sponsored by the U.S. Department of Labor.</p>',
               _employer_table(occs, spec.live_postings)),
    ]

    # Competencies: the Spec OVERRIDES (the curation skill's cut) if present;
    # otherwise we propose the deterministic O*NET-pool default from the bundle —
    # "data proposes, skill/human confirms." Ordered to match the occupation order.
    if spec.competencies:
        by_soc = {c.soc: c for c in spec.competencies}
        cols = [by_soc[o.soc] for o in occs if o.soc in by_soc]
    else:
        cols = _cols_from_bundle(occs)
    grid = _competency_grid(cols, occs)
    if grid:
        sections += ['<h1>Occupational Competencies</h1>',
                     f'<p>{_linkify(spec.competency_note)}</p>' if spec.competency_note else '', grid]

    # The coalition's programs — an editorial (college, TOP6) selection, else all
    # data programs minus excludes. ONE list drives the crosswalk AND the trends.
    by_key = {(p.college, p.top6): p for p in lens.programs}
    if spec.programs:
        progs = [by_key[k] for k in spec.programs if k in by_key]
    else:
        progs = [p for p in lens.programs if p.top6 not in spec.program_excludes]

    sections += [
        _block('<h1>College Program Alignment &amp; Supply</h1>',
               f'<p>{_linkify(spec.alignment_note)}</p>' if spec.alignment_note else
               '<p>How member-college programs across the consortium support each occupation.</p>',
               _crosswalk_svg(progs, occs)),
    ]
    if spec.charter_gaps:
        names = ", ".join(spec.charter_gaps)
        verb = "offers" if len(spec.charter_gaps) == 1 else "offer"
        sections.append(
            f'<p class="cgap"><b>Charter gap.</b> {_esc(names)} — a charter member of '
            f'the partnership — {verb} no program feeding these occupations, marking a '
            f'coordination opportunity for the consortium.</p>'
        )

    # Supply over time — same program list, from the L1 series.
    award_axis = lens.award_years[-5:]
    term_keys, term_heads = _term_axis(lens)
    total_label = "All College Programs"
    if progs and award_axis:
        # Branded only on program evaluations — a role report is not a college's own
        # document and keeps the neutral ramp.
        brand = _brand_color(lens.scope.member.id) if spec.program_top else ""
        chart = _awards_demand_svg(progs, award_axis,
                                   sum(o.annual_openings for o in occs), brand=brand)
        # No caption: the chart carries its own title, axis labels, source line and break
        # label, so a paragraph restating them is noise. Only the report's own curated
        # award_note stays — that is editorial, not chart chrome.
        sections += [
            _block(chart),
            _block(f'<p class="tnar">{_linkify(spec.award_note)}</p>' if spec.award_note else '',
                   _trend_table(progs, award_axis, [_fmt_year(y) for y in award_axis],
                                "awards", total_label)),
        ]
    if progs and term_keys:
        sections += [
            # Chart first: it carries its own title. The note and the legend belong to
            # the TABLE and sit with it, so neither reads as a caption for the chart.
            _block(_enrollment_lines_svg(progs, term_keys, term_heads, lens.college_terms,
                                         brand=_brand_color(lens.scope.member.id) if spec.program_top else "")),
            _block(f'<p class="tnar">{_linkify(spec.enrollment_note)}</p>' if spec.enrollment_note else '',
            # No total: see _trend_table. Enrollment across mixed calendars is not a
            # sound cross-college sum, and the old one silently dropped colleges with a
            # missing term — Veterinary Technology's Fall 2023 total read 411 (Santa Rosa
            # alone) against ~700 either side, a 47% regional collapse that never happened.
            # No cell-state legend: the headers name the terms, and "n/a" running down a
            # whole column for a semester college reads without being told. The states are
            # still visually distinct — n/a is lighter and italic — which is the part that
            # had to be true; the prose explaining it was a second layer.
                   _trend_table(progs, term_keys, term_heads, "enrollment",
                                college_terms=lens.college_terms)),
        ]
    from partnerships.sectors import SECTORS
    sec_label = SECTORS[play.sector].label if play.sector in SECTORS else play.sector.upper()
    dash_url = spec.dashboard_url or f"https://preview.kallipolis.us/landscape/{member_id}/{play.sector}"
    sections += [_sources_section(_org_label(lens.scope.member), sec_label, dash_url,
                                  play.title, [o.soc for o in occs], spec.program_top)]
    # NO brand colour in the document chrome. Tried three times at widening scope —
    # every heading, then the masthead rule and the Awards Offered accents — and reverted
    # each time for the same reason: colour already carries meaning in this report
    # (per-occupation accents, the amber demand rule), so a saturated brand hue in the
    # chrome competes rather than brands. It stays where it does work: the member's band
    # in the supply chart.
    body = "\n".join(s for s in sections if s)
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>{_esc(play.title)}</title><style>{_CSS}</style></head>'
        f'<body><div class="page" id="page">{body}</div></body></html>'
    )


# ── Demo: the whole report PROPOSED from just (member, play) ───────────────────
def _svamp_play() -> Play:
    """The role selection (step 1's output) for the SVAMP Manufacturing Technician
    report — O*NET's top-3 SOC matches for the title."""
    return Play(id="manufacturing-technician", title="Manufacturing Technician",
                sector="adm", socs=("17-3026", "51-9141", "17-3024"))


if __name__ == "__main__":
    member = sys.argv[1] if len(sys.argv) > 1 else "svamp"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/report.html"
    play = _svamp_play()
    # One lens build, shared by the proposer and the renderer.
    lens = build_lens(member, play=play)
    spec = propose_spec(member, play, lens=lens, author="Dayone Koo", date="June 21, 2026")
    html_doc = build_report_html(member, play, spec, lens=lens)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print(f"wrote {out} ({len(html_doc):,} bytes) — fully proposed from (member, play)")
