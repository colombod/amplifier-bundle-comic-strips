"""High-level comic creation tool — orchestrates image generation, storage, review, and assembly.

Agents work with comic:// URIs. Binary image data never enters conversation context.
All image plumbing (generation, storage, encoding, vision API) is internal.

Registration entry point: :func:`mount` (called by the Amplifier module loader).
"""

from __future__ import annotations

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

# Vision model defaults — override via config if needed
_VISION_MODEL_ANTHROPIC = "claude-opus-4-5"
_VISION_MODEL_OPENAI = "gpt-4o"
_VISION_MODEL_GOOGLE = "gemini-2.0-flash"


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
        vision_provider: Any | None = None,
        vision_models: dict[str, str] | None = None,
    ) -> None:
        self._service = service
        self._image_gen = image_gen  # ComicImageGenTool instance (internal)
        self._vision_provider = vision_provider  # For review_asset
        # Per-provider model selection — falls back to module-level defaults
        self._vision_models: dict[str, str] = vision_models or {
            "anthropic": _VISION_MODEL_ANTHROPIC,
            "openai": _VISION_MODEL_OPENAI,
            "google": _VISION_MODEL_GOOGLE,
        }

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

    async def _call_vision_api(
        self, image_paths: list[str], prompt: str
    ) -> dict[str, Any]:
        """Send images + review prompt to a vision-capable model.

        Reads image files from disk, encodes as base64, and calls the
        configured vision provider. Image bytes travel only on the wire;
        they never appear in the returned dict or the tool result.

        Returns {"passed": bool, "feedback": str}.
        Falls back to auto-pass (with a warning) when no provider is
        configured or when the provider call fails.
        """
        if self._vision_provider is None:
            logger.warning("No vision provider available — auto-passing review")
            return {
                "passed": True,
                "feedback": "Vision review not available — auto-passing.",
            }

        import asyncio
        import base64
        from pathlib import Path

        # Read images and encode as base64 (stays in memory, never serialised)
        image_parts: list[dict[str, str]] = []
        for path in image_paths:
            try:
                image_bytes = await asyncio.to_thread(Path(path).read_bytes)
            except OSError as exc:
                logger.warning("Vision API: could not read image %s: %s", path, exc)
                continue

            media_type = _detect_mime(image_bytes)
            b64_data = base64.b64encode(image_bytes).decode("ascii")
            image_parts.append({"data": b64_data, "media_type": media_type})

        if not image_parts:
            logger.warning("Vision API: no readable images — auto-passing review")
            return {
                "passed": True,
                "feedback": "No readable images found — auto-passing.",
            }

        # Ask the model for structured JSON output to avoid brittle keyword matching
        prompt_with_structure = (
            f"{prompt}\n\n"
            'Respond with a JSON object: {"passed": true/false, "feedback": "your assessment"}\n'
            "Set passed=false if ANY quality issue is found. Set passed=true only if all checks pass."
        )

        try:
            text = await self._invoke_vision_provider(
                image_parts, prompt_with_structure
            )
        except Exception as exc:
            logger.warning(
                "Vision API call failed: %s — auto-passing review", exc, exc_info=True
            )
            return {
                "passed": True,
                "feedback": f"Vision API error ({exc}) — auto-passing.",
            }

        # Try to extract JSON from the response first
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

        # Fallback to keyword detection if JSON parsing fails
        text_lower = text.lower()
        failed = any(
            kw in text_lower
            for kw in (
                "fail",
                "not pass",
                "does not pass",
                "incorrect",
                "does not meet",
            )
        )
        return {"passed": not failed, "feedback": text}

    async def _invoke_vision_provider(
        self, image_parts: list[dict[str, str]], prompt: str
    ) -> str:
        """Dispatch the vision call to the right provider API.

        Detects provider type from ``provider.name`` and calls the
        corresponding chat/messages endpoint with base64-encoded images.

        Returns the raw text response from the model.
        Raises on API errors (caller handles graceful fallback).
        """
        provider = self._vision_provider
        provider_name: str = getattr(provider, "name", "").lower()
        client = provider.client

        if "anthropic" in provider_name:
            content: list[dict[str, Any]] = []
            for img in image_parts:
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": img["media_type"],
                            "data": img["data"],
                        },
                    }
                )
            content.append({"type": "text", "text": prompt})
            response = await client.messages.create(
                model=self._vision_models.get("anthropic", _VISION_MODEL_ANTHROPIC),
                max_tokens=1024,
                messages=[{"role": "user", "content": content}],
            )
            return str(response.content[0].text)

        if "openai" in provider_name:
            msg_content: list[dict[str, Any]] = []
            for img in image_parts:
                data_uri = f"data:{img['media_type']};base64,{img['data']}"
                msg_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": data_uri},
                    }
                )
            msg_content.append({"type": "text", "text": prompt})
            response = await client.chat.completions.create(
                model=self._vision_models.get("openai", _VISION_MODEL_OPENAI),
                max_tokens=1024,
                messages=[{"role": "user", "content": msg_content}],
            )
            return str(response.choices[0].message.content)

        if "google" in provider_name or "gemini" in provider_name:
            import base64 as _b64

            from google.genai import types  # type: ignore[import-untyped]

            parts: list[Any] = []
            for img in image_parts:
                img_bytes = _b64.b64decode(img["data"])
                parts.append(
                    types.Part.from_bytes(data=img_bytes, mime_type=img["media_type"])
                )
            parts.append(types.Part.from_text(text=prompt))
            response = await client.aio.models.generate_content(
                model=self._vision_models.get("google", _VISION_MODEL_GOOGLE),
                contents=parts,
            )
            return str(response.text)

        raise ValueError(
            f"Unsupported vision provider '{provider_name}'. "
            "Expected a provider whose name contains 'anthropic', 'openai', "
            "'google', or 'gemini'."
        )

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
        from amplifier_module_comic_assets.comic_uri import singularize_type

        try:
            if parsed.asset_type == "characters":
                # Characters are project-scoped in both the URI and service layer.
                asset_data = await self._service.get_character(
                    parsed.project,
                    parsed.name,
                    version=parsed.version,
                    include="full",
                    format="path",
                )
                image_path = asset_data.get("image")
            else:
                asset_data = await self._service.get_asset(
                    parsed.project,
                    parsed.issue,
                    singularize_type(parsed.asset_type),
                    parsed.name,
                    version=parsed.version,
                    include="full",
                    format="path",
                )
                image_path = asset_data.get("image")
        except (FileNotFoundError, ValueError) as exc:
            return _error(f"Cannot resolve URI {raw_uri}: {exc}")

        if not image_path:
            return _error(f"No image found for URI: {raw_uri}")

        # Collect all image paths for vision (target + optional references)
        all_paths = [image_path]
        skipped_refs: list[str] = []

        reference_uris = params.get("reference_uris") or []
        for ref_raw in reference_uris:
            try:
                ref_parsed = parse_comic_uri(ref_raw)
                if ref_parsed.asset_type == "characters":
                    ref_data = await self._service.get_character(
                        ref_parsed.project,
                        ref_parsed.name,
                        version=ref_parsed.version,
                        include="full",
                        format="path",
                    )
                    ref_image = ref_data.get("image")
                else:
                    ref_data = await self._service.get_asset(
                        ref_parsed.project,
                        ref_parsed.issue,
                        singularize_type(ref_parsed.asset_type),
                        ref_parsed.name,
                        version=ref_parsed.version,
                        include="full",
                        format="path",
                    )
                    ref_image = ref_data.get("image")
                if ref_image:
                    all_paths.append(ref_image)
                else:
                    skipped_refs.append(ref_raw)
            except (FileNotFoundError, ValueError):
                skipped_refs.append(ref_raw)

        # Call vision API — images sent to API wire, never to LLM context
        vision_result = await self._call_vision_api(all_paths, params["prompt"])

        result_data: dict[str, Any] = {
            "uri": raw_uri,
            "passed": vision_result.get("passed", False),
            "feedback": vision_result.get("feedback", ""),
        }
        if skipped_refs:
            result_data["skipped_refs"] = skipped_refs

        return _ok(result_data)

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


