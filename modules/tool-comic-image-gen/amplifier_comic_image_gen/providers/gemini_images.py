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

    @staticmethod
    def _build_content_config(
        prompt: str,
        reference_images: list[str] | None = None,
    ) -> tuple[Any, Any]:
        """Build (contents, config) for generate_content.

        Uses google.genai types when available, falling back to plain dicts.
        When *reference_images* are provided, they are prepended as inline_data
        parts before the text prompt for multimodal input.
        """
        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            )
            parts: list[Any] = []
            if reference_images:
                for img_path in reference_images:
                    image_bytes = Path(img_path).read_bytes()
                    parts.append(
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/png",
                                data=image_bytes,
                            )
                        )
                    )
            parts.append(types.Part(text=prompt))
            contents = types.Content(parts=parts)
        except (ImportError, ModuleNotFoundError):
            config = {"response_modalities": ["IMAGE", "TEXT"]}
            parts_list: list[dict[str, Any]] = []
            if reference_images:
                for img_path in reference_images:
                    image_bytes = Path(img_path).read_bytes()
                    parts_list.append(
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": base64.b64encode(image_bytes).decode(),
                            }
                        }
                    )
            parts_list.append({"text": prompt})
            contents = {"parts": parts_list}
        return contents, config

    async def generate(
        self,
        prompt: str,
        output_path: str | Path,
        size: str = "square",  # accepted for interface compatibility; Gemini ignores dimensions
        style: str | None = None,
        model: str = "gemini-2.0-flash-exp",
        reference_images: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate an image and write it to *output_path*.

        Returns a result dict with keys: success, provider_used, path, error.
        """
        out = Path(output_path)
        try:
            contents, config = self._build_content_config(prompt, reference_images)

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
                    raise TypeError(f"Unexpected inline_data.data type: {type(data)}")
        return None
