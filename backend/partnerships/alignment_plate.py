"""The curriculum-alignment plate — one program, one occupation, one figure.

Rows are the occupation's core work activities in O*NET's order; columns are the
certificate's own outcomes and then its courses in catalog order. A solid mark means a
course's outcome or objective states the activity; a ring means the course's
description, content, lab or assignments involve it. The footer counts activities per
course; the right margin marks rows no course evidences. Static SVG in the report's
figure style (Helvetica, the report's occupation accents), no JavaScript: the report is
printed to PDF and .docx, so the evidence behind each mark lives in the appendix table
and the review file, not in a hover.
"""

from __future__ import annotations

from html import escape

from partnerships.alignment import PLO, SECTION_LABEL, Plate

#: The report's per-occupation accents (partnerships.report._ACCENTS) plus a fourth for
#: Machinists, which De Anza's plate pairs with. Keyed by SOC so a plate's colour follows
#: the occupation, not the column position.
_ACCENT = {"17-3026": "#2a9d8f", "51-9141": "#2e74b5", "17-3024": "#cc3333", "51-4041": "#7a5195"}
_SOFT = {"17-3026": "#d7efec", "51-9141": "#d9e6f5", "17-3024": "#f6dada", "51-4041": "#e3d7ea"}
_DEFAULT = ("#2e74b5", "#d9e6f5")
_FONT = 'font-family="Helvetica,Arial,sans-serif"'


def _mark(x: float, y: float, level: int, colour: str, soft: str) -> str:
    if level == 2:
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.2" fill="{colour}"/>'
    if level == 1:
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.3" fill="{soft}" stroke="{colour}" stroke-width="1.6"/>'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.5" fill="#d9dee8"/>'


def _clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip(" ,;") + "…"


def plate_svg(plate: Plate, *, width: int = 648) -> str:
    """The plate as an SVG sized to the report's content width."""
    colour, soft = _ACCENT.get(plate.paired_soc, _DEFAULT[0]), _SOFT.get(plate.paired_soc, _DEFAULT[1])
    cols = [{"code": PLO, "title": "Program outcomes"}] + [{"code": c["code"], "title": c["title"]} for c in plate.courses]
    LBL, ROW, HDR, PAD, RIGHT = 250, 18, 78, 4, 30
    cw = max(26, min(40, (width - PAD * 2 - LBL - RIGHT) / len(cols)))
    W = PAD * 2 + LBL + cw * len(cols) + RIGHT
    H = HDR + ROW * len(plate.rows) + 26
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H}" width="100%" role="img" '
           f'aria-label="{escape(plate.college)} courses against {escape(plate.occupation)} work activities" {_FONT}>']
    # column headers, rotated
    for i, c in enumerate(cols):
        cx = PAD + LBL + i * cw + cw / 2
        lab = "Program outcomes" if c["code"] == PLO else c["code"]
        out.append(f'<text transform="translate({cx + 3.5:.1f},{HDR - 6}) rotate(-52)" font-size="9.5" '
                   f'fill="{"#22304e" if c["code"] == PLO else "#3a4a6b"}" font-weight="{700 if c["code"] == PLO else 400}">{escape(lab)}</text>')
    totals = [0] * len(cols)
    for ri, r in enumerate(plate.rows):
        y = HDR + ri * ROW
        cy = y + ROW / 2
        if ri % 2 == 1:
            out.append(f'<rect x="{PAD}" y="{y}" width="{W - PAD * 2:.0f}" height="{ROW}" fill="#f3f6fb"/>')
        out.append(f'<text x="{PAD + 6}" y="{cy + 3.5:.1f}" font-size="10" fill="{"#3a3f47" if r.level else "#8a93a5"}">'
                   f'{escape(_clip(r.dwa.rstrip("."), 48))}</text>')
        for i, c in enumerate(cols):
            cell = r.cells.get(c["code"])
            lv = cell.level if cell else 0
            if lv:
                totals[i] += 1
            out.append(_mark(PAD + LBL + i * cw + cw / 2, cy, lv, colour, soft))
        if not r.level:
            out.append(f'<text x="{W - PAD - RIGHT / 2:.1f}" y="{cy + 3.5:.1f}" font-size="9" text-anchor="middle" '
                       f'fill="#a8641a" font-weight="700">gap</text>')
    fy = HDR + ROW * len(plate.rows)
    out.append(f'<line x1="{PAD + LBL}" y1="{fy + 1}" x2="{W - PAD - RIGHT:.0f}" y2="{fy + 1}" stroke="#d4dae6"/>')
    for i, t in enumerate(totals):
        cx = PAD + LBL + i * cw + cw / 2
        out.append(f'<text x="{cx:.1f}" y="{fy + 14}" font-size="9" text-anchor="middle" fill="{"#5a6577" if t else "#9aa1b2"}">{t or "·"}</text>')
    out.append(f'<text x="{PAD + LBL - 6}" y="{fy + 14}" font-size="8.5" text-anchor="end" fill="#8a93a5">activities per course</text>')
    out.append("</svg>")
    return "\n".join(out)


