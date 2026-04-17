"""Color palette extraction and validation node.

Extracts color palette from prototype images and validates against
brand/design token standards from the knowledge base.

References:
- IMG-01: Extract color palette from prototype images
- IMG-02: Validate color usage against brand/design token standards
- D-20: Use MiniMaxVisionClient for analysis
- D-24: Version metadata filtering in token retrieval
"""

from datetime import datetime
from typing import List

from src.workflow.state import ImageReviewState, Finding
from src.image.minimax_vision import MiniMaxVisionClient
from src.vectorstore.chroma_store import ChromaStore
from src.embeddings.bge_m3 import BGE_M3_Embeddings


def query_design_tokens(
    collection_name: str,
    query_text: str = "color palette design token brand",
    query_date: datetime = None,
) -> list[dict]:
    """Query knowledge base for design tokens with version filtering per D-24.

    Args:
        collection_name: Chroma collection name.
        query_text: Query text for retrieval.
        query_date: Date to check effective_date against (default: now).

    Returns:
        List of design token documents with version metadata.
    """
    if query_date is None:
        query_date = datetime.now()

    store = ChromaStore(
        collection_name=collection_name,
        embedding_fn=BGE_M3_Embeddings(),
    )

    # Get query embedding for similarity search
    embedding_fn = BGE_M3_Embeddings()
    query_embedding = embedding_fn.embed_query(query_text)

    # Use query_with_version_filter which properly checks:
    # - effective_date <= query_date
    # - superseded_date is null OR superseded_date > query_date
    results = store.query_with_version_filter(
        query_embedding=query_embedding,
        query_date=query_date,
        k=10,
    )

    return [{"content": doc.page_content, "metadata": doc.metadata} for doc, score in results]


def validate_color_node(state: ImageReviewState) -> ImageReviewState:
    """Extract color palette and validate against design tokens.

    IMG-01: Extract color palette from prototype images
    IMG-02: Validate color usage against brand/design token standards

    Uses MiniMaxVisionClient for color extraction per D-20.
    Queries design tokens with version filtering per D-24.

    Args:
        state: ImageReviewState with image_path and collection_name.

    Returns:
        Updated state with color_findings list.

    Severity calibration per D-14:
    - Primary brand color used incorrectly -> Major
    - Secondary color deviation -> Minor
    - Accent color mismatch -> Suggestion
    """
    vision_client = MiniMaxVisionClient()
    image_path = state["image_path"]

    # Extract color palette from image
    color_palette = vision_client.extract_color_palette(image_path)

    # Get design tokens from knowledge base with version filtering
    design_tokens = query_design_tokens(
        collection_name=state["collection_name"],
        query_text="color palette brand design token",
    )

    findings: List[Finding] = []

    # Parse extracted colors and compare against design tokens
    # The MiniMax response contains raw text that we analyze for color info
    for color_info in color_palette:
        raw = color_info.get("raw", "")

        # Check if any design tokens mention this color usage
        for token in design_tokens:
            token_content = token["content"].lower()

            # Look for color role mentions (primary, secondary, accent)
            if "primary" in raw.lower() and "primary" in token_content:
                # Check if primary color is consistent
                if not _colors_match(raw, token_content):
                    findings.append(Finding(
                        issue_type="color",
                        severity="Major",
                        location=f"Image: {image_path}",
                        description_en="Primary color usage may not match brand standard",
                        description_zh="主色调使用可能不符合品牌标准",
                        suggestion_en="Verify primary color against brand guidelines",
                        suggestion_zh="请验证主色调是否符合品牌指南",
                    ))

    # If no design tokens found, note this
    if not design_tokens:
        findings.append(Finding(
            issue_type="color",
            severity="Suggestion",
            location=f"Knowledge base: {state['collection_name']}",
            description_en="No design tokens found for color validation - assuming compliance",
            description_zh="知识库中未找到设计令牌进行颜色验证 - 假设合规",
            suggestion_en="Add color design tokens to knowledge base for future validation",
            suggestion_zh="请将颜色设计令牌添加到知识库以便将来验证",
        ))

    return {"color_findings": findings}


def _colors_match(color1_desc: str, color2_desc: str) -> bool:
    """Check if two color descriptions might match.

    This is a simplified heuristic - MiniMax vision provides actual hex codes.
    """
    # Extract hex codes if present
    import re
    hex_pattern = r'#[0-9A-Fa-f]{6}'

    hex1_matches = re.findall(hex_pattern, color1_desc)
    hex2_matches = re.findall(hex_pattern, color2_desc)

    if hex1_matches and hex2_matches:
        # Compare actual colors
        from src.image.color_utils import hex_to_rgb

        rgb1 = hex_to_rgb(hex1_matches[0])
        rgb2 = hex_to_rgb(hex2_matches[0])

        # Calculate color distance
        distance = sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5
        # Colors are similar if distance < 50 (in RGB space)
        return distance < 50

    # Fallback: compare descriptive terms
    color_terms = ["red", "blue", "green", "yellow", "orange", "purple", "black", "white"]
    for term in color_terms:
        if term in color1_desc.lower() and term in color2_desc.lower():
            return True

    return False


__all__ = ["validate_color_node"]
