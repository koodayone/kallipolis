"""The Curriculum Alignment section's blocks — one occupation, its work activities down the
side, one column per program the roster connects, the evidencing courses in the cells.

Two column kinds. A consortium roster names its columns by COLLEGE: up to three course
chips per cell in the college's colour, so position and colour together say who teaches
the activity. An evaluation roster names its columns by CERTIFICATE (one college): the cell
is the LEAD excerpt — the one course sentence a reviewer would point to first
(alignment.lead_for) — with the course's title and the section of the outline it comes from,
a rule down its left in the tier's shade. Every chip links to the course's outline of record.

Colour: a college's brand colour from partnerships.report, with two fallbacks where brands
collide (partnerships/college_colors.json). No occupation accent, no tier drawn as fill.
"""

from __future__ import annotations

from html import escape

from partnerships.alignment import LEVEL, PLO, SECTION_LABEL, Plate, lead_for


#: Evergreen Valley's green against Ohlone's. De Anza takes the report's amber accent;
#: Evergreen Valley keeps its own green, which is dark enough beside Ohlone's lighter one.
_COLLEGE_FALLBACK = {"deanza": "#c98a1b", "evc": "#1e894a"}
_COLOR_ALIAS = {"evc": "evergreen", "sdmesa": "sandiegomesa"}


def college_color(member_id: str) -> str:
    from partnerships.report import _brand_color
    if member_id in _COLLEGE_FALLBACK:
        return _COLLEGE_FALLBACK[member_id]
    return _brand_color(_COLOR_ALIAS.get(member_id, member_id)) or "#5a6577"


def _short(college: str) -> str:
    from partnerships.report import _short_college
    return _short_college(college)


def _col_label(pl: Plate, columns: str, *, multi: bool = False) -> str:
    """What a column is called: the college (a consortium roster, one program per college)
    or the certificate (an evaluation roster, one college's programs side by side). When
    certificate columns span more than one college (an evaluation reading other colleges'
    programs), the college is prefixed so two same-named degrees stay apart."""
    if columns == "college":
        return _short(pl.college)
    label = pl.short_title or pl.certificate
    return f"{_short(pl.college)} · {label}" if multi else label


def _multi_college(plates: list[Plate]) -> bool:
    return len({p.college for p in plates}) > 1


def column_legend(plates: list[Plate], columns: str = "college") -> str:
    seen, items = set(), []
    multi = _multi_college(plates)
    for pl in plates:
        label = _col_label(pl, columns, multi=multi)
        if label in seen:
            continue
        seen.add(label)
        items.append(f'<span class="alg-lg"><i style="background:{college_color(pl.member_id)}"></i>{escape(label)}</span>')
    tail = (f' <span class="alg-lg alg-lgnote">{COR_LEGEND}</span>' if columns == "certificate" else "")
    return ('<p class="tnar alg-legend">' + " ".join(items) +
            ' <span class="alg-lg"><b class="chip" style="--c:#5a6577">CODE</b> a course whose outline evidences the activity</span>'
            f'{tail}</p>')


#: Courses shown per cell. Ranked by the evidence tier the page no longer draws — an
#: outcome or objective that states the activity outranks content that involves it — then
#: by the certificate's catalog order; the rest fold into a neutral "+N" chip. Three answers
#: "does this college teach it, and where"; the rest is height.
CHIPS_PER_CELL = 3
#: The section of the Course Outline of Record a lead excerpt comes from, as the tag reads it.
COR_TAG = {"outcomes": "Student learning outcome", "objectives": "Course objective", "description": "Course description",
           "content": "Course content", "lab": "Lab content", "assignments": "Course assignment"}
COR_LEGEND = "The caption above each excerpt names the section of the course outline of record it comes from."


def block_key(colour: str = "#5a6577") -> str:
    """The one-line key under a certificate-column block: what a chip is. The college swatch
    is left out (the column header names the certificate a few lines down) and the captions
    need no explanation — a small heading over a quoted sentence reads as its source."""
    return f'<p class="tnar alg-key"><b class="chip" style="--c:{colour}">CODE</b> a course whose outline evidences the activity</p>'


