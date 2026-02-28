"""Shared test fixtures and constants for tool-comic-image-gen tests."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock

# 1x1 red PNG encoded as base64 — used by OpenAI, Gemini, and tool tests
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"

# Same image as raw bytes — derived from the shared base64 constant
TINY_PNG_BYTES = base64.b64decode(TINY_PNG_B64)


def make_openai_provider(name: str = "provider-openai") -> MagicMock:
    """Create a mock provider mimicking the Amplifier OpenAI provider."""
    provider = MagicMock()
    provider.name = name

    response = MagicMock()
    response.data = [MagicMock(b64_json=TINY_PNG_B64)]

    provider.client.images.generate = AsyncMock(return_value=response)
    provider.client.images.edit = AsyncMock(return_value=response)
    return provider


def make_gemini_provider(name: str = "provider-google") -> MagicMock:
    """Create a mock provider mimicking the Amplifier Google/Gemini provider."""
    provider = MagicMock()
    provider.name = name

    # Build response: candidates[0].content.parts = [text_part, image_part]
    text_part = MagicMock()
    text_part.inline_data = None
    text_part.text = "Here is the generated image."

    image_part = MagicMock()
    image_part.inline_data.data = TINY_PNG_BYTES
    image_part.inline_data.mime_type = "image/png"
    image_part.text = None

    candidate = MagicMock()
    candidate.content.parts = [text_part, image_part]

    response = MagicMock()
    response.candidates = [candidate]

    provider.client.aio.models.generate_content = AsyncMock(return_value=response)
    return provider


def make_gemini_imagen_provider(name: str = "provider-google") -> MagicMock:
    """Create a mock provider mimicking Gemini Imagen (generateImages endpoint)."""
    provider = MagicMock()
    provider.name = name

    # Build response: generated_images[0].image.image_bytes = TINY_PNG_BYTES
    generated_image = MagicMock()
    generated_image.image.image_bytes = TINY_PNG_BYTES

    response = MagicMock()
    response.generated_images = [generated_image]

    provider.client.aio.models.generate_images = AsyncMock(return_value=response)
    # Also provide generate_content so we can assert it was NOT called
    provider.client.aio.models.generate_content = AsyncMock()
    return provider
