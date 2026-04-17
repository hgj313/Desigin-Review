"""PRD terminology validation node.

Validates terminology consistency against design standards glossary per PRD-02.
Uses HybridRetriever for exact + semantic matching.
"""

import logging
import re
from typing import List, Tuple

from langchain_core.documents import Document

from src.workflow.state import PRDReviewState, Finding
from src.vectorstore.chroma_store import ChromaStore
from src.embeddings.bge_m3 import BGE_M3_Embeddings
from src.retrieval.hybrid_search import HybridRetriever


logger = logging.getLogger(__name__)

# Similarity thresholds for semantic matching
EXACT_MATCH_THRESHOLD = 0.95
SEMANTIC_MATCH_THRESHOLD = 0.85


def _find_term_location(prd_text: str, term: str) -> str:
    """Find the line number where a term appears."""
    lines = prd_text.split('\n')
    for i, line in enumerate(lines, 1):
        if term.lower() in line.lower():
            return f"Line {i}"
    return "document"


def _check_exact_match(prd_text: str, glossary_terms: List[str]) -> List[Finding]:
    """Check for exact terminology matches (case-insensitive)."""
    findings = []
    text_lower = prd_text.lower()

    for term in glossary_terms:
        term_lower = term.lower()
        # Find all occurrences
        if term_lower in text_lower:
            # For each occurrence, check context
            location = _find_term_location(prd_text, term)
            # This is a simple presence check; in a real implementation,
            # you'd compare the definition with usage context
            findings.append(Finding(
                issue_type="terminology",
                severity="Major",
                location=location,
                description_en=f"Term '{term}' found in document - verify usage matches design standard definition",
                description_zh=f"术语'{term}'出现在文档中 - 请验证使用是否符合设计标准定义",
                suggestion_en=f"Consult the design standards glossary for '{term}' definition",
                suggestion_zh=f"请查阅设计标准词汇表中'{term}'的定义",
            ))

    return findings


def _check_semantic_match(
    prd_text: str,
    glossary_terms: List[str],
    retriever: HybridRetriever,
) -> List[Finding]:
    """Check for semantically similar terms using embeddings."""
    findings = []

    # Extract words from PRD text
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', prd_text)
    unique_words = list(set(words))

    for word in unique_words:
        # Skip very short words
        if len(word) < 4:
            continue

        # Skip if it's an exact glossary term
        if word.lower() in [t.lower() for t in glossary_terms]:
            continue

        # Search for similar terms
        try:
            results = retriever.search(word, k=3)
            for doc, score in results:
                if score >= SEMANTIC_MATCH_THRESHOLD:
                    # Find a glossary term that matches
                    glossary_term = doc.page_content.split('\n')[0] if doc.page_content else ""
                    location = _find_term_location(prd_text, word)
                    findings.append(Finding(
                        issue_type="terminology",
                        severity="Minor",
                        location=location,
                        description_en=f"Term '{word}' may be inconsistent with design standards (similar to '{glossary_term}')",
                        description_zh=f"术语'{word}'可能与设计标准不一致（类似于'{glossary_term}'）",
                        suggestion_en=f"Consider using design standard terminology instead of '{word}'",
                        suggestion_zh=f"请考虑使用设计标准术语替代'{word}'",
                    ))
        except Exception as e:
            logger.debug(f"Semantic check failed for '{word}': {e}")

    return findings


def validate_terminology_node(state: PRDReviewState) -> PRDReviewState:
    """Validate terminology consistency against design standards glossary.

    Args:
        state: PRDReviewState with prd_text and collection_name.

    Returns:
        Updated state with terminology_findings list populated.
    """
    prd_text = state["prd_text"]
    collection_name = state["collection_name"]
    findings: List[Finding] = []

    try:
        # Initialize ChromaStore and HybridRetriever
        store = ChromaStore(
            collection_name=collection_name,
            embedding_fn=BGE_M3_Embeddings(),
        )

        # Get all documents from collection
        all_docs = store.collection.get()

        if not all_docs["documents"]:
            # Empty collection - no glossary found
            findings.append(Finding(
                issue_type="terminology",
                severity="Suggestion",
                location="document",
                description_en="Standard Not Found: No glossary terms found in knowledge base",
                description_zh="未找到标准：知识库中未找到词汇表术语",
                suggestion_en="Populate the knowledge base with design standards glossary",
                suggestion_zh="请在知识库中填充设计标准词汇表",
            ))
            return {"terminology_findings": findings}

        # Extract glossary terms (simplified - in production, parse structured glossary)
        glossary_terms = []
        for doc_text in all_docs["documents"]:
            # Extract first line as term identifier
            first_line = doc_text.split('\n')[0].strip()
            if first_line:
                glossary_terms.append(first_line)

        # Check exact matches
        findings.extend(_check_exact_match(prd_text, glossary_terms))

        # Check semantic matches using HybridRetriever
        retriever = HybridRetriever(
            texts=all_docs["documents"],
            embedding_fn=BGE_M3_Embeddings(),
            collection=store.collection,
        )
        findings.extend(_check_semantic_match(prd_text, glossary_terms, retriever))

    except Exception as e:
        logger.error(f"Terminology validation failed: {e}")
        findings.append(Finding(
            issue_type="terminology",
            severity="Minor",
            location="document",
            description_en=f"Terminology validation error: {str(e)}",
            description_zh=f"术语验证错误：{str(e)}",
            suggestion_en="Check knowledge base connectivity",
            suggestion_zh="请检查知识库连接",
        ))

    return {
        "terminology_findings": findings,
    }


__all__ = ["validate_terminology_node"]
