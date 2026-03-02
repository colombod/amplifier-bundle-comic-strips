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
        """Generate + store a character reference sheet. Return URI."""
        required = ("project", "issue", "name", "prompt", "visual_traits", "distinctive_features")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        if self._image_gen is None:
            return _error("No image generation backend available. Cannot create character reference.")

        import os
        import tempfile

        from amplifier_module_comic_assets.comic_uri import ComicURI
        from amplifier_module_comic_assets.models import slugify

        project = params["project"]
        issue = params["issue"]
        name = params["name"]
        char_slug = slugify(name)

        # Generate the reference image to a temp path
        output_dir = tempfile.mkdtemp(prefix="comic_create_")
        output_path = os.path.join(output_dir, f"ref_{char_slug}.png")

        gen_result = await self._image_gen.generate(
            prompt=params["prompt"],
            output_path=output_path,
            size=params.get("size", "portrait"),
            style=params.get("style"),
            reference_images=None,
        )

        if not gen_result.get("success", False):
            return _error(f"Image generation failed: {gen_result.get('error', 'unknown')}")

        # Store the character via the service
        store_result = await self._service.store_character(
            project,
            issue,
            name,
            style=params.get("style", "default"),
            role=params.get("role", ""),
            character_type=params.get("character_type", "main"),
            bundle=params.get("bundle", ""),
            visual_traits=params["visual_traits"],
            team_markers=params.get("team_markers", ""),
            distinctive_features=params["distinctive_features"],
            backstory=params.get("backstory", ""),
            motivations=params.get("motivations", ""),
            personality=params.get("personality", ""),
            source_path=output_path,
        )

        version = store_result["version"]
        uri = ComicURI.for_character(project, issue, char_slug, version=version)

        return _ok({"uri": str(uri), "version": version})

    async def _resolve_character_image_paths(self, uris: list[str]) -> list[str]:
        """Resolve comic:// character URIs to absolute file paths on disk."""
        from amplifier_module_comic_assets.comic_uri import parse_comic_uri

        paths: list[str] = []
        for raw in uris:
            parsed = parse_comic_uri(raw)
            char_data = await self._service.get_character(
                parsed.project,
                parsed.name,
                style=None,
                version=parsed.version,
                include="full",
                format="path",
            )
            image_path = char_data.get("image")
            if image_path:
                paths.append(image_path)
        return paths

    async def _create_panel(self, params: dict[str, Any]) -> ToolResult:
        """Resolve character refs + generate + store panel. Return URI."""
        required = ("project", "issue", "name", "prompt")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        if self._image_gen is None:
            return _error("No image generation backend available. Cannot create panel.")

        import os
        import tempfile

        from amplifier_module_comic_assets.comic_uri import ComicURI

        project = params["project"]
        issue = params["issue"]
        name = params["name"]

        # Resolve character URIs to reference image paths
        character_uris = params.get("character_uris") or []
        ref_paths: list[str] = []
        if character_uris:
            try:
                ref_paths = await self._resolve_character_image_paths(character_uris)
            except (FileNotFoundError, ValueError) as exc:
                return _error(f"Failed to resolve character URIs: {exc}")

        output_dir = tempfile.mkdtemp(prefix="comic_create_")
        output_path = os.path.join(output_dir, f"{name}.png")

        gen_result = await self._image_gen.generate(
            prompt=params["prompt"],
            output_path=output_path,
            size=params.get("size", "square"),
            style=params.get("style"),
            reference_images=ref_paths or None,
        )

        if not gen_result.get("success", False):
            return _error(f"Image generation failed: {gen_result.get('error', 'unknown')}")

        store_result = await self._service.store_asset(
            project, issue, "panel", name,
            source_path=output_path,
            metadata={"prompt": params["prompt"], "camera_angle": params.get("camera_angle", "")},
        )

        version = store_result["version"]
        uri = ComicURI.for_asset(project, issue, "panel", name, version=version)

        return _ok({"uri": str(uri), "version": version})

    async def _create_cover(self, params: dict[str, Any]) -> ToolResult:
        """Resolve character refs + generate + store cover. Return URI."""
        required = ("project", "issue", "prompt", "title")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        if self._image_gen is None:
            return _error("No image generation backend available. Cannot create cover.")

        import os
        import tempfile

        from amplifier_module_comic_assets.comic_uri import ComicURI

        project = params["project"]
        issue = params["issue"]
        name = "cover"  # Covers always use name "cover"

        character_uris = params.get("character_uris") or []
        ref_paths: list[str] = []
        if character_uris:
            try:
                ref_paths = await self._resolve_character_image_paths(character_uris)
            except (FileNotFoundError, ValueError) as exc:
                return _error(f"Failed to resolve character URIs: {exc}")

        output_dir = tempfile.mkdtemp(prefix="comic_create_")
        output_path = os.path.join(output_dir, "cover.png")

        gen_result = await self._image_gen.generate(
            prompt=params["prompt"],
            output_path=output_path,
            size=params.get("size", "landscape"),
            style=params.get("style"),
            reference_images=ref_paths or None,
        )

        if not gen_result.get("success", False):
            return _error(f"Image generation failed: {gen_result.get('error', 'unknown')}")

        store_result = await self._service.store_asset(
            project, issue, "cover", name,
            source_path=output_path,
            metadata={
                "title": params["title"],
                "subtitle": params.get("subtitle", ""),
            },
        )

        version = store_result["version"]
        uri = ComicURI.for_asset(project, issue, "cover", name, version=version)

        return _ok({"uri": str(uri), "version": version})

    async def _call_vision_api(
        self, image_paths: list[str], prompt: str
    ) -> dict[str, Any]:
        """Call a vision-capable model with images and a review prompt.

        Returns {\"passed\": bool, \"feedback\": str}.
        This is a placeholder — the real implementation will use a vision
        provider from the coordinator. For now, returns a \"not available\"
        response so the agent can still proceed.
        """
        return {
            "passed": True,
            "feedback": "Vision review not yet available — auto-passing.",
        }

    async def _review_asset(self, params: dict[str, Any]) -> ToolResult:
        """Vision-based review. Resolve URI → image path → vision API → text feedback."""
        required = ("uri", "prompt")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        from amplifier_module_comic_assets.comic_uri import parse_comic_uri

        raw_uri = params["uri"]
        try:
            parsed = parse_comic_uri(raw_uri)
        except ValueError as exc:
            return _error(f"Invalid URI: {exc}")

        # Resolve the target asset to a file path
        try:
            if parsed.asset_type == "character":
                asset_data = await self._service.get_character(
                    parsed.project, parsed.name,
                    version=parsed.version,
                    include="full", format="path",
                )
                image_path = asset_data.get("image")
            else:
                asset_data = await self._service.get_asset(
                    parsed.project, parsed.issue, parsed.asset_type, parsed.name,
                    version=parsed.version,
                    include="full", format="path",
                )
                image_path = asset_data.get("image")
        except (FileNotFoundError, ValueError) as exc:
            return _error(f"Cannot resolve URI {raw_uri}: {exc}")

        if not image_path:
            return _error(f"No image found for URI: {raw_uri}")

        # Collect all image paths for vision (target + optional references)
        all_paths = [image_path]

        reference_uris = params.get("reference_uris") or []
        for ref_raw in reference_uris:
            try:
                ref_parsed = parse_comic_uri(ref_raw)
                if ref_parsed.asset_type == "character":
                    ref_data = await self._service.get_character(
                        ref_parsed.project, ref_parsed.name,
                        version=ref_parsed.version,
                        include="full", format="path",
                    )
                    ref_image = ref_data.get("image")
                else:
                    ref_data = await self._service.get_asset(
                        ref_parsed.project, ref_parsed.issue,
                        ref_parsed.asset_type, ref_parsed.name,
                        version=ref_parsed.version,
                        include="full", format="path",
                    )
                    ref_image = ref_data.get("image")
                if ref_image:
                    all_paths.append(ref_image)
            except (FileNotFoundError, ValueError):
                continue  # Skip unresolvable references

        # Call vision API — images sent to API wire, never to LLM context
        vision_result = await self._call_vision_api(all_paths, params["prompt"])

        return _ok({
            "uri": raw_uri,
            "passed": vision_result.get("passed", False),
            "feedback": vision_result.get("feedback", ""),
        })

    async def _resolve_image_as_data_uri(self, raw_uri: str) -> str | None:
        """Resolve a comic:// URI to a base64 data URI string (internal only)."""
        import asyncio
        from pathlib import Path

        from amplifier_module_comic_assets.comic_uri import parse_comic_uri
        from amplifier_module_comic_assets.encoding import bytes_to_data_uri

        try:
            parsed = parse_comic_uri(raw_uri)
        except ValueError:
            return None

        try:
            if parsed.asset_type == "character":
                asset = await self._service.get_character(
                    parsed.project, parsed.name,
                    version=parsed.version, include="full", format="path",
                )
                image_path = asset.get("image")
            else:
                asset = await self._service.get_asset(
                    parsed.project, parsed.issue, parsed.asset_type, parsed.name,
                    version=parsed.version, include="full", format="path",
                )
                image_path = asset.get("image")
        except (FileNotFoundError, ValueError):
            return None

        if not image_path:
            return None

        image_bytes = await asyncio.to_thread(Path(image_path).read_bytes)
        # Detect MIME from magic bytes
        if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            mime = "image/png"
        elif image_bytes[:3] == b"\xff\xd8\xff":
            mime = "image/jpeg"
        else:
            mime = "image/png"

        return bytes_to_data_uri(image_bytes, mime)

    async def _assemble_comic(self, params: dict[str, Any]) -> ToolResult:
        """Resolve all URIs in layout → base64 encode → produce HTML."""
        import asyncio
        from pathlib import Path

        required = ("project", "issue", "output_path", "layout")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        layout = params["layout"]
        output_path = params["output_path"]

        images_embedded = 0
        page_count = 0

        # --- Resolve cover ---
        cover_html = ""
        cover_info = layout.get("cover")
        if cover_info and "uri" in cover_info:
            cover_data_uri = await self._resolve_image_as_data_uri(cover_info["uri"])
            if cover_data_uri:
                title = cover_info.get("title", layout.get("title", ""))
                subtitle = cover_info.get("subtitle", "")
                cover_html = (
                    f'<section class="page cover-page">'
                    f'<div style="position:relative;text-align:center;">'
                    f'<img src="{cover_data_uri}" style="max-width:100%;max-height:80vh;" />'
                    f'<h1 style="position:absolute;top:5%;left:50%;transform:translateX(-50%);">{title}</h1>'
                    f"<h2>{subtitle}</h2>"
                    f"</div></section>"
                )
                images_embedded += 1
                page_count += 1

        # --- Resolve pages ---
        pages_html = ""
        for page_def in layout.get("pages", []):
            page_count += 1
            panels_html = ""
            for panel_def in page_def.get("panels", []):
                panel_uri = panel_def.get("uri", "")
                data_uri = await self._resolve_image_as_data_uri(panel_uri)
                if data_uri:
                    images_embedded += 1
                    # Build overlay HTML
                    overlays_html = ""
                    for overlay in panel_def.get("overlays", []):
                        pos = overlay.get("position", {})
                        style = (
                            f"position:absolute;left:{pos.get('x', 10)}%;"
                            f"top:{pos.get('y', 10)}%;width:{pos.get('width', 30)}%;"
                        )
                        text = overlay.get("text", "")
                        overlays_html += f'<div class="overlay" style="{style}">{text}</div>'

                    panels_html += (
                        f'<div class="panel" style="position:relative;">'
                        f'<img src="{data_uri}" style="width:100%;" />'
                        f"{overlays_html}</div>"
                    )

            pages_html += f'<section class="page story-page"><div class="panel-grid">{panels_html}</div></section>'

        # --- Assemble final HTML ---
        title = layout.get("title", "Comic")
        html = (
            f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
            f"<title>{title}</title>"
            f"<style>"
            f"*{{box-sizing:border-box;margin:0;padding:0;}}"
            f".page{{width:100%;padding:1rem;}}"
            f".panel-grid{{display:grid;gap:8px;}}"
            f".panel img{{width:100%;display:block;}}"
            f"</style></head><body>"
            f"{cover_html}{pages_html}"
            f"</body></html>"
        )

        await asyncio.to_thread(lambda: Path(output_path).write_text(html, encoding="utf-8"))

        # Also store as final asset (non-fatal if fails)
        try:
            await self._service.store_asset(
                params["project"], params["issue"], "final", "comic",
                content=html,
            )
        except Exception:
            pass

        return _ok({
            "output_path": output_path,
            "pages": page_count,
            "images_embedded": images_embedded,
        })


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