def _discover_vision_provider(providers: dict[str, Any]) -> Any | None:
    """Find the first vision-capable provider from coordinator providers.

    Checks provider names for known vision-capable platforms in priority order:
    Anthropic Claude > OpenAI > Google/Gemini.

    Returns the provider object if found, or None.
    """
    # Priority order for vision: anthropic has best multimodal; then openai, google
    vision_keys = ("anthropic", "openai", "google", "gemini")
    for key in vision_keys:
        for provider_name, provider in providers.items():
            if key in provider_name.lower():
                logger.info(
                    "comic_create: discovered vision provider '%s' for review_asset",
                    provider_name,
                )
                return provider
    return None


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

    # Discover a vision-capable provider for review_asset.
    # Falls back to None gracefully — review_asset auto-passes when absent.
    vision_provider = None
    try:
        providers = coordinator.get("providers") or {}
        vision_provider = _discover_vision_provider(providers)
        if vision_provider is None:
            logger.warning(
                "comic_create: no vision-capable provider found "
                "(providers: %s). review_asset will auto-pass.",
                list(providers.keys()) or "(none)",
            )
    except Exception:
        logger.warning(
            "comic_create: could not query coordinator providers — "
            "review_asset will auto-pass.",
            exc_info=True,
        )

    vision_config = cfg.get("vision", {})
    vision_models = {
        "anthropic": vision_config.get("anthropic_model", _VISION_MODEL_ANTHROPIC),
        "openai": vision_config.get("openai_model", _VISION_MODEL_OPENAI),
        "google": vision_config.get("google_model", _VISION_MODEL_GOOGLE),
    }

    tool = ComicCreateTool(
        service=service,
        image_gen=image_gen,
        vision_provider=vision_provider,
        vision_models=vision_models,
    )
    await coordinator.mount("tools", tool, name=tool.name)
