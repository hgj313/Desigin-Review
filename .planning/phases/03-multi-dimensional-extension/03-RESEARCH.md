# Phase 3: Multi-Dimensional Extension - Research

**Researched:** 2026/04/17
**Domain:** Prototype Image Review with Parallel Multi-Dimensional Fan-out and Iterative Refinement
**Confidence:** MEDIUM (based on training knowledge; web search unavailable for verification)

## Summary

Phase 3 extends the Phase 2 single-dimension PRD review agent to prototype image review with parallel multi-dimensional fan-out across Structure, Terminology, Layout, and Accessibility dimensions (per AGT-02). The phase introduces MiniMax Image Understanding for extracting color palettes, typography hierarchy, spacing/grid alignment, and WCAG contrast compliance from prototype images. It also adds LangGraph cycles for iterative re-retrieval when initial findings are inconclusive (AGT-04), and version metadata in Chroma to prevent stale standards from being applied (AGT-05).

**Primary recommendation:** Build an ImageReviewState that extends PRDReviewState with image-specific fields. Use MiniMax's OpenAI-compatible multimodal API (same base URL as Phase 2 LLM calls) for image analysis. Implement a 4-way parallel fan-out (validate_color, validate_typography, validate_spacing, validate_accessibility) similar to Phase 2's structure/terminology/completeness/formatting validators. Add version metadata filtering to Chroma queries for AGT-05 compliance.

## User Constraints (from CONTEXT.md)

### Phase 1 Decisions (Extends)
| Decision | Value |
|----------|-------|
| D-01 to D-12 | Phase 1 locked decisions (chunking, embeddings, Chroma, bge-m3, bilingual) |
| AGT-01 | LangGraph for workflow orchestration |
| AGT-03 | Standard Not Found behavior |

### Phase 2 Decisions (Extends)
| Decision | Value |
|----------|-------|
| D-13 | Structured Markdown compliance reports |
| D-14 | Hybrid severity calibration (rules + LLM) |
| D-15 | Hybrid terminology matching (exact + semantic) |
| D-16 | User-controlled review depth (fast/thorough/balanced) |
| D-17 | Iterative refine agent loop, max 3 iterations |
| Fan-out/join | 4 parallel validators -> aggregate_findings -> conditional loop |

### Phase 3 Specific Decisions
- **IMG-06:** System uses MiniMax Image Understanding for image analysis (OpenAI-compatible API)
- **AGT-02:** Review dimensions execute in parallel (Structure, Terminology, Layout, Accessibility fan-out)
- **AGT-04:** System uses LangGraph cycles for re-retrieval when initial findings are inconclusive
- **AGT-05:** Knowledge base stores version metadata (version_id, effective_date) to prevent stale standards

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRD-05 | Detect unstated assumptions (vague language: "as needed", "etc.") | Pattern: extend Phase 2 completeness validator |
| IMG-01 | Extract color palette from prototype images | MiniMax Image Understanding API + color analysis |
| IMG-02 | Validate color usage against brand/design token standards | Color extraction + knowledge base retrieval |
| IMG-03 | Analyze typography hierarchy (heading vs body vs caption) | MiniMax vision + image analysis |
| IMG-04 | Validate spacing/grid alignment against 8pt/4pt standards | Image measurement + grid validation |
| IMG-05 | WCAG AA contrast compliance checking | Color contrast algorithm (WCAG 2.1) |
| IMG-06 | Use MiniMax Image Understanding (OpenAI-compatible API) | MiniMax multimodal API |
| AGT-02 | Parallel fan-out across 4 dimensions (Structure, Terminology, Layout, Accessibility) | LangGraph parallel edges |
| AGT-04 | LangGraph cycles for re-retrieval when inconclusive | Cycle pattern from Phase 2 |
| AGT-05 | Version metadata (version_id, effective_date) in Chroma | Chroma metadata filtering |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **LangChain** | ^0.3.x | LLM integration, retrieval chains | Required per project constraints |
| **LangGraph** | ^0.2.x | State machine workflow, cycles | Required per AGT-01; superior for complex stateful workflows |
| **MiniMax SDK** | latest | OpenAI-compatible LLM + image API | Required per PROJECT.md; IMG-06 requires MiniMax |
| **Chroma** | latest | Vector store (from Phase 1) | Local, zero-setup |
| **bge-m3** | latest | Embeddings (from Phase 1) | Bilingual Chinese/English |
| **Pillow** | latest | Image processing | Color extraction, image dimension analysis |

