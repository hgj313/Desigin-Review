"""Shared Kernel - entities shared across all bounded contexts.

Entities:
- Finding: Canonical finding structure for violations
- Severity: Severity level with label and weight
- SeverityLevel: Enum for severity levels
- ReviewDimension: Enum for review dimensions
"""

from .entities import (
    Finding,
    Severity,
    SeverityLevel,
    ReviewDimension,
)

__all__ = [
    "Finding",
    "Severity",
    "SeverityLevel",
    "ReviewDimension",
]
