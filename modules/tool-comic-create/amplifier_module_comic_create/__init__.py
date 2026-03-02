"""High-level comic creation tool — orchestrates image generation, storage, review, and assembly.

Agents work with comic:// URIs. Binary image data never enters conversation context.
All image plumbing (generation, storage, encoding, vision API) is internal.

Registration entry point: :func:`mount` (called by the Amplifier module loader).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

try:
    from amplifier_core.models import ToolResult  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover

    @dataclass
    class ToolResult:  # type: ignore[no-redef]
        """Minimal stand-in used when amplifier_core is not installed."""

        success: bool = False
        output: Any = ""


from ._version import __version__  # noqa: F401, E402

__amplifier_module_type__ = "tool"

__all__ = ["mount", "ComicCreateTool"]


def _ok(result: Any) -> ToolResult:
    return ToolResult(success=True, output=json.dumps(result))


def _error(msg: str) -> ToolResult:
    return ToolResult(success=False, output=msg)


class ComicCreateTool:
    """High-level comic creation tool with 5 actions.

    Actions:
        create_character_ref — Generate + store character reference sheet.
        create_panel — Resolve character refs + generate + store panel.
        create_cover — Resolve character refs + generate + store cover.
        review_asset — Vision-based review with optional reference comparison.
        assemble_comic — Resolve all URIs + produce self-contained HTML.

    Binary image data stays internal. Agents receive only URIs and text.
    """

    def __init__(
        self,
        service: Any,
        image_gen: Any | None = None,
    ) -> None:
        self._service = service
        self._image_gen = image_gen  # ComicImageGenTool instance (internal)

    @property
    def name(self) -> str:
        return "comic_create"

    @property
    def description(self) -> str:
        return (
            "High-level comic creation tool. Create character references, panels, "
            "covers, review assets via vision, and assemble final HTML comics. "
            "Works with comic:// URIs — binary image data stays internal."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Operation to perform.",
                    "enum": [
                        "create_character_ref",
                        "create_panel",
                        "create_cover",
                        "review_asset",
                        "assemble_comic",
                    ],
                },
                "project": {"type": "string", "description": "Project identifier."},
                "issue": {"type": "string", "description": "Issue identifier."},
                "name": {"type": "string", "description": "Asset name."},
                "prompt": {"type": "string", "description": "Generation or review prompt."},
                "visual_traits": {"type": "string", "description": "Character visual description."},
                "distinctive_features": {"type": "string", "description": "Character distinctive features."},
                "personality": {"type": "string", "description": "Character personality context."},
                "character_uris": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of comic:// character URIs for reference images.",
                },
                "size": {
                    "type": "string",
                    "description": "Image aspect ratio.",
                    "enum": ["landscape", "portrait", "square"],
                    "default": "square",
                },
                "camera_angle": {"type": "string", "description": "Camera framing hint."},
                "title": {"type": "string", "description": "Comic/cover title."},
                "subtitle": {"type": "string", "description": "Subtitle or tagline."},
                "uri": {"type": "string", "description": "comic:// URI for review_asset target."},
                "reference_uris": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional comic:// URIs for visual comparison in review.",
                },
                "output_path": {"type": "string", "description": "Output path for assemble_comic."},
                "style_uri": {"type": "string", "description": "Style guide URI for assembly."},
                "layout": {"type": "object", "description": "Structured layout for assemble_comic."},
            },
            "required": ["action"],
        }

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Dispatch to the appropriate action handler."""
        action = params.get("action")
        dispatch: dict[str, Any] = {
            "create_character_ref": self._create_character_ref,
            "create_panel": self._create_panel,
            "create_cover": self._create_cover,
            "review_asset": self._review_asset,
            "assemble_comic": self._assemble_comic,
        }
        handler = dispatch.get(action)  # type: ignore[arg-type]
        if handler is None:
            valid = ", ".join(sorted(dispatch))
            return _error(f"Unknown action '{action}'. Valid actions: {valid}")
        return await handler(params)

    async def _create_character_ref(self, params: dict[str, Any]) -> ToolResult:
        return _error("create_character_ref not yet implemented")

    async def _create_panel(self, params: dict[str, Any]) -> ToolResult:
        return _error("create_panel not yet implemented")

    async def _create_cover(self, params: dict[str, Any]) -> ToolResult:
        return _error("create_cover not yet implemented")

    async def _review_asset(self, params: dict[str, Any]) -> ToolResult:
        return _error("review_asset not yet implemented")

    async def _assemble_comic(self, params: dict[str, Any]) -> ToolResult:
        return _error("assemble_comic not yet implemented")


async def mount(coordinator: Any, config: Any = None) -> None:
    """Amplifier module entry point — build service and register the tool."""
    from amplifier_module_comic_assets.service import ComicProjectService
    from amplifier_module_comic_assets.storage import FileSystemStorage

    cfg = config or {}
    storage_cfg = cfg.get("storage", {})
    backend = storage_cfg.get("backend", "filesystem")
    if backend == "filesystem":
        fs_cfg = storage_cfg.get("filesystem", {})
        root = fs_cfg.get("root", ".comic-assets")
        storage = FileSystemStorage(root=root)
    else:
        raise ValueError(f"Unknown storage backend '{backend}'")

    service = ComicProjectService(storage=storage)

    # Attempt to get the generate_image tool's internal backend.
    # It may not be available (validation dry-run, or image-gen not loaded).
    image_gen = None
    try:
        tools = coordinator.get("tools") or {}
        image_gen = tools.get("generate_image")
    except Exception:
        pass

    tool = ComicCreateTool(service=service, image_gen=image_gen)
    await coordinator.mount("tools", tool, name=tool.name)