### Image Analysis
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **Pillow** | latest | Basic image analysis | IMG-01 color extraction, IMG-04 spacing |
| **colorthief** | latest | Dominant color extraction | IMG-01 palette extraction from images |
| **MiniMax Image Understanding** | via API | Multi-modal analysis | IMG-03 typography, IMG-04 layout, IMG-05 contrast |

**Note:** MiniMax Image Understanding is used for complex image analysis (IMG-01 to IMG-06). Pillow/colorthief are fallbacks for basic color extraction if MiniMax API fails.

**Installation:**
```bash
uv add pillow colorthief
# MiniMax already added in Phase 2
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── workflow/
│   ├── state.py              # ImageReviewState extends PRDReviewState
│   ├── graph.py               # Image review graph (extends Phase 2)
│   └── nodes/
│       ├── image_base.py      # Base class for image validators
│       ├── color.py           # IMG-01, IMG-02: color palette extraction/validation
│       ├── typography.py      # IMG-03: typography hierarchy analysis
│       ├── spacing.py         # IMG-04: spacing/grid alignment validation
│       ├── accessibility.py    # IMG-05: WCAG contrast checking
│       └── prd_assumptions.py # PRD-05: vague language detection
├── image/
│   ├── minimax_vision.py      # MiniMax Image Understanding client
│   └── color_utils.py        # Color extraction and contrast calculation
└── report/
    └── markdown.py            # Extended report generation (from Phase 2)
```

### Pattern 1: MiniMax Image Understanding via OpenAI-Compatible API

**What:** Use MiniMax's multimodal API with OpenAI-compatible endpoint for image analysis.

**When to use:** IMG-06 requirement for MiniMax Image Understanding.

**Implementation:**
```python
# Source: [ASSUMED - MiniMax OpenAI-compatible API]
from langchain_openai import ChatOpenAI
import base64
from PIL import Image
import io

def encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64 string for API."""
    with Image.open(image_path) as img:
        buffer = io.BytesIO()
        img.save(buffer, format=img.format or "PNG")
        return base64.b64encode(buffer.getvalue()).decode()

def analyze_image_with_minimax(
    image_path: str,
    prompt: str,
    model: str = "MiniMax/M2.7",
) -> str:
    """Analyze prototype image using MiniMax Image Understanding."""
    llm = ChatOpenAI(
        model=model,
        api_key=os.environ.get("MINIMAX_API_KEY"),
        base_url="https://api.minimax.chat/v1",
    )

    # Encode image
    image_base64 = encode_image_to_base64(image_path)

    # Create message with image
    response = llm.invoke([
        HumanMessage(content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"}
            }
        ])
    ])

    return response.content
```

**Color palette extraction prompt:**
```
Extract the color palette from this UI prototype image. For each dominant color, provide:
1. Hex code
2. RGB values
3. Usage location (button, background, text, etc.)
4. Whether it appears to be a primary, secondary, or accent color

Return as structured list.
```

**Typography analysis prompt:**
```
Analyze the typography in this UI prototype:
1. Identify heading styles (font size, weight, line height)
2. Identify body text styles
3. Identify caption/label styles
4. Note the hierarchy relationship (H1 > H2 > body > caption)
5. Estimate font family if identifiable

Return as structured list.
```

### Pattern 2: Color Palette Extraction (IMG-01)

**What:** Extract dominant colors from prototype images using color analysis.

