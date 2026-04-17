"""PRD and image review workflow nodes."""

from src.workflow.nodes.structure import validate_structure_node
from src.workflow.nodes.terminology import validate_terminology_node
from src.workflow.nodes.completeness import validate_completeness_node
from src.workflow.nodes.formatting import validate_formatting_node
from src.workflow.nodes.aggregate import aggregate_findings_node, aggregate_image_findings_node

# Phase 3 image validators
from src.workflow.nodes.color import validate_color_node
from src.workflow.nodes.typography import validate_typography_node
from src.workflow.nodes.spacing import validate_spacing_node
from src.workflow.nodes.accessibility import validate_accessibility_node
from src.workflow.nodes.assumptions import detect_prd_assumptions_node

__all__ = [
    # Phase 2 PRD validators
    "validate_structure_node",
    "validate_terminology_node",
    "validate_completeness_node",
    "validate_formatting_node",
    "aggregate_findings_node",
    # Phase 3 image validators
    "validate_color_node",
    "validate_typography_node",
    "validate_spacing_node",
    "validate_accessibility_node",
    "detect_prd_assumptions_node",
    "aggregate_image_findings_node",
]
