"""Provider discovery — BRIDGE MODULE for Issue #90.

Hardcoded provider-name matching to map configured Amplifier providers
to the appropriate image generation backend classes.

Falls back to direct API-key discovery from environment variables when
the coordinator does not expose providers (e.g. the tool module loads
before providers are mounted).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
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


# ---------------------------------------------------------------------------
# Lightweight provider shim for env-var fallback
# ---------------------------------------------------------------------------


@dataclass
class _EnvProvider:
    """Minimal provider facade built from an environment variable API key.

    Backends only need ``provider.name`` and ``provider.client``.
    The client is lazily created on first access so import-time failures
    are deferred until the backend actually tries to generate an image.
    """

    name: str
    _api_key: str
    _client: Any = field(default=None, init=False, repr=False)
    _base_url: str | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = self._make_client()
        return self._client

    def _make_client(self) -> Any:
        raise NotImplementedError


class _OpenAIEnvProvider(_EnvProvider):
    """Creates an AsyncOpenAI client from OPENAI_API_KEY."""

    def _make_client(self) -> Any:
        from openai import AsyncOpenAI  # type: ignore[reportMissingImports]

        kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return AsyncOpenAI(**kwargs)


class _GeminiEnvProvider(_EnvProvider):
    """Creates a google.genai.Client from GOOGLE_API_KEY."""

    def _make_client(self) -> Any:
        from google import genai  # type: ignore[reportMissingImports,reportAttributeAccessIssue]

        return genai.Client(api_key=self._api_key)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _discover_from_env() -> list[ImageBackend]:
    """Fallback: build backends directly from environment API keys."""
    backends: list[ImageBackend] = []

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        try:
            prov = _OpenAIEnvProvider(
                name="openai",
                _api_key=openai_key,
                _base_url=os.environ.get("OPENAI_BASE_URL"),
            )
            backends.append(OpenAIImageBackend(prov))
            logger.info("generate_image: created OpenAI backend from OPENAI_API_KEY")
        except Exception:
            logger.warning(
                "generate_image: OPENAI_API_KEY is set but OpenAI client init failed",
                exc_info=True,
            )

    google_key = os.environ.get("GOOGLE_API_KEY", "")
    if google_key:
        try:
            prov = _GeminiEnvProvider(name="google", _api_key=google_key)
            backends.append(GeminiImageBackend(prov))
            logger.info("generate_image: created Gemini backend from GOOGLE_API_KEY")
        except Exception:
            logger.warning(
                "generate_image: GOOGLE_API_KEY is set but Gemini client init failed",
                exc_info=True,
            )

    return backends


def discover_image_backends(
    providers: dict[str, Any],
) -> list[ImageBackend]:
    """Discover image-capable backends from the available providers.

    Iterates *providers*, matching provider names against known keys in
    ``_PROVIDER_BACKEND_MAP``.  Returns instantiated backend objects.

    If no backends are found via the coordinator, falls back to creating
    clients directly from ``OPENAI_API_KEY`` / ``GOOGLE_API_KEY``
    environment variables.

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

    # Fallback: try environment variables when coordinator gave us nothing
    if not backends:
        provider_keys = list(providers.keys()) if providers else []
        logger.info(
            "generate_image: no backends from coordinator providers (keys: %s). "
            "Trying env-var fallback (OPENAI_API_KEY, GOOGLE_API_KEY)...",
            provider_keys or "(empty)",
        )
        backends = _discover_from_env()

    if not backends:
        logger.warning(
            "No image generation backends discovered from providers or environment. "
            "Neither coordinator providers nor OPENAI_API_KEY/GOOGLE_API_KEY yielded "
            "a usable backend. Comics CANNOT be created without image generation access.",
        )

    return backends
