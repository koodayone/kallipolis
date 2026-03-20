"""
Report generation workflow — skeleton implementation.

Architecture is wired to the Anthropic API via LangChain. The chain structure
is correct and ready to receive real Cypher queries and report logic in a
subsequent iteration. Currently returns a stubbed response.
"""
import logging
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

_llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=2048)

_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert in California community college workforce development reporting, "
        "familiar with Strong Workforce Program and Perkins V federal requirements.",
    ),
    (
        "human",
        "Generate a structured outline for a {report_type} report for a California "
        "community college. Include major sections, data requirements, and key metrics.",
    ),
])

_chain = _prompt | _llm | StrOutputParser()


async def run_report(report_type: str) -> dict:
    """
    Stub: returns an architecturally correct but placeholder response.
    To implement: replace stub with _chain.ainvoke({"report_type": report_type})
    and populate sections from Cypher query results.
    """
    logger.info(f"Report workflow called for type: {report_type}")

    report_labels = {
        "strong_workforce": "Strong Workforce Program Report",
        "perkins_v": "Perkins V Comprehensive Local Needs Assessment",
    }

    return {
        "report_type": report_type,
        "report_label": report_labels.get(report_type, report_type),
        "status": "stub",
        "message": "Report generation workflow is architecturally wired but pending institutional data connection.",
        "sections": [],
    }
