"""Provider discovery — BRIDGE MODULE for Issue #90.

Hardcoded provider-name matching to map configured Amplifier providers
to the appropriate image generation backend classes.
"""

from __future__ import annotations

import logging
from typing import Any

from .gemini_images import GeminiImageBackend
from .openai_images import OpenAIImageBackend

logger = logging.getLogger(__name__)

ImageBackend = OpenAIImageBackend | GeminiImageBackend

_PROVIDER_BACKEND_MAP: dict[str, type[ImageBackend]] = {
    "openai": OpenAIImageBackend,
    "google": GeminiImageBackend,
    "gemini": GeminiImageBackend,
}


def discover_image_backends(
    providers: dict[str, Any],
    preferred: str | None = None,
) -> list[ImageBackend]:
    """Discover image-capable backends from the available providers.

    Iterates *providers*, matching provider names against known keys in
    ``_PROVIDER_BACKEND_MAP``.  Returns instantiated backend objects.

    If *preferred* is set and more than one backend is found, the list is
    sorted so that the preferred provider appears first.
    """
    backends: list[ImageBackend] = []

    for provider_name, provider in providers.items():
        name_lower = provider_name.lower()
        for key, backend_cls in _PROVIDER_BACKEND_MAP.items():
            if key in name_lower:
                backends.append(backend_cls(provider))
                break  # avoid matching same provider twice

    if preferred is not None and len(backends) > 1:
        preferred_lower = preferred.lower()
        backends.sort(key=lambda b: preferred_lower not in b.provider.name.lower())

    if not backends:
        logger.warning("No image generation backends discovered from providers")

    return backends
