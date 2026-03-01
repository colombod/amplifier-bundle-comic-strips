"""Tests for the tool module mount() function and ComicImageGenTool class."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_module_comic_image_gen import ComicImageGenTool, mount
from amplifier_module_comic_image_gen.providers.openai_images import OpenAIImageBackend

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


def test_tool_schema_has_model_param() -> None:
    """model should be an optional string parameter for explicit model override."""
    tool = ComicImageGenTool(backends=[])
    schema = tool.input_schema

    # Must exist in properties with type string
    assert "model" in schema["properties"]
    model_prop = schema["properties"]["model"]
    assert model_prop["type"] == "string"

    # Must NOT be in the required list
    assert "model" not in schema["required"]


def test_tool_schema_has_requirements_param() -> None:
    """requirements should be an optional object with sub-properties."""
    tool = ComicImageGenTool(backends=[])
    schema = tool.input_schema

    # Must exist in properties with type object
    assert "requirements" in schema["properties"]
    req_prop = schema["properties"]["requirements"]
    assert req_prop["type"] == "object"

    # Must have the three sub-properties
    sub_props = req_prop["properties"]
    assert "needs_reference_images" in sub_props
    assert sub_props["needs_reference_images"]["type"] == "boolean"
    assert "style_category" in sub_props
    assert sub_props["style_category"]["type"] == "string"
    assert "detail_level" in sub_props
    assert sub_props["detail_level"]["type"] == "string"
    assert sub_props["detail_level"]["enum"] == ["low", "medium", "high", "ultra"]

    # Must NOT be in the required list
    assert "requirements" not in schema["required"]


@pytest.mark.asyncio(loop_scope="function")
async def test_execute_with_explicit_model_passes_to_backend(tmp_path: Path) -> None:
    """When params contain 'model', it should be passed to backend.generate()."""
    backend = MagicMock()
    backend.provider.name = "mock-provider"
    backend.generate = AsyncMock(
        return_value={
            "success": True,
            "provider_used": "mock-provider",
            "path": str(tmp_path / "out.png"),
            "error": None,
        }
    )
    tool = ComicImageGenTool(backends=[backend])

    await tool.execute(
        {
            "prompt": "A hero panel",
            "output_path": str(tmp_path / "out.png"),
            "model": "dall-e-3",
        }
    )

    backend.generate.assert_awaited_once()
    call_kwargs = backend.generate.call_args.kwargs
    assert call_kwargs["model"] == "dall-e-3"


@pytest.mark.asyncio(loop_scope="function")
async def test_execute_uses_model_selector_when_requirements_provided(
    tmp_path: Path,
) -> None:
    """When requirements dict provided (no explicit model), model selector picks the model."""
    backend = MagicMock()
    backend.provider.name = "mock-provider"
    backend.provider_type = "openai"
    backend.generate = AsyncMock(
        return_value={
            "success": True,
            "provider_used": "mock-provider",
            "path": str(tmp_path / "out.png"),
            "error": None,
        }
    )
    tool = ComicImageGenTool(backends=[backend])

    await tool.execute(
        {
            "prompt": "A hero panel",
            "output_path": str(tmp_path / "out.png"),
            "requirements": {"needs_reference_images": False, "detail_level": "medium"},
        }
    )

    backend.generate.assert_awaited_once()
    call_kwargs = backend.generate.call_args.kwargs
    assert "model" in call_kwargs
    assert call_kwargs["model"] is not None


@pytest.mark.asyncio(loop_scope="function")
async def test_execute_explicit_model_bypasses_selector(tmp_path: Path) -> None:
    """When explicit model AND requirements are both provided, explicit model wins."""
    backend = MagicMock()
    backend.provider.name = "mock-provider"
    backend.provider_type = "openai"
    backend.generate = AsyncMock(
        return_value={
            "success": True,
            "provider_used": "mock-provider",
            "path": str(tmp_path / "out.png"),
            "error": None,
        }
    )
    tool = ComicImageGenTool(backends=[backend])

    await tool.execute(
        {
            "prompt": "A hero panel",
            "output_path": str(tmp_path / "out.png"),
            "model": "dall-e-3",
            "requirements": {"needs_reference_images": False, "detail_level": "medium"},
        }
    )

    backend.generate.assert_awaited_once()
    call_kwargs = backend.generate.call_args.kwargs
    assert call_kwargs["model"] == "dall-e-3"