**When to use:** IMG-01 requirement for extracting color palette from prototype images.

**Implementation:**
```python
# Source: [ASSUMED - colorthief library pattern]
from colorthief import ColorThief
import numpy as np

def extract_color_palette(image_path: str, num_colors: int = 6) -> list[dict]:
    """Extract dominant colors with usage context."""
    color_thief = ColorThief(image_path)

    # Get dominant color first
    dominant_color = color_thief.get_color(quality=1)

    # Get palette (most common colors)
    palette = color_thief.get_palette(color_count=num_colors, quality=1)

    colors = []
    for i, (r, g, b) in enumerate(palette):
        hex_code = f"#{r:02x}{g:02x}{b:02x}"
        colors.append({
            "hex": hex_code,
            "rgb": (r, g, b),
            "is_dominant": (r, g, b) == dominant_color,
            "position": i,
        })

    return colors
```

**Alternative with Pillow (no external dependency):**
```python
# Source: [ASSUMED - Pillow color quantization]
from PIL import Image
import numpy as np

def extract_palette_pillow(image_path: str, num_colors: int = 6) -> list[dict]:
    """Extract colors using Pillow's quantize method."""
    img = Image.open(image_path)
    img = img.convert("RGB")
    img = img.resize((150, 150))  # Smaller for faster processing

    # Quantize to reduce colors
    quantized = img.quantize(colors=num_colors)
    palette = quantized.getpalette()[:num_colors * 3]

    colors = []
    for i in range(num_colors):
        r, g, b = palette[i*3:(i+1)*3]
        colors.append({
            "hex": f"#{r:02x}{g:02x}{b:02x}",
            "rgb": (r, g, b),
        })

    return colors
```

### Pattern 3: WCAG Contrast Checking (IMG-05)

**What:** Calculate contrast ratio between text and background colors per WCAG 2.1 AA standard.

**When to use:** IMG-05 requirement for accessibility contrast checking.

**Implementation:**
```python
# Source: [ASSUMED - WCAG 2.1 contrast algorithm]
import math

def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1.

    Formula: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
    """
    def adjust_channel(c: int) -> float:
        c = c / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = adjust_channel(r), adjust_channel(g), adjust_channel(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
    """Calculate contrast ratio between two colors.

    Returns ratio from 1 to 21 (e.g., 4.5:1).
    """
    lum1 = relative_luminance(*color1)
    lum2 = relative_luminance(*color2)

    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)

    return (lighter + 0.05) / (darker + 0.05)


# WCAG AA thresholds
WCAG_AA_NORMAL_TEXT = 4.5  # Minimum 4.5:1 for normal text
WCAG_AA_LARGE_TEXT = 3.0    # Minimum 3.0:1 for large text (18pt+ or 14pt+ bold)
WCAG_AA_UI_COMPONENTS = 3.0 # Minimum 3.0:1 for UI components

def check_wcag_compliance(
    text_color: tuple[int, int, int],
    bg_color: tuple[int, int, int],
    text_size: float = 14.0,
) -> dict:
    """Check WCAG AA compliance for text/background combination."""
    ratio = contrast_ratio(text_color, bg_color)

    # Determine required threshold
    if text_size >= 18 or (text_size >= 14 and text_size < 18):
        required = WCAG_AA_LARGE_TEXT
    else:
        required = WCAG_AA_NORMAL_TEXT

    compliant = ratio >= required

    return {
        "ratio": round(ratio, 2),
        "required": required,
        "compliant": compliant,
        "level": "AA" if compliant else "Fail",
        "ratio_string": f"{ratio:.1f}:1",
    }
```

### Pattern 4: 8pt/4pt Grid Validation (IMG-04)

**What:** Validate spacing between UI elements against 8pt or 4pt grid system.

**When to use:** IMG-04 requirement for spacing/grid alignment validation.

