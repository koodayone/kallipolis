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
import sys
from dataclasses import dataclass, field

from occupations.competencies import get_competencies
from partnerships.lens import LensModel, LensOccupation, Play, build_lens

# Per-occupation accent palette (teal / blue / red / purple / amber), cycled.
_ACCENTS = ["#2a9d8f", "#2e74b5", "#cc3333", "#6f5499", "#c98a1b"]


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
    live_postings: dict[str, LivePosting] = field(default_factory=dict)   # {soc -> posting}
    competencies: list[CompetencyColumn] = field(default_factory=list)    # {soc columns}
    # Editorial program selection for the crosswalk + trend tables: an ordered
    # list of (college, TOP6) the author curates as the representative pathway
    # programs. Empty → every data program that feeds the play (minus excludes).
    # "Data proposes (all feeders), the author confirms (this list)."
    programs: tuple[tuple[str, str], ...] = ()
    program_excludes: frozenset[str] = frozenset()
    extra_sources: list[str] = field(default_factory=list)


# ── Section builders (data from the lens, words from the spec) ─────────────────
def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


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


def _employer_table(occs: list[LensOccupation], postings: dict[str, LivePosting]) -> str:
    """The employer evidence: the top relevant firm per occupation (from L1), with
    an optional editorial live-posting link (from the spec)."""
    body = []
    for i, o in enumerate(occs):
        top = o.employers[0].name if o.employers else "—"
        post = postings.get(o.soc)
        cell = (f'<a target="_blank" rel="noopener" href="{_esc(post.url)}">{_esc(post.title)} ↗</a>'
                if post else "—")
        emp = post.employer if post else top
        body.append(
            f'<tr class="lc{(i % 3) + 1}">'
            f'<td class="lsoc">{_esc(o.title)}<span>SOC {_esc(o.soc)}</span></td>'
            f'<td class="lemp">{_esc(emp)}</td>'
            f'<td class="ltit">{cell}</td></tr>'
        )
    return (
        '<table class="live"><colgroup><col style="width:40%"><col style="width:17%">'
        '<col style="width:43%"></colgroup><thead><tr>'
        '<th class="lsoc">Occupation</th><th>Employer</th><th>Live posting</th>'
        f'</tr></thead><tbody>{"".join(body)}</tbody></table>'
    )


def _competency_grid(cols: list[CompetencyColumn]) -> str:
    """The O*NET KSA grid. build_docx's cmpgrid is 3-column, so this renders only
    for a 3-occupation play; callers skip it otherwise."""
    if len(cols) != 3:
        return ""
    hclass = ["c1h", "c2h", "c3h"]
    head = "".join(
        f'<th class="{hclass[i]}">{_esc(c.soc)}</th>' for i, c in enumerate(cols)
    )

    def section(name, attr):
        depth = max(len(getattr(c, attr)) for c in cols)
        if not depth:
            return ""
        out = [f'<tr class="sec"><td colspan="3">{name}</td></tr>']
        for r in range(depth):
            cells = "".join(
                f'<td>{_esc(getattr(c, attr)[r]) if r < len(getattr(c, attr)) else ""}</td>'
                for c in cols
            )
            out.append(f"<tr>{cells}</tr>")
        return "".join(out)

    desc = "".join(f'<td>{_esc(c.description)}</td>' for c in cols)
    return (
        '<table class="cmpgrid"><tbody>'
        f'<tr>{head}</tr>'
        f'<tr class="sec"><td colspan="3">Description</td></tr>'
        f'<tr class="descrow">{desc}</tr>'
        f'{section("Knowledge", "knowledge")}'
        f'{section("Skills", "skills")}'
        f'{section("Abilities", "abilities")}'
        f'{section("Technology", "technology")}'
        '</tbody></table>'
    )


