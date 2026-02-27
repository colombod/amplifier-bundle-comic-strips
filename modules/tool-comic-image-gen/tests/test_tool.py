"""Tests for the tool module mount() function and ComicImageGenTool class."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_comic_image_gen import ComicImageGenTool, mount
from amplifier_comic_image_gen.providers.openai_images import OpenAIImageBackend

from .conftest import make_openai_provider


def _make_coordinator(providers: dict[str, object]) -> MagicMock:
    """Create a MagicMock coordinator for testing mount()."""
    coord = MagicMock()

    def _get_side_effect(mount_point: str) -> object:
        if mount_point == "providers":
            return providers
        return {}

    coord.get = MagicMock(side_effect=_get_side_effect)
    coord.mount = AsyncMock()
    return coord


# ── Property tests ───────────────────────────────────────────────


def test_tool_has_required_properties() -> None:
    tool = ComicImageGenTool(backends=[])

    assert tool.name == "generate_image"
    assert "image" in tool.description.lower()

    schema = tool.input_schema
    assert "prompt" in schema["properties"]
    assert "output_path" in schema["properties"]
    assert schema["required"] == ["prompt", "output_path"]


# ── Mount tests ──────────────────────────────────────────────────


@pytest.mark.asyncio(loop_scope="function")
async def test_mount_registers_tool() -> None:
    provider = make_openai_provider()
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
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)
    tool = ComicImageGenTool(backends=[backend])

    output_path = str(tmp_path / "panel_01.png")
    result = await tool.execute(
        {"prompt": "A superhero panel", "output_path": output_path}
    )

    assert result.success is True
    assert "provider_used" in result.output
    assert Path(output_path).exists()


@pytest.mark.asyncio(loop_scope="function")
async def test_execute_with_no_backends(tmp_path: Path) -> None:
    tool = ComicImageGenTool(backends=[])

    result = await tool.execute(
        {"prompt": "A panel", "output_path": str(tmp_path / "out.png")}
    )

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
    backup_provider = make_openai_provider(name="provider-openai-backup")
    backup_backend = OpenAIImageBackend(backup_provider)

    tool = ComicImageGenTool(
        backends=[failing_backend, backup_backend],
    )

    output_path = str(tmp_path / "panel_fallback.png")
    result = await tool.execute({"prompt": "A panel", "output_path": output_path})

    assert result.success is True
    assert result.output["provider_used"] == "provider-openai-backup"


@pytest.mark.asyncio(loop_scope="function")
async def test_execute_missing_required_params() -> None:
    tool = ComicImageGenTool(backends=[])

    result = await tool.execute({"prompt": "A panel"})

    assert result.success is False
    assert "output_path" in result.output.lower()


# ── Schema tests ─────────────────────────────────────────────────────


def test_tool_size_enum_uses_aspect_ratios() -> None:
    tool = ComicImageGenTool(backends=[])
    schema = tool.input_schema
    size_prop = schema["properties"]["size"]

    assert size_prop["enum"] == ["landscape", "portrait", "square"]
    assert size_prop["default"] == "square"


def test_tool_schema_has_reference_images_param() -> None:
    """reference_images should be an optional array of strings in the schema."""
    tool = ComicImageGenTool(backends=[])
    schema = tool.input_schema

    # Must exist in properties
    assert "reference_images" in schema["properties"]

    ref_prop = schema["properties"]["reference_images"]
    assert ref_prop["type"] == "array"
    assert ref_prop["items"]["type"] == "string"

    # Must NOT be in the required list
    assert "reference_images" not in schema["required"]
