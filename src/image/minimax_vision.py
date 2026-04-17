"""MiniMax Vision client for image understanding.

Uses MiniMax Image Understanding API via OpenAI-compatible endpoint
per D-20 (OpenAI-compatible API at https://api.minimax.chat/v1).

References:
- D-20: MiniMax Image Understanding via OpenAI-compatible API
- D-21: Image resize to max 1024x1024 before encoding
"""

import os
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from PIL import Image


class MiniMaxVisionClient:
    """Client for MiniMax Image Understanding API per D-20.

    Uses OpenAI-compatible API endpoint at https://api.minimax.chat/v1.
    Same base URL as MiniMax LLM - unified API access.

    Attributes:
        llm: ChatOpenAI instance configured for MiniMax.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize MiniMax Vision client.

        Args:
            api_key: MiniMax API key. Defaults to MINIMAX_API_KEY env var.
        """
        self.llm = ChatOpenAI(
            model="MiniMax/M2.7",
            api_key=api_key or os.environ.get("MINIMAX_API_KEY"),
            base_url="https://api.minimax.chat/v1",
        )

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 string per D-21.

        Args:
            image_path: Path to image file.

        Returns:
            Base64-encoded image string.
        """
        img = Image.open(image_path)

        # Resize to max 1024x1024 per D-21
        img.thumbnail((1024, 1024))

        # Encode to PNG
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    def analyze_ui_image(
        self,
        image_path: str,
        analysis_type: str = "full",
    ) -> dict:
        """Analyze UI prototype image with MiniMax Vision.

        Args:
            image_path: Path to image file.
            analysis_type: Type of analysis - "color", "typography", "spacing", "accessibility", "full".

        Returns:
            dict with analysis results keyed by aspect type.
        """
        # Define prompts for each analysis type
        prompts = {
            "color": """Extract the color palette from this UI prototype.
For each dominant color provide:
1. Hex code
2. RGB values
3. Usage location (button, background, text, etc.)
4. Whether it appears to be a primary, secondary, or accent color

Return as structured list with 5-8 colors.""",

            "typography": """Analyze the typography in this UI prototype:
1. Identify heading styles (font size, weight, line height)
2. Identify body text styles
3. Identify caption/label styles
4. Note the hierarchy relationship (H1 > H2 > body > caption)
5. Estimate font family if identifiable

Return as structured list.""",

            "spacing": """Measure spacing in this UI prototype:
1. Grid system used (8pt, 4pt, or other)
2. Common spacing values between elements
3. Padding and margin patterns
4. Whether elements align to a grid

Return as structured list.""",

            "accessibility": """Check accessibility in this UI prototype:
1. Identify text and background color combinations
2. Note any areas that may have low contrast
3. Identify text sizes for contrast evaluation

Return as list of text/background pairs with locations.""",

            "full": """Comprehensive UI analysis of this prototype:
1. Color palette with hex codes, RGB, and usage roles
2. Typography hierarchy with sizes, weights, and relationships
3. Spacing/grid system used (8pt, 4pt, or other)
4. Accessibility concerns (contrast issues, text sizes)
5. Layout structure and alignment patterns

Return as comprehensive structured report.""",
        }

        prompt = prompts.get(analysis_type, prompts["full"])

        # Encode image
        image_b64 = self._encode_image(image_path)

        # Call API
        response = self.llm.invoke([
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }
        ])

        return {
            "analysis_type": analysis_type,
            "raw_response": response.content,
            "image_path": image_path,
        }

    def extract_color_palette(self, image_path: str) -> list[dict]:
        """Extract color palette from prototype image per IMG-01.

        Args:
            image_path: Path to prototype image.

        Returns:
            List of color dicts with hex, rgb, usage, role.
        """
        result = self.analyze_ui_image(image_path, "color")
        # Parse raw response into structured format
        # For now, return raw - will be parsed in validator node
        return [{"raw": result["raw_response"]}]

    def analyze_typography(self, image_path: str) -> list[dict]:
        """Analyze typography hierarchy per IMG-03.

        Args:
            image_path: Path to prototype image.

        Returns:
            List of typography elements with sizes, weights, hierarchy.
        """
        result = self.analyze_ui_image(image_path, "typography")
        return [{"raw": result["raw_response"]}]

    def measure_spacing(self, image_path: str) -> list[dict]:
        """Measure spacing and grid alignment per IMG-04.

        Args:
            image_path: Path to prototype image.

        Returns:
            List of spacing measurements.
        """
        result = self.analyze_ui_image(image_path, "spacing")
        return [{"raw": result["raw_response"]}]

    def check_accessibility(self, image_path: str) -> list[dict]:
        """Check accessibility compliance per IMG-05.

        Args:
            image_path: Path to prototype image.

        Returns:
            List of accessibility findings.
        """
        result = self.analyze_ui_image(image_path, "accessibility")
        return [{"raw": result["raw_response"]}]


__all__ = ["MiniMaxVisionClient"]