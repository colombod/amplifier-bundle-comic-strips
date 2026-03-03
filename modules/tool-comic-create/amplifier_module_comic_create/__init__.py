"""High-level comic creation tool — orchestrates image generation, storage, review, and assembly.

Agents work with comic:// URIs. Binary image data never enters conversation context.
All image plumbing (generation, storage, encoding, vision API) is internal.

Registration entry point: :func:`mount` (called by the Amplifier module loader).
"""

from __future__ import annotations

import base64
import json
import logging
import re
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


def _detect_mime(image_bytes: bytes) -> str:
    """Detect image MIME type from magic bytes."""
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"  # fallback


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
        coordinator: Any | None = None,
    ) -> None:
        self._service = service
        self._image_gen = image_gen  # ComicImageGenTool instance (internal)
        self._coordinator = coordinator  # for provider access

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
                    "description": (
                        "Operation to perform.\n"
                        "- create_character_ref: requires project, issue, name, prompt,"
                        " visual_traits, distinctive_features\n"
                        "- create_panel: requires project, issue, name, prompt;"
                        " optional character_uris, size\n"
                        "- create_cover: requires project, issue, prompt, title;"
                        " optional character_uris, subtitle\n"
                        "- review_asset: requires uri, prompt; optional reference_uris\n"
                        "- assemble_comic: requires project, issue, output_path, layout;"
                        " optional style_uri"
                    ),
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
                "prompt": {
                    "type": "string",
                    "description": "Generation or review prompt.",
                },
                "visual_traits": {
                    "type": "string",
                    "description": "Character visual description.",
                },
                "distinctive_features": {
                    "type": "string",
                    "description": "Character distinctive features.",
                },
                "personality": {
                    "type": "string",
                    "description": "Character personality context.",
                },
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
                "camera_angle": {
                    "type": "string",
                    "description": "Camera framing hint.",
                },
                "title": {"type": "string", "description": "Comic/cover title."},
                "subtitle": {"type": "string", "description": "Subtitle or tagline."},
                "uri": {
                    "type": "string",
                    "description": "comic:// URI for review_asset target.",
                },
                "reference_uris": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional comic:// URIs for visual comparison in review.",
                },
                "output_path": {
                    "type": "string",
                    "description": "Output path for assemble_comic.",
                },
                "style_uri": {
                    "type": "string",
                    "description": "Style guide URI for assembly.",
                },
                "layout": {
                    "type": "object",
                    "description": "Structured layout for assemble_comic.",
                },
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
        required = (
            "project",
            "issue",
            "name",
            "prompt",
            "visual_traits",
            "distinctive_features",
        )
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        if self._image_gen is None:
            return _error(
                "No image generation backend available. Cannot create character reference."
            )

        import os
        import tempfile

        from amplifier_module_comic_assets.comic_uri import ComicURI
        from amplifier_module_comic_assets.models import slugify

        project = params["project"]
        issue = params["issue"]
        name = params["name"]
        char_slug = slugify(name)

        # Generate the reference image to a temp path
        with tempfile.TemporaryDirectory(prefix="comic_create_") as output_dir:
            output_path = os.path.join(output_dir, f"ref_{char_slug}.png")

            gen_result = await self._image_gen.execute(
                {
                    "prompt": params["prompt"],
                    "output_path": output_path,
                    "size": params.get("size", "portrait"),
                    "style": params.get("style"),
                    "reference_images": None,
                }
            )

            if not gen_result.success:
                return _error(f"Image generation failed: {gen_result.output}")

            # Store the character via the service (copies the file before we exit the with block)
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
        uri = ComicURI.for_character(project, char_slug, version=version)

        return _ok({"uri": str(uri), "version": version})

    async def _resolve_character_image_paths(self, uris: list[str]) -> list[str]:
        """Resolve comic:// character URIs to absolute file paths on disk."""
        from amplifier_module_comic_assets.comic_uri import parse_comic_uri

        paths: list[str] = []
        for raw in uris:
            parsed = parse_comic_uri(raw)
            # Characters are project-scoped in both the URI (v2: comic://project/characters/name)
            # and the service layer — no issue segment needed for retrieval.
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

        with tempfile.TemporaryDirectory(prefix="comic_create_") as output_dir:
            output_path = os.path.join(output_dir, f"{name}.png")

            gen_result = await self._image_gen.execute(
                {
                    "prompt": params["prompt"],
                    "output_path": output_path,
                    "size": params.get("size", "square"),
                    "style": params.get("style"),
                    "reference_images": ref_paths or None,
                }
            )

            if not gen_result.success:
                return _error(f"Image generation failed: {gen_result.output}")

            store_result = await self._service.store_asset(
                project,
                issue,
                "panel",
                name,
                source_path=output_path,
                metadata={
                    "prompt": params["prompt"],
                    "camera_angle": params.get("camera_angle", ""),
                },
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

        with tempfile.TemporaryDirectory(prefix="comic_create_") as output_dir:
            output_path = os.path.join(output_dir, "cover.png")

            gen_result = await self._image_gen.execute(
                {
                    "prompt": params["prompt"],
                    "output_path": output_path,
                    "size": params.get("size", "landscape"),
                    "style": params.get("style"),
                    "reference_images": ref_paths or None,
                }
            )

            if not gen_result.success:
                return _error(f"Image generation failed: {gen_result.output}")

            store_result = await self._service.store_asset(
                project,
                issue,
                "cover",
                name,
                source_path=output_path,
                metadata={
                    "title": params["title"],
                    "subtitle": params.get("subtitle", ""),
                },
            )

        version = store_result["version"]
        uri = ComicURI.for_asset(project, issue, "cover", name, version=version)

        return _ok({"uri": str(uri), "version": version})

    async def _find_vision_provider(self) -> tuple[Any, Any]:
        """Find a vision-capable provider from the coordinator.

        Returns (provider, model_id) or (None, None) if none found.
        """
        if self._coordinator is None:
            return None, None

        try:
            providers = self._coordinator.get("providers") or {}
        except Exception:
            return None, None

        if not providers:
            return None, None

        # Try routing matrix first (optional)
        try:
            state = getattr(self._coordinator, "session_state", {})
            routing_matrix = state.get("routing_matrix")
            if routing_matrix:
                from amplifier_module_hooks_routing.resolver import (  # type: ignore[import-untyped]
                    find_provider_by_type,
                    resolve_model_role,
                )

                resolved = await resolve_model_role(
                    ["vision", "general"], routing_matrix["roles"], providers
                )
                if resolved:
                    match = find_provider_by_type(providers, resolved[0]["provider"])
                    if match:
                        return match[1], resolved[0]["model"]
        except (ImportError, Exception):
            pass

        # Fallback: scan for vision capability
        for name, provider in providers.items():
            try:
                info = provider.get_info()
                caps = (
                    getattr(info, "capabilities", None)
                    or getattr(info, "capability_tags", None)
                    or []
                )
                if "vision" in caps:
                    try:
                        models = await provider.list_models()
                        for m in models:
                            mcaps = (
                                getattr(m, "capabilities", None)
                                or getattr(m, "capability_tags", None)
                                or []
                            )
                            if "vision" in mcaps:
                                return provider, m.id
                    except Exception:
                        pass
                    return provider, None
            except Exception:
                continue

        return None, None

    async def _call_vision_api(
        self, image_parts: list[dict[str, str]], prompt: str
    ) -> dict[str, Any]:
        """Send pre-prepared images + prompt to a vision-capable provider.

        Args:
            image_parts: List of dicts with {type: "base64", media_type: "image/png", data: "base64..."}
                         These are passed directly as ImageBlock.source — no transformation needed.
            prompt: The review prompt.

        Returns:
            {"passed": bool, "feedback": str}
        """
        provider, model = await self._find_vision_provider()
        if provider is None:
            logger.warning("No vision provider available — auto-passing review")
            return {
                "passed": True,
                "feedback": "No vision provider available — auto-passing.",
            }

        try:
            from amplifier_core.message_models import (  # type: ignore[import-untyped]
                ChatRequest,
                ImageBlock,
                Message,
                TextBlock,
            )
        except ImportError:
            logger.warning("amplifier_core.message_models not available — auto-passing")
            return {"passed": True, "feedback": "Vision not available — auto-passing."}

        # Build content blocks from pre-prepared image_parts
        content = []
        for img in image_parts:
            content.append(ImageBlock(type="image", source=img))

        if not content:
            return {"passed": True, "feedback": "No images to review."}

        # Structured prompt requesting JSON output
        prompt_with_structure = (
            f"{prompt}\n\n"
            'Respond with a JSON object: {"passed": true/false, "feedback": "your assessment"}\n'
            "Set passed=false if ANY quality issue is found."
        )
        content.append(TextBlock(type="text", text=prompt_with_structure))

        try:
            response = await provider.complete(
                ChatRequest(
                    messages=[Message(role="user", content=content)],
                    model=model,
                    max_output_tokens=1024,
                )
            )

            # Extract text from response
            text = ""
            for block in response.content:
                if hasattr(block, "type") and block.type == "text":
                    text = block.text
                    break

            if not text:
                return {
                    "passed": True,
                    "feedback": "Vision returned no text — auto-passing.",
                }

            # Parse JSON (with keyword fallback)
            json_match = re.search(
                r'\{[^{}]*"passed"\s*:\s*(true|false)[^{}]*\}', text, re.IGNORECASE
            )
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    return {
                        "passed": parsed.get("passed", False),
                        "feedback": parsed.get("feedback", text),
                    }
                except json.JSONDecodeError:
                    pass

            # Keyword fallback
            text_lower = text.lower()
            failed = any(
                kw in text_lower
                for kw in (
                    "fail",
                    "not pass",
                    "does not pass",
                    "reject",
                    "poor quality",
                )
            )
            return {"passed": not failed, "feedback": text}

        except Exception as exc:
            logger.warning("Vision API call failed: %s — auto-passing", exc)
            return {
                "passed": True,
                "feedback": f"Vision failed ({exc}) — auto-passing.",
            }

    async def _review_asset(self, params: dict[str, Any]) -> ToolResult:
        """Vision-based review. Resolve URI → bytes → base64 → vision API → text feedback.

        This is the orchestrator: it handles all storage resolution and byte
        reading, then passes pre-prepared image_parts to _call_vision_api which
        has ZERO file I/O.
        """
        required = ("uri", "prompt")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        import asyncio
        from pathlib import Path

        from amplifier_module_comic_assets.comic_uri import (
            parse_comic_uri,
            singularize_type,
        )

        raw_uri = params["uri"]
        try:
            parse_comic_uri(raw_uri)
        except ValueError as exc:
            return _error(f"Invalid URI: {exc}")

        async def _resolve_to_image_part(uri: str) -> dict[str, str] | None:
            """Resolve a comic:// URI → read bytes → base64 → image_part dict."""
            try:
                parsed = parse_comic_uri(uri)
            except ValueError:
                return None

            try:
                if parsed.asset_type == "characters":
                    asset = await self._service.get_character(
                        parsed.project,
                        parsed.name,
                        version=parsed.version,
                        include="full",
                        format="path",
                    )
                    image_path = asset.get("image")
                else:
                    asset = await self._service.get_asset(
                        parsed.project,
                        parsed.issue,
                        singularize_type(parsed.asset_type),
                        parsed.name,
                        version=parsed.version,
                        include="full",
                        format="path",
                    )
                    image_path = asset.get("image")
            except (FileNotFoundError, ValueError):
                return None

            if not image_path:
                return None

            try:
                image_bytes = await asyncio.to_thread(Path(image_path).read_bytes)
            except OSError:
                return None

            mime = _detect_mime(image_bytes)
            b64_data = base64.b64encode(image_bytes).decode("ascii")
            return {"type": "base64", "media_type": mime, "data": b64_data}

        # Resolve target
        target_part = await _resolve_to_image_part(raw_uri)
        if target_part is None:
            return _error(f"No image found for URI: {raw_uri}")

        image_parts: list[dict[str, str]] = [target_part]

        # Resolve optional references
        skipped_refs: list[str] = []
        for ref_uri in params.get("reference_uris") or []:
            try:
                ref_part = await _resolve_to_image_part(ref_uri)
                if ref_part:
                    image_parts.append(ref_part)
                else:
                    skipped_refs.append(ref_uri)
            except Exception:
                skipped_refs.append(ref_uri)

        # Call vision — pure, no file I/O
        vision_result = await self._call_vision_api(image_parts, params["prompt"])

        result: dict[str, Any] = {
            "uri": raw_uri,
            "passed": vision_result["passed"],
            "feedback": vision_result["feedback"],
        }
        if skipped_refs:
            result["skipped_refs"] = skipped_refs
        return _ok(result)

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

        from amplifier_module_comic_assets.comic_uri import singularize_type

        try:
            if parsed.asset_type == "characters":
                asset = await self._service.get_character(
                    parsed.project,
                    parsed.name,
                    version=parsed.version,
                    include="full",
                    format="path",
                )
                image_path = asset.get("image")
            else:
                asset = await self._service.get_asset(
                    parsed.project,
                    parsed.issue,
                    singularize_type(parsed.asset_type),
                    parsed.name,
                    version=parsed.version,
                    include="full",
                    format="path",
                )
                image_path = asset.get("image")
        except (FileNotFoundError, ValueError):
            return None

        if not image_path:
            return None

        image_bytes = await asyncio.to_thread(Path(image_path).read_bytes)
        mime = _detect_mime(image_bytes)
        return bytes_to_data_uri(image_bytes, mime)

    async def _resolve_style_css(self, style_uri: str) -> str:
        """Attempt to resolve a comic:// style URI to its CSS text content.

        Returns an empty string if the URI cannot be resolved or is not a
        text/CSS asset (non-fatal — caller falls back to default CSS variables).
        """
        from amplifier_module_comic_assets.comic_uri import parse_comic_uri

        try:
            parsed = parse_comic_uri(style_uri)
        except ValueError:
            return ""

        try:
            asset = await self._service.get_asset(
                parsed.project,
                parsed.issue,
                parsed.asset_type,
                parsed.name,
                version=parsed.version,
                include="full",
                format="content",
            )
            css_content = asset.get("content", "")
            return css_content if isinstance(css_content, str) else ""
        except Exception:
            return ""

    async def _collect_layout_uris(self, layout: dict[str, Any]) -> list[str]:
        """Return every comic:// URI referenced in a layout dict."""
        uris: list[str] = []

        cover = layout.get("cover")
        if cover and cover.get("uri"):
            uris.append(cover["uri"])

        for page in layout.get("pages", []):
            for panel in page.get("panels", []):
                if panel.get("uri"):
                    uris.append(panel["uri"])

        for char in layout.get("characters") or []:
            if char.get("uri"):
                uris.append(char["uri"])

        return uris

    async def _assemble_comic(self, params: dict[str, Any]) -> ToolResult:
        """Resolve all URIs in layout → render proper HTML with SVG bubbles and navigation."""
        import asyncio
        from pathlib import Path

        from .html_renderer import render_comic_html

        required = ("project", "issue", "output_path", "layout")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        layout = params["layout"]
        output_path = params["output_path"]

        # --- Resolve style CSS (non-fatal) ---
        style_css = ""
        style_uri = params.get("style_uri", "")
        if style_uri:
            style_css = await self._resolve_style_css(style_uri)

        # --- Collect and resolve all image URIs in parallel ---
        all_uris = await self._collect_layout_uris(layout)
        data_uris = await asyncio.gather(
            *[self._resolve_image_as_data_uri(uri) for uri in all_uris]
        )
        resolved_images: dict[str, str] = {
            uri: du for uri, du in zip(all_uris, data_uris) if du
        }

        # Count embedded images and pages for the response payload
        images_embedded = len(resolved_images)
        page_count = (
            (
                1
                if layout.get("cover") and layout["cover"].get("uri") in resolved_images
                else 0
            )
            + (1 if layout.get("characters") else 0)
            + len(layout.get("pages", []))
        )

        # --- Render full HTML ---
        html = render_comic_html(layout, resolved_images, style_css)

        await asyncio.to_thread(
            lambda: Path(output_path).write_text(html, encoding="utf-8")
        )

        return _ok(
            {
                "output_path": output_path,
                "pages": page_count,
                "images_embedded": images_embedded,
            }
        )


async def mount(coordinator: Any, config: Any = None) -> None:
    """Amplifier module entry point — retrieve shared service and register the tool.

    Retrieves the ``ComicProjectService`` singleton registered by ``tool-comic-assets``
    via the coordinator capability registry.  ``tool-comic-assets`` **must** be listed
    before ``tool-comic-create`` in the behavior YAML so the capability is available
    at mount time.
    """
    service = coordinator.get_capability("comic.project-service")
    if service is None:
        raise RuntimeError(
            "comic.project-service capability not found. "
            "Ensure tool-comic-assets is included before tool-comic-create in the behavior YAML."
        )

    # Attempt to get the generate_image tool's internal backend.
    # It may not be available (validation dry-run, or image-gen not loaded).
    image_gen = None
    try:
        tools = coordinator.get("tools") or {}
        image_gen = tools.get("generate_image")
    except Exception:
        pass

    tool = ComicCreateTool(
        service=service,
        image_gen=image_gen,
        coordinator=coordinator,  # pass coordinator directly for provider access
    )
    await coordinator.mount("tools", tool, name=tool.name)
