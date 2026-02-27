"""Tests for provider discovery logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from amplifier_comic_image_gen.providers import discover_image_backends


def _make_provider(name: str) -> MagicMock:
    """Create a minimal mock provider with .name and .client attributes."""
    p = MagicMock()
    p.name = name
    p.client = MagicMock()
    return p


def test_discovers_openai_provider() -> None:
    providers = {"provider-openai": _make_provider("provider-openai")}
    backends = discover_image_backends(providers)
    assert len(backends) == 1
    assert backends[0].provider.name == "provider-openai"


def test_discovers_google_provider() -> None:
    providers = {"provider-google": _make_provider("provider-google")}
    backends = discover_image_backends(providers)
    assert len(backends) == 1
    assert backends[0].provider.name == "provider-google"


def test_discovers_both_providers() -> None:
    providers = {
        "provider-openai": _make_provider("provider-openai"),
        "provider-google": _make_provider("provider-google"),
    }
    backends = discover_image_backends(providers)
    assert len(backends) == 2
    names = {b.provider.name for b in backends}
    assert names == {"provider-openai", "provider-google"}


def test_ignores_non_image_providers() -> None:
    providers = {
        "provider-anthropic": _make_provider("provider-anthropic"),
        "provider-ollama": _make_provider("provider-ollama"),
    }
    backends = discover_image_backends(providers)
    assert len(backends) == 0


def test_empty_providers() -> None:
    backends = discover_image_backends({})
    assert len(backends) == 0


def test_preferred_provider_ordering() -> None:
    providers = {
        "provider-openai": _make_provider("provider-openai"),
        "provider-google": _make_provider("provider-google"),
    }
    backends = discover_image_backends(providers, preferred="google")
    assert backends[0].provider.name == "provider-google"
    assert backends[1].provider.name == "provider-openai"