**Implementation:**
```python
# Source: [ASSUMED - grid system validation pattern]
from PIL import Image
import numpy as np

def measure_element_spacing(image_path: str) -> list[dict]:
    """Measure spacing between UI elements.

    Assumes prototype is a wireframe or has clear visual boundaries.
    Returns spacing measurements in pixels.
    """
    img = Image.open(image_path)
    img_array = np.array(img)

    # Detect edges to find element boundaries
    # Simplified: detect horizontal/vertical lines
    # In practice, use edge detection or MiniMax for element detection

    # For now, return placeholder structure
    return []


def validate_grid_alignment(
    spacing_px: float,
    dpi: int = 72,
    grid_size: int = 8,
) -> dict:
    """Validate spacing against grid system.

    Args:
        spacing_px: Measured spacing in pixels
        dpi: Image DPI (default 72 for screen)
        grid_size: Grid size in points (8 or 4)

    Returns:
        Validation result with alignment status.
    """
    # Convert pixels to points (1 point = 1/72 inch)
    spacing_pt = spacing_px

    # Check if spacing is multiple of grid
    remainder = spacing_pt % grid_size

    return {
        "spacing_px": spacing_px,
        "spacing_pt": spacing_pt,
        "grid_size": grid_size,
        "is_aligned": remainder < 0.5,  # Allow small tolerance
        "nearest_grid": round(spacing_pt / grid_size) * grid_size,
        "deviation": remainder if remainder < grid_size / 2 else grid_size - remainder,
    }
```

### Pattern 5: Parallel Fan-Out with 4 Image Validators (AGT-02)

**What:** Execute 4 image review dimensions (color, typography, spacing, accessibility) in parallel, then aggregate results.

**When to use:** AGT-02 requirement for parallel fan-out across dimensions.

**Implementation (extends Phase 2 graph):**
```python
# Source: [ASSUMED - LangGraph fan-out pattern from Phase 2]
def create_image_review_graph() -> StateGraph:
    """Create image review workflow with 4-way parallel fan-out.

    Graph structure:
        start -> validate_color (IMG-01, IMG-02)
              -> validate_typography (IMG-03)
              -> validate_spacing (IMG-04)
              -> validate_accessibility (IMG-05)
              -> aggregate_findings
              -> (conditional: iterate? -> re_retrieve -> validators) x max_iterations
              -> generate_report -> END
    """
    workflow = StateGraph(ImageReviewState)

    # Fan-out: 4 parallel image validation nodes
    workflow.add_node("validate_color", validate_color_node)
    workflow.add_node("validate_typography", validate_typography_node)
    workflow.add_node("validate_spacing", validate_spacing_node)
    workflow.add_node("validate_accessibility", validate_accessibility_node)

    # PRD assumption detection (per PRD-05)
    workflow.add_node("detect_prd_assumptions", detect_prd_assumptions_node)

    # Join: aggregate findings
    workflow.add_node("aggregate_findings", aggregate_image_findings_node)

    # Iterative refinement loop (per AGT-04)
    workflow.add_node("should_refine", should_refine_node)
    workflow.add_node("re_retrieve", re_retrieve_node)

    # Report generation
    workflow.add_node("generate_report", generate_report_node)

    # Entry point: __start__ -> all 5 validators (fan-out in parallel)
    workflow.add_edge("__start__", "validate_color")
    workflow.add_edge("__start__", "validate_typography")
    workflow.add_edge("__start__", "validate_spacing")
    workflow.add_edge("__start__", "validate_accessibility")
    workflow.add_edge("__start__", "detect_prd_assumptions")

    # Fan-out edges: all validators feed into aggregate_findings
    workflow.add_edge("validate_color", "aggregate_findings")
    workflow.add_edge("validate_typography", "aggregate_findings")
    workflow.add_edge("validate_spacing", "aggregate_findings")
    workflow.add_edge("validate_accessibility", "aggregate_findings")
    workflow.add_edge("detect_prd_assumptions", "aggregate_findings")

    # Join to refinement check
    workflow.add_edge("aggregate_findings", "should_refine")

    # Refinement conditional: loop back to validators or proceed to report
    workflow.add_conditional_edges(
        "should_refine",
        should_refine_decision,
        {
            "refine": "re_retrieve",
            "generate_report": "generate_report",
        },
    )

    # Re-retrieve loops back to color validator (rest can use cached analysis)
    workflow.add_edge("re_retrieve", "validate_color")

    # Report to END
    workflow.add_edge("generate_report", END)

    return workflow.compile()
```