def _crosswalk_svg(programs, occs: list[LensOccupation]) -> str:
    """The program→occupation funnel: the selected programs on the left, the
    occupations on the right, an edge wherever a program feeds an occupation.
    Driven by the SAME program list as the trend tables — one coalition, two views."""
    socs = [o.soc for o in occs]
    accent = {soc: _ACCENTS[i % len(_ACCENTS)] for i, soc in enumerate(socs)}
    feed_list = list(programs)

    LBOX_W, RBOX_W, BOXH, GAP = 324, 254, 56, 16
    n = max(len(feed_list), len(socs), 1)
    H = 40 + n * (BOXH + GAP)
    W = 720

    def col_y(count, i):
        span = count * (BOXH + GAP) - GAP
        top = (H - span) / 2
        return top + i * (BOXH + GAP)

    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
             'font-family="Helvetica,Arial,sans-serif">']

    # edges first (behind boxes)
    lx = 6 + LBOX_W
    rx = 460
    for fi, p in enumerate(feed_list):
        fy = col_y(len(feed_list), fi) + BOXH / 2
        for soc in p.socs:
            if soc not in socs:
                continue
            si = socs.index(soc)
            ry = col_y(len(socs), si) + BOXH / 2
            cx = (lx + rx) / 2
            parts.append(
                f'<path d="M {lx} {fy:.0f} C {cx:.0f} {fy:.0f}, {cx:.0f} {ry:.0f}, {rx} {ry:.0f}" '
                f'fill="none" stroke="{accent[soc]}" stroke-width="1.8" opacity="0.5"/>'
            )

    # left program boxes
    for fi, p in enumerate(feed_list):
        y = col_y(len(feed_list), fi)
        parts.append(
            f'<rect x="6" y="{y:.0f}" width="{LBOX_W}" height="{BOXH}" rx="6" '
            'fill="#f7f8fb" stroke="#d4dae6"/>'
            f'<text x="20" y="{y + 20:.0f}" font-size="13.5" font-weight="700" fill="#2a3450">{_esc(p.college)}</text>'
            f'<text x="20" y="{y + 38:.0f}" font-size="11" fill="#5a6678">{_esc(p.program)}</text>'
            f'<text x="20" y="{y + 51:.0f}" font-size="9.5" fill="#9099ab">TOP {_esc(p.top6)}</text>'
        )

    # right occupation boxes
    for si, o in enumerate(occs):
        y = col_y(len(socs), si)
        parts.append(
            f'<rect x="{rx}" y="{y:.0f}" width="{RBOX_W}" height="{BOXH}" rx="7" fill="{accent[o.soc]}"/>'
            f'<text x="{rx + 16}" y="{y + 26:.0f}" font-size="13.5" font-weight="700" fill="#fff">{_esc(o.title[:30])}</text>'
            f'<text x="{rx + 16}" y="{y + 44:.0f}" font-size="11" fill="#fff" opacity="0.92">SOC {_esc(o.soc)}</text>'
        )
    parts.append("</svg>")
    return f'<div class="xwrap">{"".join(parts)}</div>'


def _fmt_year(y: str) -> str:
    """'2024-2025' -> '2024–25' (the report's award-year display form)."""
    parts = y.split("-")
    return f"{parts[0]}–{parts[1][-2:]}" if len(parts) == 2 and len(parts[1]) >= 2 else y


def _trend_table(programs, axis: list[str], headers: list[str], value_attr: str, total_label: str) -> str:
    """A `table.trend`: one row per (college, program), a value per axis key, a
    total row. Values come from the L1 program series; '—' marks no data/zero.
    Fixed to 5 value columns (+ label) to match build_docx's 6-column trend table."""
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    rows, totals = [], [0] * len(axis)
    for p in programs:
        series = getattr(p, value_attr)
        cells = []
        for i, k in enumerate(axis):
            v = series.get(k) or 0
            totals[i] += v
            cells.append('<td class="num zero">—</td>' if not v else f'<td class="num">{v:,}</td>')
        rows.append(
            f'<tr><td class="prog"><b>{_esc(p.college)}</b><br>'
            f'<span>TOP {_esc(p.top6)} · {_esc(p.program)}</span></td>{"".join(cells)}</tr>'
        )
    tot = "".join('<td class="num zero">—</td>' if not t else f'<td class="num">{t:,}</td>' for t in totals)
    return (
        '<table class="trend"><colgroup><col class="cprog"><col><col><col><col><col></colgroup>'
        f'<thead><tr><th class="prog">College · TOP code</th>{head}</tr></thead><tbody>'
        f'{"".join(rows)}'
        f'<tr class="tot"><td class="prog">{_esc(total_label)}</td>{tot}</tr>'
        '</tbody></table>'
    )


