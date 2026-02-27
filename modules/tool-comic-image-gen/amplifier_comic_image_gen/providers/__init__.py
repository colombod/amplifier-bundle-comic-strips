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

# Union of all supported image backends
ImageBackend = OpenAIImageBackend | GeminiImageBackend

_PROVIDER_BACKEND_MAP: dict[str, type[ImageBackend]] = {
    "openai": OpenAIImageBackend,
    "google": GeminiImageBackend,
    "gemini": GeminiImageBackend,
}


def discover_image_backends(
    providers: dict[str, Any],
) -> list[ImageBackend]:
    """Discover image-capable backends from the available providers.

    Iterates *providers*, matching provider names against known keys in
    ``_PROVIDER_BACKEND_MAP``.  Returns instantiated backend objects.

    Note: preferred-provider ordering is handled by
    :meth:`ComicImageGenTool.execute` at call time, not at discovery time.
    """
    backends: list[ImageBackend] = []

    for provider_name, provider in providers.items():
        name_lower = provider_name.lower()
        for key, backend_cls in _PROVIDER_BACKEND_MAP.items():
            if key in name_lower:
                backends.append(backend_cls(provider))
                break  # avoid matching same provider twice

    if not backends:
        logger.warning("No image generation backends discovered from providers")

    return backends