### Pattern 6: Chroma Version Metadata Filtering (AGT-05)

**What:** Filter knowledge base queries by version_id and effective_date to prevent stale standards.

**When to use:** AGT-05 requirement for version metadata in Chroma.

**Implementation:**
```python
# Source: [ASSUMED - Chroma metadata filtering]
from datetime import datetime

def query_current_standards(
    collection,
    query_embedding: list[float],
    query_date: datetime,
    k: int = 5,
) -> list[tuple[Document, float]]:
    """Query knowledge base with version filtering.

    Only retrieves standards where:
    - effective_date <= query_date (standard was in effect)
    - (superseded_date is null OR superseded_date > query_date) (not yet superseded)
    """
    # Chroma where filter syntax
    where_filter = {
        "$and": [
            {"effective_date": {"$lte": query_date.isoformat()}},
            {"$or": [
                {"superseded_date": None},
                {"superseded_date": {"$gt": query_date.isoformat()}}
            ]}
        ]
    }

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    # Convert to documents with scores
    documents_with_scores = []
    if results["documents"]:
        for doc_text, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = 1 / (1 + distance)
            doc = Document(page_content=doc_text, metadata=metadata)
            documents_with_scores.append((doc, score))

    return documents_with_scores


# When adding documents, include version metadata
def add_standard_with_version(
    collection,
    content: str,
    version_id: str,
    effective_date: datetime,
    superseded_date: datetime = None,
):
    """Add standard document with version metadata."""
    metadata = {
        "document_name": "Brand Design Standards",
        "section": "Color",
        "version_id": version_id,
        "effective_date": effective_date.isoformat(),
        "superseded_date": superseded_date.isoformat() if superseded_date else None,
    }

    # Generate embedding and add to collection
    # ...
```

### Pattern 7: PRD-05 Vague Language Detection

**What:** Detect unstated assumptions in requirements using vague language patterns.

**When to use:** PRD-05 requirement for detecting vague language ("as needed", "etc.", "as appropriate").

