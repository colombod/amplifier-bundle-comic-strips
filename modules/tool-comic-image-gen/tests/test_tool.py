"""Tests for the tool module mount() function and ComicImageGenTool class."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_comic_image_gen import ComicImageGenTool, mount
from amplifier_comic_image_gen.providers.openai_images import OpenAIImageBackend

from .conftest import TINY_PNG_B64


def _make_coordinator(
    providers: dict[str, object],
    working_dir: str = "/tmp",
) -> MagicMock:
    """Create a MagicMock coordinator for testing mount()."""
    coord = MagicMock()

    def _get_side_effect(mount_point: str) -> object:
        if mount_point == "providers":
            return providers
        return {}

    coord.get = MagicMock(side_effect=_get_side_effect)
    coord.get_capability = MagicMock(return_value=working_dir)
    coord.mount = AsyncMock()
    return coord


def _make_openai_provider() -> MagicMock:
    """Create a full mock OpenAI provider with images.generate AsyncMock."""
    provider = MagicMock()
    provider.name = "provider-openai"

    response = MagicMock()
    response.data = [MagicMock(b64_json=TINY_PNG_B64)]

    provider.client.images.generate = AsyncMock(return_value=response)
    return provider


# ── Property tests ───────────────────────────────────────────────


def test_tool_has_required_properties() -> None:
    tool = ComicImageGenTool(backends=[], working_dir="/tmp")

    assert tool.name == "generate_image"
    assert "image" in tool.description.lower()

    schema = tool.input_schema
    assert "prompt" in schema["properties"]
    assert "output_path" in schema["properties"]
    assert schema["required"] == ["prompt", "output_path"]


# ── Mount tests ──────────────────────────────────────────────────


@pytest.mark.asyncio(loop_scope="function")
async def test_mount_registers_tool() -> None:
    provider = _make_openai_provider()
    coord = _make_coordinator({"provider-openai": provider})

    await mount(coord, config=None)

    coord.mount.assert_awaited_once()
    call_args = coord.mount.call_args
    assert call_args.args[0] == "tools"
    assert call_args.kwargs["name"] == "generate_image"


@pytest.mark.asyncio(loop_scope="function")
async def test_mount_with_no_providers() -> None:
    coord = _make_coordinator({})

    await mount(coord, config=None)

    coord.mount.assert_awaited_once()


# ── Execute tests ────────────────────────────────────────────────


@pytest.mark.asyncio(loop_scope="function")
async def test_execute_generates_image(tmp_path: Path) -> None:
    provider = _make_openai_provider()
    backend = OpenAIImageBackend(provider)
    tool = ComicImageGenTool(backends=[backend], working_dir=str(tmp_path))

    output_path = str(tmp_path / "panel_01.png")
    result = await tool.execute(
        {"prompt": "A superhero panel", "output_path": output_path}
    )

    assert result.success is True
    assert "provider_used" in result.output
    assert Path(output_path).exists()


@pytest.mark.asyncio(loop_scope="function")
async def test_execute_with_no_backends() -> None:
    tool = ComicImageGenTool(backends=[], working_dir="/tmp")

    result = await tool.execute({"prompt": "A panel", "output_path": "/tmp/out.png"})

    assert result.success is False
    assert "no image" in result.output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_execute_falls_back_on_failure(tmp_path: Path) -> None:
    # First backend fails
    failing_provider = MagicMock()
    failing_provider.name = "provider-openai-primary"
    failing_provider.client.images.generate = AsyncMock(
        side_effect=Exception("API down"),
    )
    failing_backend = OpenAIImageBackend(failing_provider)

    # Second backend succeeds
    backup_provider = MagicMock()
    backup_provider.name = "provider-openai-backup"
    response = MagicMock()
    response.data = [MagicMock(b64_json=TINY_PNG_B64)]
    backup_provider.client.images.generate = AsyncMock(return_value=response)
    backup_backend = OpenAIImageBackend(backup_provider)

    tool = ComicImageGenTool(
        backends=[failing_backend, backup_backend],
        working_dir=str(tmp_path),
    )

    output_path = str(tmp_path / "panel_fallback.png")
    result = await tool.execute({"prompt": "A panel", "output_path": output_path})

    assert result.success is True
    assert result.output["provider_used"] == "provider-openai-backup"


@pytest.mark.asyncio(loop_scope="function")
async def test_execute_missing_required_params() -> None:
    tool = ComicImageGenTool(backends=[], working_dir="/tmp")

    result = await tool.execute({"prompt": "A panel"})

    assert result.success is False
    assert "output_path" in result.output.lower()
