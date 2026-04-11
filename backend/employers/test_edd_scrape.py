"""Unit tests for employers/edd_scrape.py HTML parsers.

The EDD ALMIS employer database is an ASP.NET application scraped via
regex. Any shift in its HTML structure silently breaks the name-row
parser or the form-state extractor, and the only visible signal is a
cache file with fewer employers than expected. These fixture-based
tests freeze the current markup shape so a regression surfaces
immediately instead of downstream in the merge step.

The fixture HTML is a minimal facsimile of one empResults.aspx page —
one result row and one __VIEWSTATE token — extracted from a capture of
a real response. If these tests fail, compare the fixture to a fresh
capture to decide whether the scraper needs updating.

Coverage:
  - _parse_employer_rows: extracts name, address, city, industry, size
    class from the result-table markup
  - _parse_employer_rows: returns empty list on empty/irrelevant HTML
  - _extract_form_state: captures __VIEWSTATE, __EVENTVALIDATION,
    __VIEWSTATEGENERATOR values when present
  - _extract_form_state: returns empty dict when form state is absent
"""

from employers.edd_scrape import _extract_form_state, _parse_employer_rows


# The row regex is sensitive to inter-cell whitespace — the live EDD
# markup renders each `<td>` adjacent to the previous one, so the
# fixture reproduces that layout exactly. Only the linkhref-to-anchor
# transition uses \s* in the pattern.
_SAMPLE_ROW_HTML = (
    '<a href="empDetails.aspx?menuChoice=emp&amp;empid=123456&amp;geogArea=0604000037">'
    'Kaiser Permanente</a></td>'
    '<td class="tableData">1 Kaiser Way</td>'
    '<td class="tableData">Los Angeles</td>'
    '<td class="tableData">Healthcare - Hospitals (General)</td>'
    '<td class="tableData">1,000-4,999 employees</td>'
)


_SAMPLE_FORM_HTML = """
<form>
<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="ABCDEFG123" />
<input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="GEN456" />
<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="EV789" />
</form>
"""


class TestParseEmployerRows:
    def test_extracts_single_row(self):
        rows = _parse_employer_rows(_SAMPLE_ROW_HTML)
        assert len(rows) == 1
        row = rows[0]
        assert row["name"] == "Kaiser Permanente"
        assert row["address"] == "1 Kaiser Way"
        assert row["city"] == "Los Angeles"
        assert row["industry"] == "Healthcare - Hospitals (General)"
        assert row["size_class"] == "1,000-4,999 employees"
        assert row["emp_id"] == "123456"
        assert row["geog_area"] == "0604000037"

    def test_empty_html_returns_empty_list(self):
        assert _parse_employer_rows("") == []

    def test_irrelevant_html_returns_empty_list(self):
        assert _parse_employer_rows("<html><body>no results</body></html>") == []

    def test_multiple_rows(self):
        doubled = _SAMPLE_ROW_HTML + _SAMPLE_ROW_HTML.replace("123456", "789012")
        rows = _parse_employer_rows(doubled)
        assert len(rows) == 2
        assert rows[0]["emp_id"] == "123456"
        assert rows[1]["emp_id"] == "789012"


class TestExtractFormState:
    def test_extracts_all_three_tokens(self):
        state = _extract_form_state(_SAMPLE_FORM_HTML)
        assert state["__VIEWSTATE"] == "ABCDEFG123"
        assert state["__VIEWSTATEGENERATOR"] == "GEN456"
        assert state["__EVENTVALIDATION"] == "EV789"

    def test_returns_empty_dict_when_absent(self):
        assert _extract_form_state("<html></html>") == {}

    def test_partial_form_state(self):
        # A page may render __VIEWSTATE without __EVENTVALIDATION; the
        # extractor should capture what's there without erroring.
        html = '<input name="__VIEWSTATE" value="ONLY_VS" />'
        state = _extract_form_state(html)
        assert state.get("__VIEWSTATE") == "ONLY_VS"
        assert "__EVENTVALIDATION" not in state
