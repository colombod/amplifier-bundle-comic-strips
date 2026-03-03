"""Shared pytest fixtures for tool-comic-create tests."""

from __future__ import annotations

import asyncio
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import pytest_asyncio

from amplifier_module_comic_assets.service import ComicProjectService
from amplifier_module_comic_assets.storage import FileSystemStorage

_MINIMAL_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


# ---------------------------------------------------------------------------
# Mock vision provider — follows the REAL Amplifier Provider protocol.
# No MagicMock: any interface mismatch (renamed method, wrong signature)
# is caught immediately instead of silently passing.
# ---------------------------------------------------------------------------


class MockVisionProvider:
    """Follows the real Amplifier Provider protocol for vision testing."""

    __test__ = False  # prevent pytest from treating this as a test class

    def __init__(
        self, response_text: str = '{"passed": true, "feedback": "Looks good."}'
    ) -> None:
        self.name = "mock-vision"
        self.response_text = response_text
        self.call_count = 0
        self.last_request: Any = None

    def get_info(self) -> Any:
        return type("ProviderInfo", (), {
            "capabilities": ["vision"],
            "capability_tags": ["vision"],
        })()

    async def list_models(self) -> list[Any]:
        return [
            type("ModelInfo", (), {
                "id": "mock-vision-model",
                "capabilities": ["vision"],
                "capability_tags": ["vision"],
            })()
        ]

    async def complete(self, request: Any) -> Any:
        self.call_count += 1
        self.last_request = request
        text_block = type("TextBlock", (), {"type": "text", "text": self.response_text})()
        return type("ChatResponse", (), {"content": [text_block]})()


class MockCoordinator:
    """Simulates coordinator.get() for testing — no MagicMock."""

    __test__ = False  # prevent pytest from treating this as a test class

    def __init__(
        self,
        vision_provider: MockVisionProvider | None = None,
        tools: dict[str, Any] | None = None,
    ) -> None:
        self._providers: dict[str, Any] = {}
        self._tools: dict[str, Any] = tools or {}
        if vision_provider is not None:
            self._providers["mock-vision"] = vision_provider

    def get(self, mount_point: str, name: str | None = None) -> Any:
        if mount_point == "providers":
            return self._providers
        if mount_point == "tools":
            return self._tools
        return None


# ---------------------------------------------------------------------------
# Stub amplifier_core.message_models for tests that exercise the full
# provider path.  amplifier_core is not installed in the test environment
# so we patch sys.modules with minimal stubs that satisfy _call_vision_api.
# ---------------------------------------------------------------------------


class _ImageBlock:
    def __init__(self, type: str, source: dict[str, str]) -> None:
        self.type = type
        self.source = source


class _TextBlock:
    def __init__(self, type: str, text: str) -> None:
        self.type = type
        self.text = text


class _Message:
    def __init__(self, role: str, content: list[Any]) -> None:
        self.role = role
        self.content = content


class _ChatRequest:
    def __init__(
        self,
        messages: list[Any],
        model: Any = None,
        max_output_tokens: int | None = None,
    ) -> None:
        self.messages = messages
        self.model = model
        self.max_output_tokens = max_output_tokens


@pytest.fixture()
def patch_message_models():
    """Patch sys.modules to provide stub amplifier_core.message_models.

    Needed for tests that exercise the full _call_vision_api → provider.complete()
    path when amplifier_core is not installed in the test environment.
    """
    msg_module = types.ModuleType("amplifier_core.message_models")
    msg_module.ImageBlock = _ImageBlock  # type: ignore[attr-defined]
    msg_module.TextBlock = _TextBlock  # type: ignore[attr-defined]
    msg_module.Message = _Message  # type: ignore[attr-defined]
    msg_module.ChatRequest = _ChatRequest  # type: ignore[attr-defined]

    core_module = types.ModuleType("amplifier_core")
    core_module.message_models = msg_module  # type: ignore[attr-defined]

    orig_core = sys.modules.get("amplifier_core")
    orig_msgs = sys.modules.get("amplifier_core.message_models")

    sys.modules["amplifier_core"] = core_module
    sys.modules["amplifier_core.message_models"] = msg_module

    yield

    if orig_core is None:
        sys.modules.pop("amplifier_core", None)
    else:
        sys.modules["amplifier_core"] = orig_core

    if orig_msgs is None:
        sys.modules.pop("amplifier_core.message_models", None)
    else:
        sys.modules["amplifier_core.message_models"] = orig_msgs


# ---------------------------------------------------------------------------
# Real test backend — follows the exact same protocol as OpenAIImageBackend
# and GeminiImageBackend so any interface mismatch is caught immediately.
# ---------------------------------------------------------------------------


class TestImageBackend:
    """A real backend for testing — writes a minimal PNG to disk, no API calls.

    Implements the full backend protocol used by ComicImageGenTool.execute():
      - ``provider.name``  (str)  — accessed in error messages
      - ``provider_type``  (str)  — used for preferred-provider routing
      - ``async generate(prompt, output_path, size, style,
                         reference_images, model)``
          same positional-or-keyword signature as the real backends

    If the backend interface ever changes (new required attribute, renamed
    method, different return-dict keys) these tests will fail immediately
    instead of silently passing with a MagicMock that swallows the mismatch.
    """

    def __init__(self) -> None:
        self.provider = SimpleNamespace(name="test-provider")
        self.provider_type = "test"
        self.name = "test-backend"

    async def generate(
        self,
        prompt: str,
        output_path: str | Path,
        size: str = "square",
        style: str | None = None,
        model: str | None = None,
        reference_images: list[str] | None = None,
    ) -> dict[str, Any]:
        """Write a minimal valid PNG to *output_path* — no network calls."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(_MINIMAL_PNG)
        return {
            "success": True,
            "path": str(out),
            "provider_used": "test-provider",
            "error": None,
        }


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_storage(tmp_path):
    """FileSystemStorage rooted at tmp_path / '.comic-assets'."""
    return FileSystemStorage(str(tmp_path / ".comic-assets"))


@pytest.fixture()
def service(tmp_storage):
    """ComicProjectService backed by a fresh temporary storage."""
    return ComicProjectService(tmp_storage)


@pytest.fixture()
def sample_png(tmp_path):
    """Write a minimal PNG file and return its path as a string."""
    png_path = tmp_path / "test.png"
    png_path.write_bytes(_MINIMAL_PNG)
    return str(png_path)


@pytest.fixture()
def image_gen():
    """Real ComicImageGenTool wired with a TestImageBackend — zero mocks.

    Using the real ``ComicImageGenTool`` (not a ``MagicMock``) means that any
    interface mismatch between ``ComicCreateTool`` and ``ComicImageGenTool``
    (wrong method name, missing attribute, changed return shape) is caught
    immediately rather than hidden behind a mock that accepts anything.
    """
    from amplifier_module_comic_image_gen import ComicImageGenTool

    backend = TestImageBackend()
    return ComicImageGenTool(backends=[backend])


# ---------------------------------------------------------------------------
# Event-loop hygiene
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _drain_executor() -> None:
    """Ensure the default executor is shut down after each test.

    ``asyncio.to_thread()`` in ``FileSystemStorage`` creates a
    ``ThreadPoolExecutor`` per event loop.  With ``loop_scope="function"``
    each test gets a fresh loop; without explicit shutdown, thread stacks
    (8 MB each on Linux) accumulate across the suite.
    """
    yield
    loop = asyncio.get_event_loop()
    await loop.shutdown_default_executor()