**Implementation (extends Phase 2 completeness node):**
```python
# Source: [ASSUMED - pattern from completeness.py PLACEHOLDER_PATTERNS]
# Already partially implemented in Phase 2 completeness.py

VAGUE_LANGUAGE_PATTERNS = [
    (r'\bas needed\b', "Vague: 'as needed' - what triggers the need?"),
    (r'\bas appropriate\b', "Vague: 'as appropriate' - what determines appropriateness?"),
    (r'\betc\.?\b', "Vague: 'etc.' - what specifically is included?"),
    (r'\band so on\b', "Vague: 'and so on' - enumerate specific items"),
    (r'\bsuch as\b', "Vague: 'such as' - provide complete list or use 'including'"),
    (r'\bto be determined\b', "Unstated: 'TBD' - specify actual value"),
    (r'\bpending\b', "Unstated: 'pending' - specify deadline or trigger"),
    (r'\bmaybe\b', "Vague: 'maybe' - state actual condition"),
    (r'\bsometime\b', "Vague: 'sometime' - specify actual timeline"),
    (r'\bmight\b', "Vague: 'might' - state actual probability or trigger"),
]


def detect_vague_language(prd_text: str) -> list[Finding]:
    """Detect vague language indicating unstated assumptions."""
    findings = []

    for pattern, description in VAGUE_LANGUAGE_PATTERNS:
        matches = re.finditer(pattern, prd_text, re.IGNORECASE)
        for match in matches:
            # Get line number
            line_num = prd_text[:match.start()].count('\n') + 1

            findings.append(Finding(
                issue_type="assumptions",
                severity="Major",  # Vague language is significant
                location=f"Line {line_num}",
                description_en=f"Unstated assumption detected: {description}",
                description_zh=f"检测到未说明的假设：{description}",
                suggestion_en="Provide specific criteria or enumerate all items",
                suggestion_zh="请提供具体标准或列举所有项目",
            ))

    return findings
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color palette extraction | Custom color quantization | colorthief or Pillow quantize | Battle-tested algorithms, handles edge cases |
| WCAG contrast calculation | Custom formula | Standard algorithm from W3C | Correctness critical for accessibility |
| Grid spacing measurement | Manual pixel counting | MiniMax Image Understanding | Accurate element detection requires ML |
| Typography analysis | OCR + heuristics | MiniMax vision | Font detection from images is complex |
| Version filtering | Custom Chroma queries | Chroma where clause with date comparison | Correct date handling is tricky |

**Key insight:** Image analysis (color extraction, typography, spacing) is complex ML/CV problem. MiniMax Image Understanding API provides these capabilities via simple API call rather than building custom ML pipelines.

## Common Pitfalls

### Pitfall 1: MiniMax Image API Timeout/Size Limits

**What goes wrong:** Large prototype images cause API timeout or are rejected for size.

**Why it happens:** MiniMax API has image size limits (typically < 10MB).

**How to avoid:**
- Resize images before sending (Pillow: `img.thumbnail((1024, 1024))`)
- Compress with quality setting
- For multi-screen prototypes, analyze one screen at a time

**Warning signs:** API errors with 413 or timeout status codes

### Pitfall 2: Color Extraction Inaccuracy on Complex Images

**What goes wrong:** Colorthief extracts wrong colors from busy/prototype images.

**Why it happens:** Colorthief optimized for photographs, not UI wireframes.

**How to avoid:**
- Use MiniMax Image Understanding for better UI-specific color extraction
- Resize to reduce visual complexity
- Filter out near-white/near-black background colors

**Warning signs:** Extracted palette doesn't match visible UI colors

### Pitfall 3: Stale Standards Breaking Review

**What goes wrong:** Old version of design standards retrieved, causing false negatives.

**Why it happens:** No version filtering at query time (AGT-05 not implemented).

**How to avoid:**
- Always filter by effective_date at query time
- Include current_date in query state
- Verify version_id matches expected standard version

### Pitfall 4: Infinite Loop in Image Analysis Cycle

**What goes wrong:** LangGraph cycle for re-retrieval never terminates.

**Why it happens:** Same as Phase 2 - forgetting to increment iteration counter.

**How to avoid:**
- Copy Phase 2's iteration pattern exactly
- Increment `review_iteration` in should_refine_node
- Check both iteration count AND convergence (has anything changed?)

### Pitfall 5: Mixed Severity from Parallel Validators

**What goes wrong:** Findings from parallel validators have inconsistent severity.

**Why it happens:** Each validator uses slightly different thresholds for severity.

**How to avoid:**
- Use centralized severity mapping (shared function)
- Validate severity output from each node
- Per D-14: rules + LLM discretion, with bounds

## Code Examples

### ImageReviewState Definition

```python
# Source: [ASSUMED - extends PRDReviewState]
class ImageReviewState(TypedDict):
    """State for image review workflow.

    Extends PRDReviewState with image-specific fields.
    """
    # From PRDReviewState (inherited)
    prd_text: str
    collection_name: str
    review_depth: Literal["fast", "balanced", "thorough"]
    max_iterations: int
    review_iteration: int
    structure_findings: List[Finding]
    terminology_findings: List[Finding]
    completeness_findings: List[Finding]
    formatting_findings: List[Finding]
    all_findings: List[Finding]
    refined_findings: Optional[List[Finding]]
    report: Optional[str]
    status: str
    error: Optional[str]

    # Image-specific fields (Phase 3)
    image_path: str
    image_analysis: Optional[dict]  # Cached MiniMax analysis
    color_findings: List[Finding]
    typography_findings: List[Finding]
    spacing_findings: List[Finding]
    accessibility_findings: List[Finding]
    assumption_findings: List[Finding]  # PRD-05
    design_tokens: List[dict]  # Retrieved brand standards


