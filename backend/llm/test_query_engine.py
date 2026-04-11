"""Unit tests for llm.query_engine.validate_cypher — the Cypher safety gate.

This is the only thing standing between LLM-generated queries and the graph.
Regressions here are silent and high-impact, so the suite is deliberately
opinionated about write keywords, college scoping, and formatting quirks.
"""

import pytest

from llm.query_engine import validate_cypher, DISALLOWED_KEYWORDS


class TestReadOnlyEnforcement:
    @pytest.mark.parametrize("keyword", sorted(DISALLOWED_KEYWORDS))
    def test_each_disallowed_keyword_is_rejected(self, keyword):
        # Every disallowed keyword should raise, regardless of case.
        cypher = f"MATCH (c:College {{name: $college}}) {keyword} (c) RETURN c"
        with pytest.raises(ValueError, match="disallowed operations"):
            validate_cypher(cypher)

    def test_lowercase_write_keywords_are_rejected(self):
        # Lowercase too — the tokenizer uppercases before checking.
        with pytest.raises(ValueError, match="disallowed operations"):
            validate_cypher("match (c:College {name: $college}) delete c")

    def test_read_only_match_passes(self):
        cypher = "MATCH (c:College {name: $college}) RETURN c"
        assert validate_cypher(cypher) == cypher


class TestCollegeScoping:
    def test_missing_college_scope_is_rejected(self):
        with pytest.raises(ValueError, match="missing college scope"):
            validate_cypher("MATCH (c:College) RETURN c")

    def test_dollar_college_parameter_satisfies_scope(self):
        cypher = "MATCH (c:College {name: $college}) RETURN c"
        assert validate_cypher(cypher) == cypher

    def test_literal_college_property_satisfies_scope(self):
        # When the LLM inlines `college:` as a property filter rather than
        # using $college, scoping is still present.
        cypher = "MATCH (c:Course {college: 'foothill'}) RETURN c"
        assert validate_cypher(cypher) == cypher


class TestFormattingCleanup:
    def test_strips_markdown_fences(self):
        cypher = "```cypher\nMATCH (c:College {name: $college}) RETURN c\n```"
        result = validate_cypher(cypher)
        assert not result.startswith("```")
        assert not result.endswith("```")
        assert "MATCH" in result

    def test_strips_trailing_semicolon(self):
        cypher = "MATCH (c:College {name: $college}) RETURN c;"
        assert not validate_cypher(cypher).endswith(";")

    def test_strips_surrounding_whitespace(self):
        cypher = "  \n  MATCH (c:College {name: $college}) RETURN c  \n  "
        assert validate_cypher(cypher) == "MATCH (c:College {name: $college}) RETURN c"


class TestCannotTranslateSignal:
    def test_cannot_translate_raises_user_facing_error(self):
        with pytest.raises(ValueError, match="rephrasing"):
            validate_cypher("CANNOT_TRANSLATE")

    def test_cannot_translate_embedded_still_raises(self):
        with pytest.raises(ValueError, match="rephrasing"):
            validate_cypher("// CANNOT_TRANSLATE — query ambiguous")
