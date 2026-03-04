"""Shared pytest fixtures for tool-comic-create tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import pytest_asyncio

from amplifier_core import (
    ChatRequest,
    ChatResponse,
    ModelInfo,
    Provider,
    ProviderInfo,
    TextBlock,
    ToolCall,
)

from amplifier_module_comic_assets.service import ComicProjectService
from amplifier_module_comic_assets.storage import FileSystemStorage

_MINIMAL_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


# ---------------------------------------------------------------------------
# FakeVisionProvider — strict test double following the real Provider protocol.
# Uses actual amplifier_core types — if the protocol changes, this breaks.
# isinstance(FakeVisionProvider(), Provider) is verified at module level below.
# ---------------------------------------------------------------------------


class FakeVisionProvider:
    """Strict test double following the real Provider protocol.

    Uses actual amplifier_core types — if the protocol changes, this breaks.
    isinstance(FakeVisionProvider(), Provider) is verified at test time.
    """

    __test__ = False  # prevent pytest from treating this as a test class

    def __init__(
        self, response_text: str = '{"passed": true, "feedback": "Looks good."}'
    ) -> None:
        self._response_text = response_text
        self.call_count = 0
        self.last_request: ChatRequest | None = None

    @property
    def name(self) -> str:
        return "fake-vision"

    def get_info(self) -> ProviderInfo:
        return ProviderInfo(
            id="fake-vision",
            display_name="Fake Vision Provider",
            capabilities=["vision"],
        )

    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id="fake-vision-model",
                display_name="Fake Vision Model",
                context_window=128000,
                max_output_tokens=4096,
                capabilities=["vision"],
            )
        ]

    async def complete(self, request: ChatRequest, **kwargs: Any) -> ChatResponse:
        self.call_count += 1
        self.last_request = request
        return ChatResponse(content=[TextBlock(text=self._response_text)])

    def parse_tool_calls(self, response: ChatResponse) -> list[ToolCall]:
        return []


# Verify at import time that our fake matches the real protocol
assert isinstance(
    FakeVisionProvider(), Provider
), "FakeVisionProvider does not match Provider protocol!"


class FakeCoordinator:
    """Minimal coordinator test double — provides get() for providers and tools."""

    __test__ = False  # prevent pytest from treating this as a test class

    def __init__(
        self,
        vision_provider: FakeVisionProvider | None = None,
        tools: dict[str, Any] | None = None,
    ) -> None:
        self._providers: dict[str, Any] = {}
        self._tools: dict[str, Any] = tools or {}
        if vision_provider is not None:
            self._providers["fake-vision"] = vision_provider

    def get(self, mount_point: str, name: str | None = None) -> Any:
        if mount_point == "providers":
            return self._providers
        if mount_point == "tools":
            return self._tools
        return None


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
def fake_vision_provider() -> FakeVisionProvider:
    """FakeVisionProvider with default passing response."""
    return FakeVisionProvider()


@pytest.fixture()
def fake_coordinator(fake_vision_provider: FakeVisionProvider) -> FakeCoordinator:
    """FakeCoordinator wired with a FakeVisionProvider."""
    return FakeCoordinator(vision_provider=fake_vision_provider)


@pytest.fixture()
def fake_coordinator_no_vision() -> FakeCoordinator:
    """FakeCoordinator with no vision provider (triggers auto-pass)."""
    return FakeCoordinator()


@pytest.fixture()
def tmp_storage(tmp_path: Path) -> FileSystemStorage:
    """FileSystemStorage rooted at tmp_path / '.comic-assets'."""
    return FileSystemStorage(str(tmp_path / ".comic-assets"))


@pytest.fixture()
def service(tmp_storage: FileSystemStorage) -> ComicProjectService:
    """ComicProjectService backed by a fresh temporary storage."""
    return ComicProjectService(tmp_storage)


@pytest.fixture()
def sample_png(tmp_path: Path) -> str:
    """Write a minimal PNG file and return its path as a string."""
    png_path = tmp_path / "test.png"
    png_path.write_bytes(_MINIMAL_PNG)
    return str(png_path)


@pytest.fixture()
def image_gen() -> Any:
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
