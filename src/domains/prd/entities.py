"""PRD Domain - PRD Document entities.

Entities:
- PRDDocument: Main PRD document aggregate
- Section: A section within the PRD

References:
- ARCHITECTURE.md: PRD Context section
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Section:
    """A section within a PRD document.

    Attributes:
        title: Section title (e.g., "1. Overview", "2. User Stories")
        level: Heading level (1 for H1, 2 for H2, etc.)
        content: Raw text content of the section
        required: Whether this section is required by design standards
        position: Position in document order
    """
    title: str
    level: int  # H1=1, H2=2, H3=3...
    content: str
    required: bool = False
    position: int = 0

    def is_heading_only(self) -> bool:
        """Check if section has no body content (just a heading)."""
        return len(self.content.strip()) == 0


@dataclass
class PRDDocument:
    """A Product Requirements Document ready for review.

    Attributes:
        content: Full raw text content
        sections: Parsed sections from the document
        metadata: Document metadata (file_path, version, etc.)
        document_type: Type indicator ("prd")
    """
    content: str
    sections: list[Section] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    document_type: str = "prd"
    ingested_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_text(cls, text: str, metadata: Optional[dict] = None) -> "PRDDocument":
        """Create PRDDocument from raw text.

        Args:
            text: Raw text content of the PRD
            metadata: Optional metadata dict

        Returns:
            PRDDocument instance
        """
        sections = cls._parse_sections(text)
        return cls(
            content=text,
            sections=sections,
            metadata=metadata or {},
        )

    @staticmethod
    def _parse_sections(text: str) -> list[Section]:
        """Parse text into sections based on heading patterns.

        This is a simplified parser. A full implementation would use
        more sophisticated document structure detection.

        Args:
            text: Raw text to parse

        Returns:
            List of Section objects
        """
        sections = []
        lines = text.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            stripped = line.strip()
            # Detect heading (starts with # or number pattern like "1." "1.1")
            if stripped.startswith("#") or _is_numbered_heading(stripped):
                # Save previous section
                if current_section is not None:
                    current_section.content = "\n".join(current_content).strip()
                    sections.append(current_section)

                # Parse new heading
                level = _get_heading_level(stripped)
                title = _clean_heading(stripped)
                current_section = Section(
                    title=title,
                    level=level,
                    content="",
                    position=len(sections),
                )
                current_content = []
            elif current_section is not None:
                current_content.append(line)
            else:
                # Content before first heading - treat as intro
                current_content.append(line)

        # Don't forget last section
        if current_section is not None:
            current_section.content = "\n".join(current_content).strip()
            sections.append(current_section)

        return sections

    def get_required_sections(self) -> list[Section]:
        """Get sections marked as required."""
        return [s for s in self.sections if s.required]

    def get_missing_sections(self, required_titles: list[str]) -> list[str]:
        """Get titles of required sections that are missing.

        Args:
            required_titles: List of required section titles

        Returns:
            List of missing section titles
        """
        existing_titles = {s.title.lower() for s in self.sections}
        return [t for t in required_titles if t.lower() not in existing_titles]


def _is_numbered_heading(line: str) -> bool:
    """Check if line looks like a numbered heading (e.g., "1. Overview")."""
    return bool(_clean_heading(line).split()[0].rstrip(".").isdigit() if _clean_heading(line) else False)


def _get_heading_level(line: str) -> int:
    """Get heading level from line."""
    if line.startswith("####"):
        return 4
    elif line.startswith("###"):
        return 3
    elif line.startswith("##"):
        return 2
    elif line.startswith("#"):
        return 1
    # Numbered heading like "1. Overview" is H1
    elif _is_numbered_heading(line):
        return 1
    return 1


def _clean_heading(line: str) -> str:
    """Remove heading markers from line."""
    return line.lstrip("#").strip()
