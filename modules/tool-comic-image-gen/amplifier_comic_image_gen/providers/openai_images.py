"""OpenAI image generation backend — BRIDGE MODULE for Issue #90.

Wraps the OpenAI Images API (gpt-image-1, DALL-E 3/2) behind a
provider-agnostic generate() interface used by the comic image tool.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any


OPENAI_IMAGE_MODELS = ["gpt-image-1", "dall-e-3", "dall-e-2"]


class OpenAIImageBackend:
    """Generate images via an Amplifier OpenAI provider."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        self.client = provider.client

    async def generate(
        self,
        prompt: str,
        output_path: str | Path,
        size: str = "1024x1024",
        style: str | None = None,
        model: str = "gpt-image-1",
    ) -> dict[str, Any]:
        """Generate an image and write it to *output_path*.

        Returns a result dict with keys: success, provider_used, path, error.
        """
        out = Path(output_path)
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "response_format": "b64_json",
                "quality": "high",
            }
            if style is not None and model == "dall-e-3":
                kwargs["style"] = style

            response = await self.client.images.generate(**kwargs)

            image_bytes = base64.b64decode(response.data[0].b64_json)
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
