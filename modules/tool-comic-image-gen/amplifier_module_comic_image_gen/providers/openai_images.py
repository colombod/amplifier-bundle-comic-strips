"""OpenAI image generation backend — BRIDGE MODULE for Issue #90.

Wraps the OpenAI Images API (gpt-image-1, DALL-E 3/2) behind a
provider-agnostic generate() interface used by the comic image tool.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import random
from pathlib import Path
from typing import Any

import openai  # pyright: ignore[reportMissingImports]

logger = logging.getLogger(__name__)


ASPECT_RATIO_MAP: dict[str, str] = {
    "landscape": "1536x1024",
    "portrait": "1024x1536",
    "square": "1024x1024",
}

_EDIT_CAPABLE_MODELS: frozenset[str] = frozenset(
    {
        "gpt-image-1.5",
        "gpt-image-1",
        "gpt-image-1-mini",
        "dall-e-2",
    }
)

# Models that require the legacy ``response_format`` kwarg (not ``output_format``).
# Only classic DALL-E models use this parameter; gpt-image-* and unknown models must not.
_DALLE_RESPONSE_FORMAT_MODELS: frozenset[str] = frozenset({"dall-e-3"})

_MAX_ATTEMPTS: int = 3

_RETRYABLE: tuple[type[Exception], ...] = (
    openai.RateLimitError,
    openai.APIStatusError,
)

_NON_RETRYABLE: tuple[type[Exception], ...] = (
    openai.AuthenticationError,
    openai.PermissionDeniedError,
    openai.BadRequestError,
    openai.UnprocessableEntityError,
)


class OpenAIImageBackend:
    """Generate images via an Amplifier OpenAI provider."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        self.client = provider.client

    @property
    def provider_type(self) -> str:
        """Return the provider type identifier."""
        return "openai"

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

        Retries up to :data:`_MAX_ATTEMPTS` times on retryable errors
        (e.g. 429 RateLimitError) with exponential backoff + jitter.
        Non-retryable errors (401, 403, 400, 422) fail immediately.

        Returns a result dict with keys: success, provider_used, path, error.
        """
        out = Path(output_path)
        pixel_size = ASPECT_RATIO_MAP.get(size, ASPECT_RATIO_MAP["square"])
        use_edit = bool(reference_images) and model in _EDIT_CAPABLE_MODELS

        for attempt in range(_MAX_ATTEMPTS):
            try:
                if use_edit:
                    response = await self._call_edit(
                        model=model,
                        prompt=prompt,
                        pixel_size=pixel_size,
                        reference_images=reference_images,  # type: ignore[arg-type]  # narrowed by use_edit check above
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

            # NOTE: _NON_RETRYABLE must be caught before _RETRYABLE — AuthenticationError
            # and PermissionDeniedError are APIStatusError subclasses and would be silently
            # retried if the order were reversed.
            except _NON_RETRYABLE as exc:
                logger.exception(
                    "OpenAI image generation failed (non-retryable) for model %s", model
                )
                return {
                    "success": False,
                    "provider_used": self.provider.name,
                    "path": str(out),
                    "error": str(exc),
                }

            except _RETRYABLE as exc:
                if attempt == _MAX_ATTEMPTS - 1:
                    # Final attempt exhausted — give up
                    logger.exception(
                        "OpenAI image generation failed after %d attempts for model %s",
                        _MAX_ATTEMPTS,
                        model,
                    )
                    return {
                        "success": False,
                        "provider_used": self.provider.name,
                        "path": str(out),
                        "error": str(exc),
                    }
                delay = 2**attempt + random.uniform(0, 1)
                logger.warning(
                    "OpenAI rate limited (attempt %d/%d), retrying in %.2fs",
                    attempt + 1,
                    _MAX_ATTEMPTS,
                    delay,
                )
                await asyncio.sleep(delay)

            except Exception as exc:
                logger.exception("OpenAI image generation failed for model %s", model)
                return {
                    "success": False,
                    "provider_used": self.provider.name,
                    "path": str(out),
                    "error": str(exc),
                }

        # Should never be reached, but satisfies type checker
        return {  # pragma: no cover
            "success": False,
            "provider_used": self.provider.name,
            "path": str(out),
            "error": "Exceeded maximum retry attempts",
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
            "quality": "high",
        }
        # gpt-image-1 family: returns base64; uses output_format, not response_format.
        # DALL-E 3: legacy response_format kwarg.
        # Unknown/future models: omit both — the API decides.
        if model in _EDIT_CAPABLE_MODELS:
            kwargs["output_format"] = "png"
        elif model in _DALLE_RESPONSE_FORMAT_MODELS:
            kwargs["response_format"] = "b64_json"
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
        # Use asyncio.to_thread to avoid blocking the event loop during disk I/O
        image_bytes_list = [
            await asyncio.to_thread(Path(p).read_bytes) for p in reference_images
        ]
        kwargs: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "image": image_bytes_list,
            "size": pixel_size,
            "quality": "high",
        }
        # gpt-image-1 always returns base64; doesn't accept response_format.
        # Defensive: _call_edit is only invoked when model is in _EDIT_CAPABLE_MODELS,
        # so this branch is currently unreachable — kept for future call-site safety.
        if model not in _EDIT_CAPABLE_MODELS:
            kwargs["response_format"] = "b64_json"
        return await self.client.images.edit(**kwargs)
