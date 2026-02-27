"""Shared test fixtures and constants for tool-comic-image-gen tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

# 1x1 red PNG encoded as base64 — used by OpenAI and tool tests
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"


def make_openai_provider(name: str = "provider-openai") -> MagicMock:
    """Create a mock provider mimicking the Amplifier OpenAI provider."""
    provider = MagicMock()
    provider.name = name

    response = MagicMock()
    response.data = [MagicMock(b64_json=TINY_PNG_B64)]

    provider.client.images.generate = AsyncMock(return_value=response)
    return provider
