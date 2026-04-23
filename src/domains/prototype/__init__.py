"""Prototype Domain - Prototype image review bounded context.

Entities:
- Prototype: A prototype consisting of one or more screens
- Screen: A single screen in the prototype
- Component: A UI component within a screen

Services:
- VisionAnalyzer: Analyzes prototype using MiniMax Vision
- LayoutValidator: Validates 8pt grid and spacing
- AccessibilityChecker: Checks WCAG compliance
"""

from .entities import Prototype, Screen, Component
from .services import VisionAnalyzer, LayoutValidator, AccessibilityChecker

__all__ = [
    "Prototype",
    "Screen",
    "Component",
    "VisionAnalyzer",
    "LayoutValidator",
    "AccessibilityChecker",
]