def plate_legend() -> str:
    return ('<p class="tnar"><span class="alg-solid">●</span> a course outcome or objective states the activity '
            '&nbsp; <span class="alg-ring">○</span> the course description, content, lab or assignments involve it '
            '&nbsp; · no evidence in the outline &nbsp; · rows in O*NET\'s order, most important first</p>')


def plate_readout(plate: Plate) -> str:
    """The sentence under the plate: counts, the courses that carry the most, the
    highest-ranked activities no course evidences."""
    c = plate.counts()
    load = sorted(((n, code) for code, n in c["per_course"].items() if n), reverse=True)[:2]
    gaps = [r.dwa.rstrip(".") for r in plate.rows if not r.level][:3]
    parts = [f"<b>{c['outcome_level']} of {c['activities']}</b> core work activities are stated in course outcomes or objectives; "
             f"{c['any_evidence'] - c['outcome_level']} more are involved in course content."]
    if load:
        parts.append("Carrying the most: " + ", ".join(f"{code} ({n})" for n, code in load) + ".")
    if gaps:
        parts.append("Not evidenced by any course: " + "; ".join(escape(g) for g in gaps) + ".")
    return f'<p class="tnar">{" ".join(parts)}</p>'


def evidence_table(plate: Plate, *, max_rows: int | None = None) -> str:
    """Appendix: every mark's sentence. Activity · course · section · quote."""
    rows = []
    for r in plate.rows:
        for code, cell in r.cells.items():
            for e in cell.evidence:
                rows.append(f'<tr><td>{escape(r.dwa.rstrip("."))}</td><td>{escape("Program outcomes" if code == PLO else code)}</td>'
                            f'<td>{escape(SECTION_LABEL.get(e.section, e.section))}</td><td>“{escape(e.quote)}”</td></tr>')
    if max_rows:
        rows = rows[:max_rows]
    return ('<table class="alg-ev"><thead><tr><th>Work activity</th><th>Course</th><th>Section</th><th>Outline text</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


# ── Occupation blocks: the consortium view ─────────────────────────────────────
# Five programs converge on three occupations, so the report reads by occupation: the
# ten most important core activities, each followed by the courses — from any member
# college — whose outlines evidence it, as chips in the college's colour. One chip style,
# one meaning: the course's outline evidences the activity. Whether that evidence is an
# outcome, an objective or lab content is real and kept — in the saved alignment and the
# appendix's section column — but it is not drawn: two chip styles read as two shades of
# one fact and cost the reader a legend. No chip: nothing in the consortium evidences it.
# The per-program plate above stays the view for a single college's own report.

#: Colleges whose logo-extracted brand colours sit too close on white paper to tell
#: apart at chip size: De Anza's navy (#1e3a5f) against Mission's blue (#0086ad), and
#: Evergreen Valley's green against Ohlone's. De Anza takes the report's amber accent;
#: Evergreen Valley keeps its own green, which is dark enough beside Ohlone's lighter one.
_COLLEGE_FALLBACK = {"deanza": "#c98a1b", "evc": "#1e894a"}
_COLOR_ALIAS = {"evc": "evergreen"}


def college_color(member_id: str) -> str:
    from partnerships.report import _brand_color
    if member_id in _COLLEGE_FALLBACK:
        return _COLLEGE_FALLBACK[member_id]
    return _brand_color(_COLOR_ALIAS.get(member_id, member_id)) or "#5a6577"


def _short(college: str) -> str:
    from partnerships.report import _short_college
    return _short_college(college)


def college_legend(plates: list[Plate]) -> str:
    seen, items = set(), []
    for pl in plates:
        if pl.member_id in seen:
            continue
        seen.add(pl.member_id)
        items.append(f'<span class="alg-lg"><i style="background:{college_color(pl.member_id)}"></i>{escape(_short(pl.college))}</span>')
    return ('<p class="tnar alg-legend">' + " ".join(items) +
            ' <span class="alg-lg"><b class="chip" style="--c:#5a6577">CODE</b> a course whose outline evidences the activity</span></p>')


def occupation_block(soc: str, plates: list[Plate], *, top_n: int = 10, college_order: list[str] | None = None) -> str:
    """One occupation: header, then a table — the top-N activities down the side, one
    column per connected college in a fixed consortium order, that college's evidencing
    courses stacked as chips in the cell. Position carries the college (the strong
    channel); colour repeats it. An empty cell is a quiet dash; only a row empty in every
    column gets the amber consortium-gap line."""
    if not plates:
        return ""
    order = college_order or []
    plates = sorted(plates, key=lambda p: (order.index(p.member_id) if p.member_id in order else 99, p.college))
    title = plates[0].occupation
    rows = plates[0].rows[:top_n]
    conn = "; ".join(f"{escape(_short(p.college))} ({'paired' if p.role == 'paired' else 'crosswalk'})" for p in plates)
    head = "".join(f'<th style="--c:{college_color(p.member_id)}"><span class="alg-colhd">{escape(_short(p.college))}</span>'
                   f'<span class="alg-colrole">{"paired" if p.role == "paired" else "crosswalk"}</span></th>' for p in plates)
    out = [f'<p class="chtitle">{escape(title)} <span class="alg-soc">SOC {escape(soc)}</span></p>',
           f'<p class="tnar alg-hd">Programs read against it: {conn}. The {len(rows)} most important core work activities, in O*NET\'s order.</p>',
           f'<table class="alg-tbl"><colgroup><col class="alg-actcol">{"".join("<col>" for _ in plates)}</colgroup>'
           f'<thead><tr><th class="alg-acthd">Work activity</th>{head}</tr></thead><tbody>']
    covered = 0
    per_college: dict[str, int] = {}
    uncovered = []
    for r in rows:
        cells, any_ = [], False
        for pl in plates:
            pr = next((x for x in pl.rows if x.dwa_id == r.dwa_id), None)
            codes = [code for code, cell in (pr.cells.items() if pr else []) if code != PLO]
            col = college_color(pl.member_id)
            if codes:
                any_ = True
                per_college[pl.college] = per_college.get(pl.college, 0) + len(codes)
                cells.append('<td><div class="alg-chips">' + "".join(
                    f'<b class="chip" style="--c:{col}" title="{escape(pl.college)} · {escape(c)}">{escape(c)}</b>' for c in codes) + "</div></td>")
            else:
                cells.append('<td class="alg-empty">—</td>')
        if any_:
            covered += 1
        else:
            uncovered.append(r.dwa.rstrip("."))
        act = escape(r.dwa.rstrip("."))
        if not any_:
            act += '<span class="alg-gap">no course in the consortium evidences this</span>'
        out.append(f'<tr class="{"alg-gaprow" if not any_ else ""}"><td class="alg-act">{act}</td>{"".join(cells)}</tr>')
    out.append("</tbody></table>")
    lead = sorted(per_college.items(), key=lambda kv: -kv[1])[:2]
    parts = [f"<b>{covered} of {len(rows)}</b> activities are evidenced by at least one course in the consortium."]
    if lead:
        parts.append("Most courses from " + " and ".join(f"{escape(_short(c))} ({n})" for c, n in lead) + ".")
    if uncovered:
        parts.append("Not evidenced by any college: " + "; ".join(escape(u) for u in uncovered) + ".")
    out.append(f'<p class="tnar">{" ".join(parts)}</p>')
    return "\n".join(out)


def appendix_tables(plates: list[Plate], *, top_n: int | None = None) -> str:
    """Evidence tables grouped by occupation then college. `top_n` limits each table to
    the rows the block shows (the compact print form)."""
    by_soc: dict[str, list[Plate]] = {}
    for pl in plates:
        by_soc.setdefault(pl.paired_soc, []).append(pl)
    out = []
    for soc, pls in by_soc.items():
        out.append(f'<p class="chtitle">{escape(pls[0].occupation)} <span class="alg-soc">SOC {escape(soc)}</span></p>')
        for pl in sorted(pls, key=lambda p: p.college):
            rows = []
            keep = {r.dwa_id for r in pl.rows[:top_n]} if top_n else None
            for r in pl.rows:
                if keep is not None and r.dwa_id not in keep:
                    continue
                for code, cell in r.cells.items():
                    for e in cell.evidence:
                        rows.append(f'<tr><td>{escape(r.dwa.rstrip("."))}</td><td>{escape("Program outcomes" if code == PLO else code)}</td>'
                                    f'<td>{escape(SECTION_LABEL.get(e.section, e.section))}</td><td>“{escape(e.quote)}”</td></tr>')
            if not rows:
                continue
            out.append(f'<p class="tnar alg-appx-h"><b>{escape(_short(pl.college))}</b> · {escape(pl.certificate)} · {pl.role}</p>')
            out.append('<table class="alg-ev"><thead><tr><th>Work activity</th><th>Course</th><th>Section</th><th>Outline text</th></tr></thead>'
                       f'<tbody>{"".join(rows)}</tbody></table>')
    return "\n".join(out)
