"""Image document loader using MiniMax Vision API for prototype analysis.

Supports: PNG, JPG, JPEG, WEBP
Uses MiniMax MCP understand_image tool for image analysis.

References:
- D-20: MiniMax Image Understanding via OpenAI-compatible API
- IMG-01: Prototype color palette extraction
"""

from pathlib import Path
from typing import Optional

from langchain_core.documents import Document


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


# =============================================================================
# Prototype Image Analysis (for inspection, NOT stored in RAG)
# =============================================================================

def analyze_prototype(image_path: str) -> dict:
    """Analyze a prototype image and return its visual description.

    This function is designed to be called from Claude Code context where
    the MiniMax MCP tool (understand_image) is available. It returns the
    description for immediate inspection without storing in RAG.

    Args:
        image_path: Path to the prototype image file.

    Returns:
        dict with keys:
            - image_path: Original image path
            - description: Visual description from MCP tool
            - file_name: Name of the image file

    Raises:
        ValueError: If file extension is not supported.
    """
    path = Path(image_path)
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format: {suffix}. "
            f"Supported: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        )

    # MCP tool is called from Claude Code context
    # The description is obtained via: mcp__MiniMax__understand_image()
    # This function just validates and returns metadata
    return {
        "image_path": str(path),
        "file_name": path.name,
        "description": None,  # Filled by Claude Code when calling MCP
    }


# =============================================================================
# Prototype Document Creation (for RAG storage)
# =============================================================================

def create_prototype_document(
    image_path: str,
    description: str,
    metadata: Optional[dict] = None,
) -> Document:
    """Create a RAG-ready Document from prototype image description.

    Takes the description from MCP tool and wraps it with appropriate
    metadata for Chroma vector store storage.

    Args:
        image_path: Original image path for reference.
        description: Visual description from MCP tool.
        metadata: Additional metadata to attach.

    Returns:
        Document ready for RAG storage with document_type="prototype".
    """
    path = Path(image_path)

    base_metadata = {
        "source_file": str(path),
        "file_name": path.name,
        "file_path": str(path),
        "document_type": "prototype",
        # ChromaStore required fields (must be provided or overridden)
        "document_name": path.stem,
        "section": "prototype",
    }
    if metadata:
        base_metadata.update(metadata)

    return Document(page_content=description, metadata=base_metadata)


# =============================================================================
# Prototype RAG Ingestion (stored in vector database)
# =============================================================================

def ingest_prototype(
    image_path: str,
    description: str,
    metadata: Optional[dict] = None,
) -> list[Document]:
    """Ingest a prototype image description into RAG.

    Creates a Document with prototype metadata and prepares it for
    ChromaStore storage. Note: This only creates the Document - actual
    storage requires calling ChromaStore.add_documents() separately.

    Args:
        image_path: Original image path for reference.
        description: Visual description from MCP tool.
        metadata: Additional metadata to attach.

    Returns:
        List containing one Document ready for RAG storage.

    Raises:
        ValueError: If file extension is not supported.
    """
    path = Path(image_path)
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format: {suffix}. "
            f"Supported: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        )

    return [create_prototype_document(image_path, description, metadata)]


# =============================================================================
# Legacy functions (deprecated, use MCP-based approach)
# =============================================================================

def load_image(
    file_path: str,
    metadata: Optional[dict] = None,
    analysis_type: str = "full",
) -> list[Document]:
    """Load prototype image and extract visual description via MiniMax Vision.

    DEPRECATED: Use analyze_prototype() + create_prototype_document() instead.
    This function uses the old OpenAI-compatible API which doesn't support
    multimodal images correctly.

    Args:
        file_path: Path to image file.
        metadata: Optional metadata to attach.
        analysis_type: Type of vision analysis - "full", "color", "typography",
                       "spacing", "accessibility".

    Returns:
        List containing one Document with vision analysis as page_content.
    """
    # For now, return empty - old API doesn't support images
    return []


def load_prototype(
    file_path: str,
    metadata: Optional[dict] = None,
) -> list[Document]:
    """Load prototype image with full visual analysis.

    DEPRECATED: Use analyze_prototype() + create_prototype_document() instead.

    Args:
        file_path: Path to prototype image.
        metadata: Optional metadata to attach.

    Returns:
        List containing one Document with comprehensive vision analysis.
    """
    return load_image(file_path, metadata=metadata, analysis_type="full")


__all__ = [
    "analyze_prototype",
    "create_prototype_document",
    "ingest_prototype",
    "load_image",
    "load_prototype",
    "SUPPORTED_IMAGE_EXTENSIONS",
]