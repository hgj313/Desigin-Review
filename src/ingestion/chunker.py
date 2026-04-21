"""Structural text splitter that preserves header hierarchy.

Splits documents on header boundaries (##, #) and paragraph breaks,
preserving header hierarchy as chunk metadata for source attribution.

References:
- D-01: Chunk size 500-800 tokens (default 600)
- D-02: Overlap 15-20% (default 90 tokens = 15% of 600)
- D-03: Split method: Header + Paragraph with separators list
"""

from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class StructuralChunker:
    """Header-aware text splitter per D-03.

    Splits on: ## headers, # headers, paragraph breaks
    Chunk size: 600 tokens (D-01)
    Overlap: 90 tokens (D-02: 15% of 600)

    Separators are applied in order, splitting on header boundaries first,
    then paragraph breaks, then sentences, then words.
    """

    # Separators applied in order per D-03
    DEFAULT_SEPARATORS = ["\n## ", "\n# ", "\n\n", "\n", ". ", " "]

    def __init__(
        self,
        chunk_size: int = 600,
        overlap: int = 90,
        separators: Optional[list[str]] = None,
        length_function: Optional[callable] = None,
    ):
        """Initialize the structural chunker.

        Args:
            chunk_size: Target chunk size in tokens (default 600 per D-01).
            overlap: Overlap between chunks in tokens (default 90 per D-02).
            separators: Custom separators list. Defaults to DEFAULT_SEPARATORS.
            length_function: Function to count tokens. Defaults to char-based approximation.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = separators or self.DEFAULT_SEPARATORS

        # Default length function: ~4 chars per token (approximate)
        if length_function is None:
            length_function = self._token_count

        self.splitter = RecursiveCharacterTextSplitter(
            separators=self.separators,
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=length_function,
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

    def split_documents(self, documents: list[Document]) -> list[Document]:
        """Split documents preserving header hierarchy in metadata.

        For documents with Markdown header structure, uses header-aware
        splitting to preserve section context. Otherwise uses standard
        text splitting.

        Args:
            documents: List of Document objects to split.

        Returns:
            List of chunked Document objects with updated metadata.
        """
        chunks = []

        for doc in documents:
            # Check if document has Markdown header structure
            if self._is_markdown_with_headers(doc.page_content):
                chunked = self._split_markdown_with_headers(doc)
            else:
                # Standard splitting
                texts = self.splitter.split_text(doc.page_content)
                chunked = self._create_chunks_with_metadata(
                    texts, doc.metadata, start_index=None
                )

            chunks.extend(chunked)

        # Add chunk index and total chunks metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)

        return chunks

    def _is_markdown_with_headers(self, text: str) -> bool:
        """Check if text contains Markdown header structure.

        Args:
            text: Document text.

        Returns:
            True if text contains # or ## headers.
        """
        return "\n## " in text or "\n# " in text or text.startswith("## ") or text.startswith("# ")

    def _split_markdown_with_headers(self, doc: Document) -> list[Document]:
        """Split Markdown document preserving header hierarchy.

        Splits on header boundaries first, then applies text splitting
        within each section to meet chunk size requirements.

        Args:
            doc: Document to split.

        Returns:
            List of chunked Document objects with header metadata.
        """
        header_meta = self._extract_header_metadata(doc.page_content)
        sections, section_starts = self._split_on_headers(doc.page_content)

        all_chunks = []
        for idx, section_text in enumerate(sections):
            if not section_text.strip():
                continue

            # Extract header info for this section
            section_meta = self._extract_header_metadata(section_text)
            combined_meta = {**doc.metadata, **header_meta, **section_meta}

            # Track position in original document
            section_start = section_starts[idx]

            # If section is small enough, don't split further
            if self._token_count(section_text) <= self.chunk_size:
                all_chunks.append(
                    Document(page_content=section_text, metadata=combined_meta)
                )
            else:
                # Split the section content
                texts = self.splitter.split_text(section_text)
                section_chunks = self._create_chunks_with_metadata(
                    texts, combined_meta, start_index=section_start
                )
                all_chunks.extend(section_chunks)

        return all_chunks

    def _split_on_headers(self, text: str) -> tuple[list[str], list[int]]:
        """Split text on header boundaries while preserving headers.

        Args:
            text: Text to split.

        Returns:
            Tuple of (sections, start_positions) where start_positions
            contains the character offset of each section in original text.
        """
        sections = []
        start_positions = []
        current = ""
        current_start = 0

        lines = text.split("\n")
        for line in lines:
            if line.startswith("## ") or line.startswith("# "):
                # Save previous section
                if current:
                    sections.append(current)
                    start_positions.append(current_start)
                current_start = text.find(line, current_start)
                current = line + "\n"
            else:
                current += line + "\n"

        # Don't forget the last section
        if current:
            sections.append(current)
            start_positions.append(current_start)

        return sections, start_positions

    def _extract_header_metadata(self, text: str) -> dict:
        """Extract header hierarchy from text for metadata.

        Parses the first line for # headers and returns section/subsection
        information.

        Args:
            text: Text to parse.

        Returns:
            Dict with 'section' and 'subsection' keys (empty if no header).
        """
        lines = text.strip().split("\n")
        if not lines:
            return {}

        first_line = lines[0].strip()

        if first_line.startswith("## "):
            return {
                "section": "",
                "subsection": first_line[3:].strip(),
            }
        elif first_line.startswith("# "):
            return {
                "section": first_line[2:].strip(),
                "subsection": "",
            }

        return {}

    def _create_chunks_with_metadata(
        self,
        texts: list[str],
        base_metadata: dict,
        start_index: Optional[int],
    ) -> list[Document]:
        """Create Document objects from split texts with metadata.

        Args:
            texts: List of text chunks.
            base_metadata: Base metadata to attach to each chunk.
            start_index: Starting index for position tracking.

        Returns:
            List of Document objects.
        """
        chunks = []
        for i, text in enumerate(texts):
            chunk_meta = {**base_metadata}
            if start_index is not None:
                chunk_meta["chunk_start_index"] = start_index + i
            chunks.append(Document(page_content=text, metadata=chunk_meta))
        return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 600,
    overlap: int = 90,
) -> list[Document]:
    """Convenience function for chunking documents.

    Args:
        documents: List of Document objects to chunk.
        chunk_size: Target chunk size in tokens (default 600 per D-01).
        overlap: Overlap between chunks in tokens (default 90 per D-02).

    Returns:
        List of chunked Document objects.
    """
    chunker = StructuralChunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.split_documents(documents)


__all__ = ["StructuralChunker", "chunk_documents"]
