"""
Document ingestion workflow — skeleton implementation.

Architecture is wired to the Anthropic API via LangChain. The chain structure
is correct and ready to receive real extraction and graph-write logic in a
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
        "You are an expert at extracting structured institutional data from California "
        "community college documents. Extract programs, curricula, and outcomes.",
    ),
    (
        "human",
        "Extract structured data from this document:\n\n{document_text}",
    ),
])

_chain = _prompt | _llm | StrOutputParser()


async def run_ingest(document_text: str) -> dict:
    """
    Stub: returns an architecturally correct but placeholder response.
    To implement: replace stub with _chain.ainvoke({"document_text": document_text}),
    parse the response, and write extracted entities to Neo4j.
    """
    logger.info(f"Ingestion workflow called, document length: {len(document_text)} chars")

    return {
        "status": "stub",
        "message": "Document ingestion workflow is architecturally wired but pending implementation.",
        "document_length": len(document_text),
        "extracted_entities": [],
    }