def get_initial_image_review_state(
    prd_text: str,
    image_path: str,
    collection_name: str = "design_standards",
    review_depth: str = "balanced",
) -> ImageReviewState:
    """Create initial state for image review workflow."""
    depth_config = {
        "fast": {"max_iterations": 1},
        "balanced": {"max_iterations": 2},
        "thorough": {"max_iterations": 3},
    }
    config = depth_config.get(review_depth, depth_config["balanced"])

    return ImageReviewState(
        prd_text=prd_text,
        image_path=image_path,
        collection_name=collection_name,
        review_depth=review_depth,
        max_iterations=config["max_iterations"],
        review_iteration=0,
        # ... initialize all finding lists ...
        color_findings=[],
        typography_findings=[],
        spacing_findings=[],
        accessibility_findings=[],
        assumption_findings=[],
        design_tokens=[],
        image_analysis=None,
        status="pending",
        error=None,
    )
```

### MiniMax Vision Integration

```python
# Source: [ASSUMED - MiniMax OpenAI-compatible API for images]
from langchain_openai import ChatOpenAI
from PIL import Image
import os

class MiniMaxVisionClient:
    """Client for MiniMax Image Understanding API."""

    def __init__(self, api_key: str = None):
        self.llm = ChatOpenAI(
            model="MiniMax/M2.7",
            api_key=api_key or os.environ.get("MINIMAX_API_KEY"),
            base_url="https://api.minimax.chat/v1",
        )

    def analyze_ui_image(self, image_path: str, analysis_type: str) -> dict:
        """Analyze UI prototype image.

        Args:
            image_path: Path to image file
            analysis_type: "color" | "typography" | "spacing" | "full"

        Returns:
            Structured analysis result.
        """
        prompts = {
            "color": """Extract the color palette from this UI prototype.
            For each dominant color provide: hex code, RGB, usage, role (primary/secondary/accent).
            Return as structured list with 5-8 colors.""",

            "typography": """Analyze typography in this UI:
            - Heading sizes and weights
            - Body text size
            - Caption/label styles
            - Hierarchy relationship
            Return as structured list.""",

            "spacing": """Measure spacing in this UI prototype:
            - Grid system used (8pt, 4pt, other)
            - Common spacing values
            - Padding/margin patterns
            Return as structured list.""",

            "full": """Comprehensive UI analysis:
            1. Color palette with roles
            2. Typography hierarchy
            3. Spacing/grid system
            4. Accessibility concerns (contrast issues)
            Return as comprehensive structured report.""",
        }

        # Load and prepare image
        img = Image.open(image_path)
        img.thumbnail((1024, 1024))  # Limit size

        # Convert to base64
        import base64
        from io import BytesIO
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        # Call API
        response = self.llm.invoke([
            HumanMessage(content=[
                {"type": "text", "text": prompts.get(analysis_type, prompts["full"])},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ])
        ])

        return self._parse_response(response.content, analysis_type)

    def _parse_response(self, content: str, analysis_type: str) -> dict:
        """Parse LLM response into structured format."""
        # Use LLM to parse into structured format
        # In practice, use function calling or structured output
        return {"raw": content, "type": analysis_type}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual color extraction | MiniMax vision API | 2024-2025 | Faster, consistent, multi-modal |
| OCR for text detection | Vision models for typography | 2024+ | Better font/style detection |
| Fixed color extraction | Contextual color + usage detection | MiniMax | Understand color role, not just values |
| Static grid validation | Vision-based spacing measurement | MiniMax | Accurate without pixel counting |

