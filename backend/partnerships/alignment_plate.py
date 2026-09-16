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
