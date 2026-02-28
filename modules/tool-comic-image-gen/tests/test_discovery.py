"""Tests for provider discovery logic."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from amplifier_module_comic_image_gen.providers import discover_image_backends


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


def test_ignores_non_image_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    # Clear env vars so the fallback doesn't kick in
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    providers = {
        "provider-anthropic": _make_provider("provider-anthropic"),
        "provider-ollama": _make_provider("provider-ollama"),
    }
    backends = discover_image_backends(providers)
    assert len(backends) == 0


def test_empty_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    # Clear env vars so the fallback doesn't kick in
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    backends = discover_image_backends({})
    assert len(backends) == 0


def test_discovery_does_not_accept_preferred_parameter() -> None:
    """preferred-provider sorting was moved to execute(); discovery is pure."""
    providers = {
        "provider-openai": _make_provider("provider-openai"),
        "provider-google": _make_provider("provider-google"),
    }
    # discover_image_backends no longer accepts a 'preferred' kwarg
    with pytest.raises(TypeError):
        discover_image_backends(providers, preferred="google")  # type: ignore[call-arg]


# -- Realistic provider names (matching ~/.amplifier/settings.yaml) ----------


def test_discovers_with_settings_yaml_key_names() -> None:
    """Provider keys from settings.yaml are plain names like 'openai', 'google'.

    The discovery must match these — not just 'provider-openai' style names.
    """
    providers = {
        "anthropic": _make_provider("anthropic"),
        "openai": _make_provider("openai"),
        "google": _make_provider("google"),
    }
    backends = discover_image_backends(providers)
    assert len(backends) == 2, (
        f"Expected 2 image backends (openai + google) from settings-style keys, "
        f"got {len(backends)}: {[b.provider.name for b in backends]}"
    )
    names = {b.provider.name for b in backends}
    assert names == {"openai", "google"}


def test_discovers_openai_bare_key() -> None:
    """A provider keyed as just 'openai' (no prefix) must be discovered."""
    providers = {"openai": _make_provider("openai")}
    backends = discover_image_backends(providers)
    assert len(backends) == 1
    assert backends[0].provider.name == "openai"


def test_discovers_google_bare_key() -> None:
    """A provider keyed as just 'google' (no prefix) must be discovered."""
    providers = {"google": _make_provider("google")}
    backends = discover_image_backends(providers)
    assert len(backends) == 1
    assert backends[0].provider.name == "google"


def test_ignores_anthropic_bare_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Anthropic is not an image provider — must not produce a backend."""
    # Clear env vars so the fallback doesn't kick in
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    providers = {"anthropic": _make_provider("anthropic")}
    backends = discover_image_backends(providers)
    assert len(backends) == 0


def test_env_fallback_discovers_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """When coordinator providers are empty, env-var fallback finds OpenAI."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    backends = discover_image_backends({})
    assert len(backends) == 1
    assert backends[0].provider.name == "openai"


def test_env_fallback_discovers_google(monkeypatch: pytest.MonkeyPatch) -> None:
    """When coordinator providers are empty, env-var fallback finds Gemini."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    backends = discover_image_backends({})
    assert len(backends) == 1
    assert backends[0].provider.name == "google"


def test_env_fallback_discovers_both(monkeypatch: pytest.MonkeyPatch) -> None:
    """When coordinator providers are empty, env-var fallback finds both."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    backends = discover_image_backends({})
    assert len(backends) == 2
    names = {b.provider.name for b in backends}
    assert names == {"openai", "google"}


def test_env_fallback_skipped_when_coordinator_has_backends() -> None:
    """Env-var fallback should NOT fire when coordinator already found backends."""
    providers = {"openai": _make_provider("openai")}
    backends = discover_image_backends(providers)
    # Should have exactly 1 from coordinator, env fallback not triggered
    assert len(backends) == 1
    assert backends[0].provider.name == "openai"
