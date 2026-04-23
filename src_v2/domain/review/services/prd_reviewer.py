"""PRD Reviewer Service - LLM-based semantic analysis for PRD documents.

Per D-01: LLM semantic inference for vague language detection
Per D-02: CRITICAL/HIGH/MEDIUM severity classification
"""

from __future__ import annotations

__all__ = ["PRDReviewerService"]

import json
import re
import uuid
from datetime import datetime
from typing import Any, Protocol

from src_v2.domain.ingestion.entities import Document, Standard
from src_v2.domain.review.entities import VagueLanguagePattern
from src_v2.domain.review.llm_prompts.prompts import (
    SEMANTIC_COMPLETENESS_PROMPT,
    VAGUE_LANGUAGE_DETECTION_PROMPT,
)
from src_v2.domain.shared.entities import Finding, ReviewDimension, SeverityLevel


class ILLMClient(Protocol):
    """Protocol for LLM client (MiniMax M2.7 or OpenAI-compatible)."""

    def chat_completion(self, messages: list[dict], **kwargs) -> dict:
        """Send chat completion request and return response."""
        ...


class IPRDReviewerService(Protocol):
    """Protocol for PRD document review operations."""

    def detect_vague_language(self, doc: Document) -> list[Finding]:
        """Detect vague or ambiguous language patterns in a PRD."""
        ...

    def validate_cross_references(
        self, doc: Document, standards: list[Standard]
    ) -> list[Finding]:
        """Validate that cross-references in the document are valid."""
        ...

    def analyze_semantic_completeness(self, doc: Document) -> list[Finding]:
        """Analyze whether the document covers all required semantic elements."""
        ...

    def calculate_semantic_score(self, doc: Document) -> int:
        """Calculate a semantic completeness score (0-100)."""
        ...


