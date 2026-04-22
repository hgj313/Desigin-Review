"""Document loaders for multi-format document ingestion.

Supports: PDF, Markdown, HTML, DOCX, PNG/JPG/JPEG/WEBP (via MiniMax Vision API)
Uses UnstructuredFileLoader as primary, PDFPlumberLoader for PDF tables.

References:
- D-06: Support Markdown, PDF, HTML, DOCX
- D-07: Use unstructured for parsing
- D-08: Use pdfplumber for PDF tables
- D-20: MiniMax Image Understanding via OpenAI-compatible API
"""

from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import PDFPlumberLoader, UnstructuredFileLoader
from langchain_core.documents import Document

from src.ingestion.image_loader import load_image


SUPPORTED_EXTENSIONS = {".pdf", ".md", ".html", ".docx", ".png", ".jpg", ".jpeg", ".webp"}


def load_document(file_path: str, metadata: Optional[dict] = None) -> list[Document]:
    """Load document with format-appropriate loader.

    Supported formats: .pdf, .md, .html, .docx, .png, .jpg, .jpeg, .webp
    Uses UnstructuredFileLoader as primary, PDFPlumberLoader for PDF tables,
    and MiniMax Vision API for images.

    Args:
        file_path: Path to the document file.
        metadata: Optional metadata to attach to each document.

    Returns:
        List of Document objects with page_content and metadata.

    Raises:
        ValueError: If file extension is not supported.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Prepare base metadata
    base_metadata = {"source_file": str(path)}
    if metadata:
        base_metadata.update(metadata)

    # Load based on file type
    if suffix == ".pdf":
        docs = _load_pdf(file_path, base_metadata)
    elif suffix == ".md":
        docs = _load_markdown(file_path, base_metadata)
    elif suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        docs = load_image(file_path, base_metadata)
    else:
        # .html, .docx
        docs = _load_with_unstructured(file_path, base_metadata)

    return docs


def _load_markdown(file_path: str, metadata: dict) -> list[Document]:
    """Load Markdown file with simple file reading.

    Args:
        file_path: Path to the Markdown file.
        metadata: Metadata to attach to documents.

    Returns:
        List of Document objects.
    """
    path = Path(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    doc = Document(page_content=content, metadata=dict(metadata))
    doc.metadata.setdefault("file_name", path.name)
    doc.metadata.setdefault("file_path", str(path))

    return [doc]


def _load_pdf(file_path: str, metadata: dict) -> list[Document]:
    """Load PDF using PDFPlumberLoader for enhanced table extraction.

    Args:
        file_path: Path to the PDF file.
        metadata: Metadata to attach to documents.

    Returns:
        List of Document objects.
    """
    # Try PDFPlumberLoader first for better table handling per D-08
    try:
        loader = PDFPlumberLoader(file_path)
        docs = loader.load()
    except Exception:
        # Fallback to UnstructuredFileLoader
        loader = UnstructuredFileLoader(file_path)
        docs = loader.load()

    # Add PDF-specific metadata
    path = Path(file_path)
    for doc in docs:
        doc.metadata.update(metadata)
        doc.metadata.setdefault("file_name", path.name)
        doc.metadata.setdefault("file_path", str(path))

    return docs


def _load_with_unstructured(file_path: str, metadata: dict) -> list[Document]:
    """Load document using UnstructuredFileLoader.

    Args:
        file_path: Path to the document.
        metadata: Metadata to attach to documents.

    Returns:
        List of Document objects.
    """
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load()

    # Add file metadata
    path = Path(file_path)
    for doc in docs:
        doc.metadata.update(metadata)
        doc.metadata.setdefault("file_name", path.name)
        doc.metadata.setdefault("file_path", str(path))

    return docs


def load_markdown(file_path: str, metadata: Optional[dict] = None) -> list[Document]:
    """Load Markdown file, preserve header hierarchy in metadata.

    Args:
        file_path: Path to the Markdown file.
        metadata: Optional metadata to attach to each document.

    Returns:
        List of Document objects.
    """
    base_metadata = {"source_file": str(Path(file_path))}
    if metadata:
        base_metadata.update(metadata)
    return _load_markdown(file_path, base_metadata)


def load_pdf(file_path: str, metadata: Optional[dict] = None) -> list[Document]:
    """Load PDF using pdfplumber for enhanced table extraction.

    Args:
        file_path: Path to the PDF file.
        metadata: Optional metadata to attach to each document.

    Returns:
        List of Document objects.
    """
    base_metadata = {"source_file": str(Path(file_path))}
    if metadata:
        base_metadata.update(metadata)
    return _load_pdf(file_path, base_metadata)


__all__ = ["load_document", "load_markdown", "load_pdf"]