def _footer(lens: LensModel, extra: list[str]) -> str:
    auth = "; ".join(f"{s.authority} ({s.role})" for s in lens.sources)
    extra_html = "".join(f"<div>{_esc(e)}</div>" for e in extra)
    return (
        f'<div class="footer"><b>Sources.</b> {_esc(auth)}.{extra_html}'
        '<div>Wages are regional occupational medians (demand-side), not graduate earnings.</div>'
        '</div>'
    )


_CSS = """
*{box-sizing:border-box}
body{margin:0;background:#e9ebee;font-family:Calibri,"Segoe UI",Arial,sans-serif;color:#202124}
.page{width:816px;min-height:1056px;margin:28px auto;background:#fff;padding:76px 84px;box-shadow:0 4px 18px rgba(0,0,0,.18)}
.title{font-size:26px;font-weight:700;color:#1f3864;line-height:1.12;padding-bottom:7px;border-bottom:2px solid #2e74b5}
.subtitle{font-size:12.5px;color:#3a3f47;margin-top:9px;line-height:1.5}
h1{font-size:15px;font-weight:700;color:#2e74b5;margin:18px 0 4px}
p{font-size:12.5px;line-height:1.5;margin:6px 0}
table{border-collapse:collapse;width:100%;margin:7px 0 3px;font-size:11.5px}
th{background:#4472c4;color:#fff;font-weight:600;text-align:left;padding:5px 9px}
td{border:1px solid #bfbfbf;padding:5px 9px;vertical-align:top}
.dem td.n,.dem th.n{text-align:right;white-space:nowrap}
tr.tot td{font-weight:700;background:#f3f6fb}
.live th{background:#eef1f6;color:#5a6577;font-size:8px;letter-spacing:.04em;text-transform:uppercase}
.live td{border:0;border-bottom:1px solid #eef1f6}
.live .lsoc{font-weight:700;color:#2a3450}.live .lsoc span{display:block;font-size:7.5px;color:#9099ab}
.live tr.lc1 td:first-child{border-left:4px solid #2a9d8f}.live tr.lc2 td:first-child{border-left:4px solid #2e74b5}.live tr.lc3 td:first-child{border-left:4px solid #cc3333}
.live .ltit a{color:#2e74b5;text-decoration:none}
.cmpgrid{table-layout:fixed}.cmpgrid th{font-size:10px;width:33.33%}
.cmpgrid th.c1h{background:#2a9d8f}.cmpgrid th.c2h{background:#2e74b5}.cmpgrid th.c3h{background:#cc3333}
.cmpgrid td{font-size:10px}.cmpgrid tr.sec td{background:#eef1f6;font-weight:700;font-size:8px;letter-spacing:.06em;text-transform:uppercase;color:#5f6368}
.cmpgrid tr.descrow td{font-style:italic;color:#5f6368;font-size:9px}
.xwrap{margin:10px 0 4px}.xwrap svg{width:100%;height:auto;display:block}
.trend{font-size:10px;table-layout:fixed}.trend col.cprog{width:230px}
.trend th,.trend td{border:1px solid #e7eaf1;padding:2px 4px;text-align:center;vertical-align:middle}
.trend thead th{background:#eef1f6;color:#5a6577;font-size:9px;font-weight:700}
.trend th.prog,.trend td.prog{text-align:left;padding-left:6px}
.trend td.prog b{font-size:10.5px;color:#2a3450}.trend td.prog span{color:#9099ab;font-size:8.5px}
.trend td.num{font-variant-numeric:tabular-nums;color:#33405a}.trend td.zero{color:#bcc3ce}
.trend tr.tot td{background:#f2f6fc;font-weight:700;border-top:1.5px solid #c8d0de;color:#2a3450}
.byline{font-size:11px;color:#70757c;margin:5px 0 0}
.tnar{font-size:11px;color:#46536b;margin:12px 0 3px;line-height:1.4}
.footer{margin-top:18px;padding-top:9px;border-top:1px solid #bfbfbf;font-size:9.5px;color:#5f6368;line-height:1.6;font-style:italic}
.footer b{font-style:normal;color:#202124}
@media print{.page{margin:0;box-shadow:none}}
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


def build_report_html(member_id: str, play: Play, spec: ReportSpec) -> str:
    """Render a workforce-pathway report for `(member_id, play)` to HTML — DATA
    from L1, WORDS from `spec`. Output conforms to the report-render contract."""
    lens = build_lens(member_id, play=play)
    occs = lens.occupations

    sections = [
        f'<div class="title">{_esc(spec.org_name)} : {_esc(play.title)}</div>',
        f'<div class="byline">{_esc(spec.byline)}</div>' if spec.byline else '',
        f'<div class="subtitle">{_esc(spec.lede)}</div>',
        '<h1>Regional Occupational Demand</h1>',
        f'<p>{_esc(spec.demand_note)}</p>' if spec.demand_note else '',
        _demand_table(occs),
        '<h1>Employer Evidence</h1>',
        '<p>Regional employers whose industries most prominently hire for these '
        'occupations, ranked by BLS staffing-pattern relevance.</p>',
        _employer_table(occs, spec.live_postings),
    ]

    # Competencies: the Spec OVERRIDES (the curation skill's cut) if present;
    # otherwise we propose the deterministic O*NET-pool default from the bundle —
    # "data proposes, skill/human confirms." Ordered to match the occupation order.
    if spec.competencies:
        by_soc = {c.soc: c for c in spec.competencies}
        cols = [by_soc[o.soc] for o in occs if o.soc in by_soc]
    else:
        cols = _cols_from_bundle(occs)
    grid = _competency_grid(cols)
    if grid:
        sections += ['<h1>Occupational Competencies</h1>',
                     f'<p>{_esc(spec.competency_note)}</p>' if spec.competency_note else '', grid]

    # The coalition's programs — an editorial (college, TOP6) selection, else all
    # data programs minus excludes. ONE list drives the crosswalk AND the trends.
    by_key = {(p.college, p.top6): p for p in lens.programs}
    if spec.programs:
        progs = [by_key[k] for k in spec.programs if k in by_key]
    else:
        progs = [p for p in lens.programs if p.top6 not in spec.program_excludes]

    sections += [
        '<h1>College Program Alignment &amp; Supply</h1>',
        f'<p>{_esc(spec.alignment_note)}</p>' if spec.alignment_note else
        '<p>How member-college programs across the consortium feed each occupation.</p>',
        _crosswalk_svg(progs, occs),
    ]

    # Supply over time — same program list, from the L1 series.
    award_axis = lens.award_years[-5:]
    fall_terms = [t for t in lens.enrollment_terms if t.startswith("Fall")][-5:]
    total_label = f"All {spec.org_short} programs"
    if progs and award_axis:
        sections += [
            f'<p class="tnar">{_esc(spec.award_note)}</p>' if spec.award_note else '',
            _trend_table(progs, award_axis, [_fmt_year(y) for y in award_axis], "awards", total_label),
        ]
    if progs and fall_terms:
        sections += [
            f'<p class="tnar">{_esc(spec.enrollment_note)}</p>' if spec.enrollment_note else '',
            _trend_table(progs, fall_terms, fall_terms, "enrollment", total_label),
        ]
    sections += [_footer(lens, spec.extra_sources)]
    body = "\n".join(s for s in sections if s)
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>{_esc(play.title)}</title><style>{_CSS}</style></head>'
        f'<body><div class="page" id="page">{body}</div></body></html>'
    )


# ── Demo: regenerate the SVAMP Manufacturing Technician report from the graph ──
_CAREERONESTOP = "https://www.careeronestop.org/Toolkit/Jobs/find-jobs-details.aspx?keyword="


def _svamp_manufacturing_technician_spec() -> tuple[Play, ReportSpec]:
    """The editorial Spec for the SVAMP Manufacturing Technician report — the
    authored half (data comes from L1). KSA is O*NET; postings are CareerOneStop;
    the 095690 exclude is a curatorial choice (Digital Fabrication is off-pathway)."""
    play = Play(id="manufacturing-technician", title="Manufacturing Technician",
                sector="adm", socs=("17-3026", "51-9141", "17-3024"))
    spec = ReportSpec(
        org_name="SVAMP Workforce Pathway",
        org_short="SVAMP",
        byline="By Dayone Koo · kallipolis.us · June 19, 2026",
        lede="The Silicon Valley Advanced Manufacturing Partnership is committed to "
             "training students to fill critical roles in the region's advanced-"
             "manufacturing sector. This report examines how member colleges support "
             "the Manufacturing Technician role and how it relates to meeting regional "
             "labor market demand.",
        demand_note="The U.S. Department of Labor's O*NET system maps the title "
                    "Manufacturing Technician to three standard occupational "
                    "classifications supported by SVAMP college programs.",
        competency_note="The three occupations share a core set of competencies — "
                        "knowledge of production processes, proficiency with industrial "
                        "systems, and the ability to reason through complex technical "
                        "problems.",
        alignment_note="The visualization below illustrates how each SVAMP college "
                       "program supports the Manufacturing Technician role, derived from "
                       "the TOP–CIP–SOC crosswalk published by the Centers of Excellence.",
        award_note="Award trends for each SVAMP college program TOP code since 2020-21 "
                   "according to CCCCO DataMart. Empty cells indicate no data reported.",
        enrollment_note="Enrollment trends for each SVAMP college program TOP code "
                        "according to CCCCO DataMart. Empty cells indicate no data reported.",
        live_postings={
            "51-9141": LivePosting("Intel", "Mask Manufacturing Technician",
                                   f"{_CAREERONESTOP}51-9141.00&location=94022&radius=25"),
            "17-3026": LivePosting("Honeywell Aerospace", "Manufacturing Test Technician Level 1",
                                   f"{_CAREERONESTOP}17-3026.00&location=94022&radius=25"),
            "17-3024": LivePosting("Johnson & Johnson", "Manufacturing Tech III — Surgical Robotics",
                                   f"{_CAREERONESTOP}17-3024.00&location=94022&radius=25"),
        },
        # competencies omitted → the report proposes them from the O*NET bundle
        # (occupations.competencies); the curation skill overrides with the
        # role-resonant cut and writes them back as spec.competencies.
        # The five representative pathway programs (one per college), curated from
        # the data feeders — the same set drives the crosswalk and both trend tables.
        programs=(
            ("Foothill College", "094500"),
            ("Mission College", "093500"),
            ("Evergreen Valley College", "095600"),
            ("Ohlone College", "095600"),
            ("De Anza College", "095630"),
        ),
        extra_sources=[
            "O*NET \"Manufacturing Technician\" occupations match (onetonline.org).",
            "O*NET summaries: 17-3026, 51-9141, 17-3024 (onetonline.org).",
            "CCCCO DataMart: Program Awards, Credit & Non-Credit Course summaries.",
            "Centers of Excellence: occupational-demand lookup + TOP–CIP–SOC crosswalk.",
        ],
    )
    return play, spec


if __name__ == "__main__":
    member = sys.argv[1] if len(sys.argv) > 1 else "svamp"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/report.html"
    play, spec = _svamp_manufacturing_technician_spec()
    html_doc = build_report_html(member, play, spec)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print(f"wrote {out} ({len(html_doc):,} bytes)")