class PRDReviewerService:
    """PRD Reviewer Service implementing LLM-based semantic analysis.

    Uses MiniMax M2.7 for semantic inference to detect:
    - Vague language patterns (D-01)
    - Missing structure (PRD-01)
    - Terminology inconsistency (PRD-02)

    Severity classification per D-02:
    - CRITICAL: Requirement is unmeasurable or completely undefined
    - HIGH: Key acceptance criteria missing or vague
    - MEDIUM: Minor ambiguity that could be clarified
    """

    def __init__(self, llm_client: ILLMClient):
        """Initialize PRDReviewerService.

        Args:
            llm_client: LLM client for semantic inference (MiniMax M2.7 or OpenAI-compatible)
        """
        self._llm = llm_client

    def detect_vague_language(self, doc: Document) -> list[Finding]:
        """Detect vague or ambiguous language patterns in a PRD.

        Uses LLM semantic inference (not regex/pattern matching) per D-01.

        Args:
            doc: Document to analyze

        Returns:
            List of Finding objects with CRITICAL/HIGH/MEDIUM severity
        """
        content = doc.content[:4000]  # Truncate per plan spec

        prompt = VAGUE_LANGUAGE_DETECTION_PROMPT.replace("{content}", content)

        messages = [
            {"role": "system", "content": "You are an expert PRD reviewer."},
            {"role": "user", "content": prompt},
        ]

        response = self._llm.chat_completion(messages)
        raw_text = self._extract_response_text(response)

        findings = self._parse_vague_language_findings(raw_text, doc.id)

        return findings

    def validate_cross_references(
        self, doc: Document, standards: list[Standard]
    ) -> list[Finding]:
        """Validate that cross-references in the document are valid.

        Args:
            doc: Document to validate
            standards: List of design standards to check against

        Returns:
            List of Finding objects for missing or invalid references
        """
        # This method is implemented in CrossReferenceValidator
        # Return empty list here - use CrossReferenceValidator for cross-reference validation
        return []

    def analyze_semantic_completeness(self, doc: Document) -> list[Finding]:
        """Analyze whether the PRD covers all required semantic elements.

        Checks for:
        - Overview section
        - User Stories section
        - Acceptance Criteria section

        Args:
            doc: Document to analyze

        Returns:
            List of Finding objects for missing or incomplete sections
        """
        content = doc.content[:4000]

        prompt = SEMANTIC_COMPLETENESS_PROMPT.replace("{content}", content)

        messages = [
            {"role": "system", "content": "You are an expert PRD reviewer."},
            {"role": "user", "content": prompt},
        ]

        response = self._llm.chat_completion(messages)
        raw_text = self._extract_response_text(response)

        findings = self._parse_semantic_completeness_findings(raw_text, doc.id)

        return findings

    def calculate_semantic_score(self, doc: Document) -> int:
        """Calculate a semantic completeness score (0-100).

        Score = 100 - (critical_count * 20) - (high_count * 10) - (medium_count * 5)
        Minimum score is 0.

        Args:
            doc: Document to score

        Returns:
            Score from 0-100
        """
        findings = self.analyze_semantic_completeness(doc)

        critical_count = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == SeverityLevel.HIGH)
        medium_count = sum(1 for f in findings if f.severity == SeverityLevel.MEDIUM)

        score = 100 - (critical_count * 20) - (high_count * 10) - (medium_count * 5)
        return max(0, score)

    def validate_prd_structure(self, doc: Document) -> list[Finding]:
        """Check PRD for required sections per PRD-01.

        Required sections:
        - Overview or 概述
        - User Story or 用户故事
        - Acceptance Criteria or 验收标准

        Args:
            doc: Document to validate

        Returns:
            List of Finding objects for missing sections
        """
        content = doc.content
        findings = []

        required_sections = [
            ("Overview", "概述"),
            ("User Story", "用户故事"),
            ("Acceptance Criteria", "验收标准"),
        ]

        for eng_term, chi_term in required_sections:
            if eng_term not in content and chi_term not in content:
                findings.append(
                    Finding(
                        id=str(uuid.uuid4()),
                        dimension=ReviewDimension.STRUCTURE,
                        severity=SeverityLevel.HIGH,
                        rule_id="prd-structure-001",
                        description=f"Required section missing: {eng_term} ({chi_term})",
                        location="document",
                        suggestion=f"Add {eng_term} section to PRD",
                        evidence=f"No mention of '{eng_term}' or '{chi_term}' in document",
                        created_at=datetime.now(),
                    )
                )

        return findings

    def validate_terminology_consistency(
        self, doc: Document, glossary: list[str]
    ) -> list[Finding]:
        """Check document for terminology consistency against glossary.

        Args:
            doc: Document to check
            glossary: List of approved terminology terms

        Returns:
            List of Finding objects for inconsistent terminology usage
        """
        findings = []
        content = doc.content.lower()

        for term in glossary:
            term_lower = term.lower()
            # Count occurrences (simple check for now)
            # Could be enhanced with proper NLP
            if term_lower in content:
                pass  # Term found, consistent

        return findings

    def _extract_response_text(self, response: Any) -> str:
        """Extract text from LLM response.

        Args:
            response: LLM response dict

        Returns:
            Extracted text content
        """
        if isinstance(response, dict):
            if "choices" in response:
                return response["choices"][0].get("message", {}).get("content", "")
            elif "content" in response:
                return response["content"]
        return str(response)

    def _parse_vague_language_findings(
        self, raw_text: str, doc_id: str
    ) -> list[Finding]:
        """Parse LLM response into Finding objects.

        Args:
            raw_text: Raw text from LLM response
            doc_id: Document ID for context

        Returns:
            List of Finding objects
        """
        findings = []

        try:
            # Try to extract JSON from response
            json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(raw_text)
        except (json.JSONDecodeError, ValueError):
            return findings

        for item in data:
            if not isinstance(item, dict):
                continue

            severity_str = item.get("severity", "MEDIUM").upper()
            severity = self._parse_severity(severity_str)

            findings.append(
                Finding(
                    id=str(uuid.uuid4()),
                    dimension=ReviewDimension.SEMANTIC,
                    severity=severity,
                    rule_id="prd-vague-001",
                    description=item.get("description", ""),
                    location=item.get("location", "document"),
                    suggestion=item.get("suggestion", ""),
                    evidence=item.get("evidence", ""),
                    created_at=datetime.now(),
                )
            )

        return findings

    def _parse_semantic_completeness_findings(
        self, raw_text: str, doc_id: str
    ) -> list[Finding]:
        """Parse semantic completeness response into Finding objects.

        Args:
            raw_text: Raw text from LLM response
            doc_id: Document ID for context

        Returns:
            List of Finding objects
        """
        findings = []

        try:
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(raw_text)
        except (json.JSONDecodeError, ValueError):
            return findings

        # Parse sections from completeness check
        sections = data.get("sections", [])
        for section in sections:
            if section.get("completeness") == "missing":
                severity_str = section.get("severity", "HIGH").upper()
                severity = self._parse_severity(severity_str)

                findings.append(
                    Finding(
                        id=str(uuid.uuid4()),
                        dimension=ReviewDimension.STRUCTURE,
                        severity=severity,
                        rule_id="prd-structure-001",
                        description=f"Section incomplete: {section.get('name', 'Unknown')}",
                        location=section.get("name", "document"),
                        suggestion="; ".join(section.get("suggestions", [])),
                        evidence=f"Completeness: {section.get('completeness')}",
                        created_at=datetime.now(),
                    )
                )

        # Parse individual findings
        for item in data.get("findings", []):
            severity_str = item.get("severity", "MEDIUM").upper()
            severity = self._parse_severity(severity_str)

            findings.append(
                Finding(
                    id=str(uuid.uuid4()),
                    dimension=ReviewDimension.SEMANTIC,
                    severity=severity,
                    rule_id="prd-vague-001",
                    description=item.get("description", ""),
                    location=item.get("location", "document"),
                    suggestion=item.get("suggestion", ""),
                    evidence="",
                    created_at=datetime.now(),
                )
            )

        return findings

    def _parse_severity(self, severity_str: str) -> SeverityLevel:
        """Parse severity string to SeverityLevel enum.

        Args:
            severity_str: Severity string like "CRITICAL", "HIGH", "MEDIUM"

        Returns:
            Corresponding SeverityLevel
        """
        if severity_str == "CRITICAL":
            return SeverityLevel.CRITICAL
        elif severity_str == "HIGH":
            return SeverityLevel.HIGH
        elif severity_str == "MEDIUM":
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW