"""Adaptive chunking service for content-type-specific text splitting.

This module provides the AdaptiveChunkingService that implements IChunkingService
Protocol and uses content-type-specific configurations for optimal text chunking.

References:
- RAG-01: Documents are chunked using content-type-specific strategies
- D-01: Chunk size 500-800 tokens (adaptive per type)
- D-02: Overlap 15-20% (adaptive per type)
"""

from typing import Protocol, runtime_checkable

from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src_v2.domain.ingestion.entities import (
    Chunk,
    DocumentContentType,
    Document,
)
from src_v2.domain.shared.value_objects import ChunkId, DocumentId


@runtime_checkable
class IChunkingService(Protocol):
    """Splits documents into retrievable chunks."""

    def chunk_document(self, doc: Document) -> list[Chunk]:
        """Split a document into chunks."""
        ...

    def detect_content_type(self, content: str) -> DocumentContentType:
        """Infer content type from text."""
        ...


# Content-type-specific chunk configurations per must_haves truths
CHUNK_CONFIGS = {
    DocumentContentType.SPACING: {
        "chunk_size": 400,
        "separators": ["\n## ", "\n- ", "\n\n", "\n"],
    },
    DocumentContentType.COLOR: {
        "chunk_size": 300,
        "separators": ["\n## ", "\n# ", "\n\n", "\n"],
    },
    DocumentContentType.TYPOGRAPHY: {
        "chunk_size": 500,
        "separators": ["\n## ", "\n# ", "\n### ", "\n\n", "\n"],
    },
    DocumentContentType.ACCESSIBILITY: {
        "chunk_size": 400,
        "separators": ["\n## ", "\n# ", "\n- ", "\n\n", "\n"],
    },
    DocumentContentType.GENERAL: {
        "chunk_size": 600,
        "separators": ["\n## ", "\n# ", "\n\n", "\n", ". ", " "],
    },
}


class AdaptiveChunkingService:
    """Content-type-adaptive text chunking service.

    Implements IChunkingService Protocol and uses content-type-specific
    chunk sizes and separators from CHUNK_CONFIGS for optimal splitting.

    Chunk overlap is automatically set to 15% of chunk_size per D-02.

    Attributes:
        chunk_size: Target chunk size in tokens (content-type-adaptive).
        separators: Separator list for splitting (content-type-adaptive).
    """

    # Keyword sets for content type detection
    _SPACING_KEYWORDS = {"spacing", "grid", "margin", "padding", "gap", "8pt", "4pt"}
    _COLOR_KEYWORDS = {
        "color",
        "colour",
        "#",
        "rgb",
        "hex",
        "palette",
        "brand",
    }
    _TYPOGRAPHY_KEYWORDS = {
        "font",
        "typography",
        "heading",
        "body",
        "text-size",
    }
    _ACCESSIBILITY_KEYWORDS = {
        "accessibility",
        "wcag",
        "contrast",
        "aria",
        "a11y",
    }

    def __init__(self):
        """Initialize with default general configuration."""
        self.chunk_size = CHUNK_CONFIGS[DocumentContentType.GENERAL]["chunk_size"]
        self.separators = CHUNK_CONFIGS[DocumentContentType.GENERAL]["separators"]

    def _get_splitter_for_content_type(
        self, content_type: DocumentContentType
    ) -> RecursiveCharacterTextSplitter:
        """Create a splitter configured for the given content type.

        Args:
            content_type: The content type to get splitter configuration for.

        Returns:
            RecursiveCharacterTextSplitter configured for content type.
        """
        config = CHUNK_CONFIGS[content_type]
        chunk_size = config["chunk_size"]
        overlap = int(chunk_size * 0.15)  # 15% overlap per D-02

        return RecursiveCharacterTextSplitter(
            separators=config["separators"],
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=self._token_count,
            add_start_index=True,
        )

    @staticmethod
    def _token_count(text: str) -> int:
        """Approximate token count using char-based estimation.

        Uses 4 chars per token as approximate ratio for English text.
        Chinese/English mixed text may vary but this is within acceptable
        tolerance for chunk sizing per D-01.

        Args:
            text: Input text.

        Returns:
            Approximate token count.
        """
        return len(text) // 4

    def detect_content_type(self, content: str) -> DocumentContentType:
        """Infer content type from text using keyword heuristics.

        Checks keywords in priority order:
        - SPACING: spacing, grid, margin, padding, gap, 8pt, 4pt
        - COLOR: color, colour, #, rgb, hex, palette, brand
        - TYPOGRAPHY: font, typography, heading, body, text-size
        - ACCESSIBILITY: accessibility, wcag, contrast, aria, a11y
        - GENERAL: default fallback

        Args:
            content: Text content to analyze.

        Returns:
            Detected DocumentContentType.
        """
        content_lower = content.lower()

        # Check SPACING
        if any(kw in content_lower for kw in self._SPACING_KEYWORDS):
            return DocumentContentType.SPACING

        # Check COLOR
        if any(kw in content_lower for kw in self._COLOR_KEYWORDS):
            return DocumentContentType.COLOR

        # Check TYPOGRAPHY
        if any(kw in content_lower for kw in self._TYPOGRAPHY_KEYWORDS):
            return DocumentContentType.TYPOGRAPHY

        # Check ACCESSIBILITY
        if any(kw in content_lower for kw in self._ACCESSIBILITY_KEYWORDS):
            return DocumentContentType.ACCESSIBILITY

        # Default
        return DocumentContentType.GENERAL

    def chunk_document(self, doc: Document) -> list[Chunk]:
        """Split a document into chunks using content-type-specific configuration.

        Uses langchain RecursiveCharacterTextSplitter with separators and
        chunk_size adapted to the document's content_type.

        Args:
            doc: Document to chunk.

        Returns:
            List of Chunk objects with populated id, document_id, content,
            content_type, metadata, and None embedding (to be populated later).
        """
        # Get content-type-specific splitter
        splitter = self._get_splitter_for_content_type(doc.content_type)

        # Create langchain Document for splitting
        lc_doc = LCDocument(page_content=doc.content, metadata=doc.metadata)

        # Split document
        split_docs = splitter.create_documents(
            [doc.content], metadatas=[doc.metadata]
        )

        # Convert to domain Chunk objects
        chunks = []
        for idx, split_doc in enumerate(split_docs):
            chunk = Chunk(
                id=ChunkId(f"chunk_{doc.id}_{idx}"),
                document_id=doc.id,
                content=split_doc.page_content,
                content_type=doc.content_type,
                metadata=dict(split_doc.metadata),
                embedding=None,
            )

            # Add chunk_index to metadata
            chunk.metadata["chunk_index"] = idx
            chunk.metadata["total_chunks"] = len(split_docs)

            # Preserve header_path if available from langchain metadata
            if "header_path" in split_doc.metadata:
                chunk.metadata["header_path"] = split_doc.metadata["header_path"]

            chunks.append(chunk)

        return chunks


__all__ = ["AdaptiveChunkingService", "CHUNK_CONFIGS", "IChunkingService"]