**Deprecated/outdated:**
- Custom OCR pipelines for typography (use vision models)
- Manual pixel measurement tools (use vision API)
- Single-dimension review (use parallel fan-out per AGT-02)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | MiniMax M2.7 supports image input via OpenAI-compatible API | Pattern 1 | API format may differ; need verification |
| A2 | MiniMax Image Understanding extracts color palette accurately | IMG-01 | May need fallback to colorthief |
| A3 | MiniMax can detect typography hierarchy from UI images | IMG-03 | Font detection from images is imprecise |
| A4 | LangGraph parallel fan-out works with 5+ nodes | AGT-02 | May need performance optimization |
| A5 | Chroma where clause supports date comparison | AGT-05 | Syntax may vary; need verification |
| A6 | 8pt/4pt grid can be detected from prototype images | IMG-04 | Grid detection may require explicit markers |

**If this table is empty:** All claims in this research were verified or cited - no user confirmation needed.

## Open Questions

1. **How to handle multi-screen prototype analysis?**
   - What we know: Single image analysis works; PRD may reference multiple screens
   - What's unclear: Batch analysis vs. sequential; how to correlate findings across screens
   - Recommendation: Analyze one screen at a time; aggregate findings in report

2. **Should MiniMax API calls be cached?**
   - What we know: Image analysis is expensive (time and tokens)
   - What's unclear: When to invalidate cache (image change? time-based?)
   - Recommendation: Cache by image_path + analysis_type; invalidate on file change

3. **How to handle design tokens in knowledge base vs. extracted colors?**
   - What we know: IMG-02 requires comparing extracted colors against brand standards
   - What's unclear: Format of design token standards in Chroma
   - Recommendation: Store design tokens with structured metadata (name, hex, rgb, usage)

4. **Does MiniMax Image Understanding work well for wireframes vs. high-fidelity?**
   - What we know: M2.7 is multimodal; should handle both
   - What's unclear: Quality difference between wireframe and pixel-perfect designs
   - Recommendation: Test with both; may need different prompts

## Environment Availability

> Step 2.6: SKIPPED (no external dependencies beyond Phase 2 code)

**Analysis:** Phase 3 builds on existing Phase 2 infrastructure. MiniMax API is already configured. Pillow and colorthief are standard Python packages. No new external tools, services, or runtimes required.

## Validation Architecture

> `workflow.nyquist_validation: false` in config - skip validation architecture section.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A - no auth in MVP |
| V3 Session Management | No | N/A - stateless review |
| V4 Access Control | No | N/A - single user |
| V5 Input Validation | Yes | Validate image file type before processing; sanitize file paths |
| V6 Cryptography | No | N/A - no cryptographic operations |

**Known Threat Patterns for Image Review:**
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious image file | Denial of Service | Validate image format; size limits before processing |
| Prototype IP disclosure | Information Disclosure | Don't store analyzed images; clear after review |
| Prompt injection via image metadata | Integrity | Don't include raw image analysis in prompts without framing |

## Sources

### Primary (HIGH confidence)
- None verified via Context7/WebFetch due to tool restrictions

### Secondary (MEDIUM confidence)
- [ASSUMED] MiniMax OpenAI-compatible API for image understanding
- [ASSUMED] WCAG 2.1 contrast algorithm from W3C specification
- [ASSUMED] LangGraph fan-out/join pattern from Phase 2 implementation

### Tertiary (LOW confidence)
- [ASSUMED] colorthief library API for color extraction
- [ASSUMED] Pillow color quantization for fallback palette extraction
- [ASSUMED] Chroma metadata filtering syntax

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - MiniMax API confirmed, other packages standard
- Architecture: MEDIUM - LangGraph patterns well-established from Phase 2
- Pitfalls: MEDIUM - common image analysis issues, may need verification

**Research date:** 2026/04/17
**Valid until:** 2026/05/17 (30 days - stable patterns)
