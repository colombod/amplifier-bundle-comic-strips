"""OpenAI image generation backend — BRIDGE MODULE for Issue #90.

Wraps the OpenAI Images API (gpt-image-1, DALL-E 3/2) behind a
provider-agnostic generate() interface used by the comic image tool.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any


ASPECT_RATIO_MAP: dict[str, str] = {
    "landscape": "1536x1024",
    "portrait": "1024x1536",
    "square": "1024x1024",
}

_EDIT_CAPABLE_MODELS: set[str] = {
    "gpt-image-1.5",
    "gpt-image-1",
    "gpt-image-1-mini",
    "dall-e-2",
}


class OpenAIImageBackend:
    """Generate images via an Amplifier OpenAI provider."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        self.client = provider.client

    async def generate(
        self,
        prompt: str,
        output_path: str | Path,
        size: str = "square",
        style: str | None = None,
        model: str = "gpt-image-1",
        reference_images: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate an image and write it to *output_path*.

        *size* is an aspect ratio name (landscape, portrait, square) which is
        mapped to pixel dimensions via :data:`ASPECT_RATIO_MAP`.

        When *reference_images* are provided and *model* supports editing,
        routes to ``images.edit`` instead of ``images.generate``.  Models in
        :data:`_EDIT_CAPABLE_MODELS` support editing; dall-e-3 does **not**,
        so it falls back to ``images.generate`` (dropping refs).

        Returns a result dict with keys: success, provider_used, path, error.
        """
        out = Path(output_path)
        try:
            pixel_size = ASPECT_RATIO_MAP.get(size, ASPECT_RATIO_MAP["square"])

            use_edit = bool(reference_images) and model in _EDIT_CAPABLE_MODELS

            if use_edit:
                response = await self._call_edit(
                    model=model,
                    prompt=prompt,
                    pixel_size=pixel_size,
                    reference_images=reference_images,  # type: ignore[arg-type]
                )
            else:
                response = await self._call_generate(
                    model=model,
                    prompt=prompt,
                    pixel_size=pixel_size,
                    style=style,
                )

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

    async def _call_generate(
        self,
        *,
        model: str,
        prompt: str,
        pixel_size: str,
        style: str | None,
    ) -> Any:
        """Call ``client.images.generate`` (no reference images)."""
        kwargs: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "size": pixel_size,
            "response_format": "b64_json",
            "quality": "high",
        }
        if style is not None and model == "dall-e-3":
            kwargs["style"] = style
        return await self.client.images.generate(**kwargs)

    async def _call_edit(
        self,
        *,
        model: str,
        prompt: str,
        pixel_size: str,
        reference_images: list[str],
    ) -> Any:
        """Call ``client.images.edit`` with reference image file bytes."""
        image_bytes_list = [Path(p).read_bytes() for p in reference_images]
        return await self.client.images.edit(
            model=model,
            prompt=prompt,
            image=image_bytes_list,
            size=pixel_size,
            response_format="b64_json",
            quality="high",
        )
