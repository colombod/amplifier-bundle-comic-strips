"""Gemini image generation backend — BRIDGE MODULE for Issue #90.

Wraps the Google Gemini generative AI API behind a provider-agnostic
generate() interface used by the comic image tool.  Uses
client.aio.models.generate_content() with response_modalities=['IMAGE', 'TEXT']
to request inline image data from Gemini's multimodal models.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any


class GeminiImageBackend:
    """Generate images via an Amplifier Google/Gemini provider."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        self.client = provider.client

    async def generate(
        self,
        prompt: str,
        output_path: str | Path,
        size: str = "1024x1024",  # ignored — Gemini doesn't support explicit dimensions
        style: str | None = None,
        model: str = "gemini-2.0-flash-exp",
    ) -> dict[str, Any]:
        """Generate an image and write it to *output_path*.

        Returns a result dict with keys: success, provider_used, path, error.
        """
        out = Path(output_path)
        try:
            # Try to import google.genai types for proper config objects
            try:
                from google.genai import types

                config = types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
                contents = types.Content(
                    parts=[types.Part(text=prompt)],
                )
            except (ImportError, ModuleNotFoundError):
                # Fall back to dict-based config if google.genai is unavailable
                config = {"response_modalities": ["IMAGE", "TEXT"]}  # type: ignore[assignment]
                contents = {"parts": [{"text": prompt}]}  # type: ignore[assignment]

            response = await self.client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            image_bytes = self._extract_image(response)
            if image_bytes is None:
                return {
                    "success": False,
                    "provider_used": self.provider.name,
                    "path": str(out),
                    "error": "No image part found in Gemini response",
                }

            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(image_bytes)

            return {
                "success": True,
                "provider_used": self.provider.name,
                "path": str(out),
                "error": None,
            }
        except Exception as exc:
            return {
                "success": False,
                "provider_used": self.provider.name,
                "path": str(out),
                "error": str(exc),
            }

    @staticmethod
    def _extract_image(response: Any) -> bytes | None:
        """Extract the first image from a Gemini response.

        Iterates response.candidates[*].content.parts[*] and returns
        the raw bytes of the first part with non-None inline_data.
        Handles both raw bytes and base64-encoded string data.
        """
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.inline_data is not None:
                    data = part.inline_data.data
                    if isinstance(data, bytes):
                        return data
                    # Handle base64-encoded string case
                    if isinstance(data, str):
                        return base64.b64decode(data)
                    return bytes(data)
        return None
