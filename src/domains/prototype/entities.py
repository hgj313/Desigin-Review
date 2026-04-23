"""Prototype Domain - Prototype image entities.

Entities:
- Prototype: A prototype consisting of one or more screens
- Screen: A single screen in the prototype
- Component: A UI component within a screen

References:
- ARCHITECTURE.md: Prototype Context section
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Component:
    """A UI component within a screen.

    Attributes:
        type: Component type (button, input, card, etc.)
        bounds: (x, y, width, height) tuple
        style: Component style properties
        label: Optional text label on the component
    """
    type: str
    bounds: tuple[int, int, int, int]  # x, y, w, h
    style: dict = field(default_factory=dict)
    label: Optional[str] = None

    @property
    def x(self) -> int:
        return self.bounds[0]

    @property
    def y(self) -> int:
        return self.bounds[1]

    @property
    def width(self) -> int:
        return self.bounds[2]

    @property
    def height(self) -> int:
        return self.bounds[3]


@dataclass
class Screen:
    """A single screen in a prototype.

    Attributes:
        name: Screen name (e.g., "Login Screen", "Home Page")
        components: List of components on this screen
        image_path: Path to the screenshot if available
    """
    name: str
    components: list[Component] = field(default_factory=list)
    image_path: Optional[str] = None

    def get_component_by_type(self, component_type: str) -> list[Component]:
        """Get all components of a specific type."""
        return [c for c in self.components if c.type == component_type]


@dataclass
class Prototype:
    """A prototype consisting of multiple screens.

    Attributes:
        image_paths: List of paths to prototype images
        screens: Parsed screens (populated after Vision analysis)
        metadata: Additional metadata
        document_type: Always "prototype"
    """
    image_paths: list[str]
    screens: list[Screen] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    document_type: str = "prototype"
    ingested_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_images(cls, image_paths: list[str], metadata: Optional[dict] = None) -> "Prototype":
        """Create Prototype from list of image paths.

        Args:
            image_paths: List of paths to prototype images
            metadata: Optional metadata dict

        Returns:
            Prototype instance
        """
        return cls(
            image_paths=image_paths,
            metadata=metadata or {},
        )

    def add_screen(self, screen: Screen) -> None:
        """Add a screen to the prototype."""
        self.screens.append(screen)

    def get_screen_by_name(self, name: str) -> Optional[Screen]:
        """Get screen by name."""
        for screen in self.screens:
            if screen.name.lower() == name.lower():
                return screen
        return None