def occupation_block(soc: str, plates: list[Plate], *, top_n: int = 10, college_order: list[str] | None = None,
                     max_chips: int = CHIPS_PER_CELL, show_gaps: bool = False, columns: str = "college",
                     intro: str = "") -> str:
    """One occupation: header, then a table — the top-N activities down the side, one
    column per plate in a fixed roster order, that program's evidencing courses stacked as
    chips in the cell. Position carries the column (the strong channel); colour repeats the
    college. `columns` names the columns by college (a consortium roster) or by certificate
    (an evaluation roster: one college, its certificates side by side). An empty cell is a
    quiet dash; only a row empty in every column gets the amber gap line."""
    if not plates:
        return ""
    order = college_order or []
    plates = sorted(plates, key=lambda p: (order.index(p.member_id) if p.member_id in order else 99, p.college))
    title = plates[0].occupation
    # Rows: the most important core activities that at least one college's outlines
    # evidence, filled from the ranked list until `top_n` or the list runs out. Activities
    # nothing evidences are left out rather than shown empty — absence of evidence is
    # the method's weakest claim and the college's to confirm (see show_gaps). The order
    # is derived, not O*NET's: an activity inherits the highest incumbent importance
    # among the tasks it is anchored to (occupations.work_activities).
    def evidenced(r):
        return any(any(code != PLO for code in x.cells) for pl in plates
                   for x in pl.rows if x.dwa_id == r.dwa_id)
    ranked = plates[0].rows
    rows = [r for r in ranked if evidenced(r)][:top_n] if not show_gaps else ranked[:top_n]
    # How each college connects to the occupation (its pairing or its crosswalk) is
    # provenance, not reading matter: it stays on the viewed Plate, off the page.
    multi = _multi_college(plates)
    head = "".join(f'<th style="--c:{college_color(p.member_id)}"><span class="alg-colhd">{escape(_col_label(p, columns, multi=multi))}</span></th>'
                   for p in plates)
    # No method line per block: how rows are chosen and ordered is said once, in the
    # section's opening paragraph (report._curriculum_section).
    out = [f'<p class="chtitle">{escape(title)} <span class="alg-soc">SOC {escape(soc)}</span></p>', intro,
           f'<table class="alg-tbl"><colgroup><col class="alg-actcol">{"".join("<col>" for _ in plates)}</colgroup>'
           f'<thead><tr><th class="alg-acthd">Work activity</th>{head}</tr></thead><tbody>']
    covered = 0
    per_college: dict[str, int] = {}
    uncovered = []
    for r in rows:
        cells, any_ = [], False
        for pl in plates:
            pr = next((x for x in pl.rows if x.dwa_id == r.dwa_id), None)
            catalog = [c["code"] for c in pl.courses]
            url_of = {c["code"]: c.get("source_url", "") for c in pl.courses}
            found = [(code, cell) for code, cell in (pr.cells.items() if pr else []) if code != PLO]
            if columns != "certificate":                 # a certificate column shows the lead, not a ranked list
                found.sort(key=lambda kv: (-kv[1].level, catalog.index(kv[0]) if kv[0] in catalog else 99))
            codes = [code for code, _ in found]
            col = college_color(pl.member_id)
            if codes and columns == "certificate":
                # One college's own document: the column has the width, so the mark is the
                # LEAD excerpt — the one course sentence a reviewer would point to first
                # (alignment.lead_for; tier breaks ties) — with its course title and the
                # section of the outline it comes from. Other evidencing courses stay in the
                # review file; a list of codes here was noise.
                any_ = True
                per_college[pl.college] = per_college.get(pl.college, 0) + len(codes)
                title_of = {c["code"]: c.get("title", "") for c in pl.courses}
                lead = lead_for(pr, pl)
                c = lead["course"]
                chip = (f'<a class="chip" href="{escape(url_of[c])}" target="_blank" rel="noopener" style="--c:{col}">{escape(c)}</a>'
                        if url_of.get(c) else f'<b class="chip" style="--c:{col}">{escape(c)}</b>')
                # The excerpt as a small block: the section it comes from as a caption, the
                # sentence beneath, a rule down the left in the tier's shade (dark where the
                # outline commits — an outcome or objective; grey where it covers).
                tier = "#2a3450" if LEVEL.get(lead["section"]) == 2 else "#7a869a"
                cells.append(f'<td class="alg-dense"><div class="alg-ev"><div class="alg-evhd">{chip}<span class="alg-ctitle">{escape(title_of.get(c, ""))}</span></div>'
                             f'<div class="alg-quote alg-rule" style="--t:{tier}"><span class="alg-secx">{escape(COR_TAG.get(lead["section"], lead["section"]))}</span>'
                             f'“{escape(lead["quote"])}”</div></div></td>')
                continue
            if codes:
                any_ = True
                per_college[pl.college] = per_college.get(pl.college, 0) + len(codes)
                shown, rest = codes[:max_chips], codes[max_chips:]
                # each chip links out to the course's outline of record — Sources lists the
                # same links by certificate; the chip is the shortest path there
                chips = "".join(
                    (f'<a class="chip" href="{escape(url_of[c])}" target="_blank" rel="noopener" style="--c:{col}" '
                     f'title="{escape(pl.college)} · {escape(c)} · outline of record">{escape(c)}</a>')
                    if url_of.get(c) else
                    f'<b class="chip" style="--c:{col}" title="{escape(pl.college)} · {escape(c)}">{escape(c)}</b>'
                    for c in shown)
                if rest:
                    chips += f'<b class="chip alg-more" title="{escape(", ".join(rest))}">+{len(rest)}</b>'
                cells.append(f'<td><div class="alg-chips">{chips}</div></td>')
            else:
                cells.append('<td class="alg-empty">—</td>')
        if any_:
            covered += 1
        else:
            uncovered.append(r.dwa.rstrip("."))
        act = escape(r.dwa.rstrip("."))
        # The certificate's own program outcomes are read (PLO cells) but not drawn: a
        # per-row marker read as a third kind of information scattered through the table.
        # They stay in the review file and the internal evidence tables.
        if not any_ and show_gaps:
            act += '<span class="alg-gap">no course in the consortium evidences this</span>'
        out.append(f'<tr class="{"alg-gaprow" if (not any_ and show_gaps) else ""}"><td class="alg-act">{act}</td>{"".join(cells)}</tr>')
    out.append("</tbody></table>")
    # No counts in the report. A tally of course marks reads as precision the matcher
    # does not have, and it counts marks the three-per-cell cap hides. The table is the
    # statement; the readout survives only in the internal review view.
    if show_gaps:
        lead = sorted(per_college.items(), key=lambda kv: -kv[1])[:2]
        parts = [f"<b>{covered} of {len(rows)}</b> activities are evidenced by at least one course in the consortium."]
        if lead:
            parts.append("Most from " + " and ".join(f"{escape(_short(c))} ({n})" for c, n in lead) + ".")
        if uncovered:
            parts.append("Not evidenced by any college: " + "; ".join(escape(u) for u in uncovered) + ".")
        out.append(f'<p class="tnar">{" ".join(parts)}</p>')
    return "\n".join(x for x in out if x)


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
