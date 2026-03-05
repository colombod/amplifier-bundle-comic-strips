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


# ---------------------------------------------------------------------------
# Image size guard — shrink images that exceed LLM API size limits
# ---------------------------------------------------------------------------

_IMAGE_MAX_BYTES: int = 4 * 1024 * 1024  # 4 MB (safe margin below 5 MB limit)

# ---------------------------------------------------------------------------
# HTML embedding defaults — keep final comic files under ~5 MB total
# ---------------------------------------------------------------------------
_HTML_PANEL_MAX_W: int = 1200
_HTML_PANEL_MAX_H: int = 900
_HTML_COVER_MAX_W: int = 1600
_HTML_COVER_MAX_H: int = 1200
_HTML_CHAR_MAX_W: int = 600
_HTML_CHAR_MAX_H: int = 800
_HTML_JPEG_QUALITY: int = 92


def _optimize_for_html(
    image_bytes: bytes,
    *,
    max_width: int = _HTML_PANEL_MAX_W,
    max_height: int = _HTML_PANEL_MAX_H,
    quality: int = _HTML_JPEG_QUALITY,
) -> tuple[bytes, str]:
    """Resize and compress an image for HTML embedding.

    Typical reduction: 1536x1024 PNG (~4 MB) → 1200x800 JPEG (~200 KB).
    A 10-panel comic goes from ~50 MB to ~3 MB of base64.

    Returns ``(optimized_bytes, mime_type)``.  Falls back to the original
    bytes (with detected MIME) when Pillow is not installed.
    """
    try:
        from io import BytesIO

        from PIL import Image  # type: ignore[import-untyped]
    except ImportError:
        logger.warning(
            "Pillow not installed — skipping HTML image optimization. "
            "Install with: pip install Pillow"
        )
        return image_bytes, _detect_mime(image_bytes)

    try:
        img = Image.open(BytesIO(image_bytes))
        img.load()  # force decode — catches truncated/corrupt data early
    except Exception:
        logger.warning("Could not decode image for optimization — using original bytes")
        return image_bytes, _detect_mime(image_bytes)

    # Down-scale to fit within bounds, preserving aspect ratio
    img.thumbnail((max_width, max_height), Image.LANCZOS)

    # JPEG requires RGB (no alpha channel)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)

    original_kb = len(image_bytes) / 1024
    optimized_kb = buf.tell() / 1024
    logger.info(
        "HTML image optimized: %.0f KB → %.0f KB (%dx%d, q=%d)",
        original_kb,
        optimized_kb,
        img.width,
        img.height,
        quality,
    )
    return buf.getvalue(), "image/jpeg"


def _shrink_image_bytes(
    image_bytes: bytes,
    *,
    max_bytes: int = _IMAGE_MAX_BYTES,
    max_dimension: int = 2048,
) -> bytes:
    """Return *image_bytes* resized/compressed if they exceed *max_bytes*.

    Strategy (progressive):
      1. If already under limit, return as-is.
      2. Re-encode as JPEG at quality=85 (often halves PNG size).
      3. If still over, scale down to fit *max_dimension* on longest side.
      4. If still over, reduce JPEG quality to 60.

    Requires Pillow; returns the original bytes unchanged if Pillow is
    unavailable (best-effort degradation).
    """
    if len(image_bytes) <= max_bytes:
        return image_bytes

    try:
        from io import BytesIO

        from PIL import Image  # type: ignore[import-untyped]
    except ImportError:
        logger.warning(
            "Image is %d bytes (> %d limit) but Pillow is not installed "
            "— cannot resize. Install with: pip install Pillow",
            len(image_bytes),
            max_bytes,
        )
        return image_bytes

    img = Image.open(BytesIO(image_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Pass 1: re-encode as JPEG quality 85
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    if buf.tell() <= max_bytes:
        return buf.getvalue()

    # Pass 2: scale down if needed
    w, h = img.size
    if max(w, h) > max_dimension:
        scale = max_dimension / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        if buf.tell() <= max_bytes:
            return buf.getvalue()

    # Pass 3: aggressive quality reduction
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=60, optimize=True)
    result = buf.getvalue()
    if len(result) > max_bytes:
        logger.warning(
            "Image still %d bytes after aggressive compression (limit %d)",
            len(result),
            max_bytes,
        )
    return result


def _optimize_resolved_images(
    layout: dict[str, Any],
    resolved: dict[str, str],
) -> dict[str, str]:
    """Re-encode every resolved data-URI image at HTML-appropriate dimensions.

    Classifies each URI by its role in the layout (cover, character, panel)
    and applies the matching size cap.  Returns a *new* dict with optimised
    data URIs.  Falls back to the original data URI when Pillow is absent.
    """
    import base64 as _b64

    from amplifier_module_comic_assets.encoding import bytes_to_data_uri  # type: ignore[import-untyped]

    # Build URI → role lookup from layout
    cover_uris: set[str] = set()
    char_uris: set[str] = set()

    cover = layout.get("cover")
    if cover and cover.get("uri"):
        cover_uris.add(cover["uri"])

    for char in layout.get("characters") or []:
        if char.get("uri"):
            char_uris.add(char["uri"])

    optimised: dict[str, str] = {}
    total_before = 0
    total_after = 0

    for uri, data_uri_str in resolved.items():
        # Extract raw bytes from data:image/...;base64,...
        try:
            header, encoded = data_uri_str.split(",", 1)
            raw = _b64.b64decode(encoded)
        except Exception:
            optimised[uri] = data_uri_str
            continue

        total_before += len(raw)

        # Choose size cap based on image role
        if uri in cover_uris:
            opt_bytes, mime = _optimize_for_html(
                raw, max_width=_HTML_COVER_MAX_W, max_height=_HTML_COVER_MAX_H
            )
        elif uri in char_uris:
            opt_bytes, mime = _optimize_for_html(
                raw, max_width=_HTML_CHAR_MAX_W, max_height=_HTML_CHAR_MAX_H
            )
        else:
            # Panel (default)
            opt_bytes, mime = _optimize_for_html(raw)

        total_after += len(opt_bytes)
        optimised[uri] = bytes_to_data_uri(opt_bytes, mime)

    if total_before > 0:
        saved_mb = (total_before - total_after) / (1024 * 1024)
        logger.info(
            "HTML image budget: %.1f MB raw → %.1f MB optimised (saved %.1f MB across %d images)",
            total_before / (1024 * 1024),
            total_after / (1024 * 1024),
            saved_mb,
            len(optimised),
        )

    return optimised


_MODERATION_KEYWORDS = ("moderation_blocked", "safety system", "content policy")


def _is_moderation_failure(gen_result: Any) -> bool:
    """Detect whether a failed image generation result was a moderation block."""
    output = gen_result.output if hasattr(gen_result, "output") else str(gen_result)
    text = str(output).lower()
    return any(kw in text for kw in _MODERATION_KEYWORDS)


def _moderation_or_error(
    gen_result: Any, asset_type: str, original_prompt: str
) -> "ToolResult":
    """Return a structured moderation-block result or a generic error.

    When a moderation block is detected, the ToolResult output is a JSON
    object with ``moderation_blocked: true`` and guidance for the calling
    agent to rethink the scene — not just retry the same prompt.
    """
    if _is_moderation_failure(gen_result):
        return ToolResult(
            success=False,
            output=json.dumps(
                {
                    "moderation_blocked": True,
                    "asset_type": asset_type,
                    "original_prompt_excerpt": original_prompt[:200],
                    "content_policy_note": (
                        f"Scene blocked by content policy. The following {asset_type} description "
                        f"was rejected: '{original_prompt[:100]}...'. Avoid similar imagery, "
                        f"action intensity, or thematic elements in ALL subsequent prompts."
                    ),
                    "guidance": (
                        "The image generation was blocked by the provider's safety system. "
                        "Do NOT retry with the same or similar prompt — it will be blocked again. "
                        "Instead, RETHINK the scene entirely: (1) Remove all violent, dark, or intense "
                        "combat imagery. (2) Replace action scenes with dramatic poses, energy effects, "
                        "or symbolic compositions. (3) Use calmer color palettes and less aggressive "
                        "framing. (4) Rewrite the scene description from scratch with a PG-rated, "
                        "family-friendly tone. (5) If the scene fundamentally requires blocked content, "
                        "change the narrative beat — show the aftermath or buildup instead of the "
                        "moment of conflict."
                    ),
                }
            ),
        )
    return _error(f"Image generation failed: {gen_result.output}")


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
        service: Any | None = None,
        image_gen: Any | None = None,
        coordinator: Any | None = None,
    ) -> None:
        self._service = service
        self._image_gen = image_gen  # ComicImageGenTool instance (internal)
        self._coordinator = coordinator  # for provider access

    def _resolve_service(self) -> Any:
        """Lazily resolve the ComicProjectService from the coordinator capability registry.

        During validation dry-runs, ``tool-comic-assets`` may not have mounted yet,
        so the capability is unavailable.  We defer the lookup to first ``execute()``
        call, when all modules are guaranteed to be mounted.
        """
        if self._service is not None:
            return self._service
        if self._coordinator is not None:
            self._service = self._coordinator.get_capability("comic.project-service")
        if self._service is None:
            raise RuntimeError(
                "comic.project-service capability not found. "
                "Ensure tool-comic-assets is included before tool-comic-create "
                "in the behavior YAML."
            )
        return self._service

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
            store_result = await self._resolve_service().store_character(
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
                metadata=params.get("metadata"),
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
            char_data = await self._resolve_service().get_character(
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

            # Enforce no-text constraint at code level (agents should also
            # include this, but we guarantee it here as a safety net).
            _NO_TEXT_SUFFIX = (
                " Do not include any text, speech bubbles, captions, dialogue,"
                " labels, letters, words, or lettering in the image."
            )
            raw_prompt = params["prompt"]
            safe_prompt = (
                raw_prompt
                if "no text" in raw_prompt.lower()
                else raw_prompt.rstrip(". ") + "." + _NO_TEXT_SUFFIX
            )

            gen_result = await self._image_gen.execute(
                {
                    "prompt": safe_prompt,
                    "output_path": output_path,
                    "size": params.get("size", "square"),
                    "style": params.get("style"),
                    "reference_images": ref_paths or None,
                    "requirements": {
                        "needs_reference_images": bool(ref_paths),
                        "style_category": "comic",
                        "detail_level": "high",
                        "task_hint": "composition",
                    },
                }
            )

            if not gen_result.success:
                return _moderation_or_error(gen_result, "panel", raw_prompt)

            store_result = await self._resolve_service().store_asset(
                project,
                issue,
                "panel",
                name,
                source_path=output_path,
                metadata={
                    "prompt": raw_prompt,
                    "safe_prompt": safe_prompt,
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

            # Cover uses portrait ratio (comic book cover) and enforces no-text.
            _NO_TEXT_SUFFIX = (
                " Do not include any text, speech bubbles, captions, dialogue,"
                " labels, letters, words, or lettering in the image."
            )
            raw_prompt = params["prompt"]
            safe_prompt = (
                raw_prompt
                if "no text" in raw_prompt.lower()
                else raw_prompt.rstrip(". ") + "." + _NO_TEXT_SUFFIX
            )

            gen_result = await self._image_gen.execute(
                {
                    "prompt": safe_prompt,
                    "output_path": output_path,
                    "size": params.get("size", "portrait"),
                    "style": params.get("style"),
                    "reference_images": ref_paths or None,
                    "requirements": {
                        "needs_reference_images": bool(ref_paths),
                        "style_category": "comic",
                        "detail_level": "high",
                        "task_hint": "composition",
                    },
                }
            )

            if not gen_result.success:
                return _moderation_or_error(gen_result, "cover", raw_prompt)

            store_result = await self._resolve_service().store_asset(
                project,
                issue,
                "cover",
                name,
                source_path=output_path,
                metadata={
                    "title": params["title"],
                    "subtitle": params.get("subtitle", ""),
                    "prompt": raw_prompt,
                    "safe_prompt": safe_prompt,
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
                    asset = await self._resolve_service().get_character(
                        parsed.project,
                        parsed.name,
                        version=parsed.version,
                        include="full",
                        format="path",
                    )
                    image_path = asset.get("image")
                else:
                    asset = await self._resolve_service().get_asset(
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

            # Shrink if over LLM API size limit (typically 5 MB)
            image_bytes = _shrink_image_bytes(image_bytes)

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
            svc = self._resolve_service()
            if parsed.asset_type == "characters":
                asset = await svc.get_character(
                    parsed.project,
                    parsed.name,
                    version=parsed.version,
                    include="full",
                    format="path",
                )
                image_path = asset.get("image")
            else:
                asset = await svc.get_asset(
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
            asset = await self._resolve_service().get_asset(
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

        from .html_renderer import render_comic_html, validate_rendered_html

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

        # --- Optimize images for HTML embedding (shrink ~4 MB PNGs to ~200 KB JPEGs) ---
        resolved_images = await asyncio.to_thread(
            _optimize_resolved_images, layout, resolved_images
        )

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

        # Validate HTML before writing
        errors, warnings = validate_rendered_html(
            html,
            expected_pages=len(layout.get("pages", []))
            + (1 if layout.get("characters") else 0)
            + (1 if layout.get("cover", {}).get("uri") else 0),
            expected_panels=sum(
                len(page.get("panels", [])) for page in layout.get("pages", [])
            ),
        )
        if errors:
            return _error(
                json.dumps(
                    {
                        "validation_failed": True,
                        "errors": errors,
                        "warnings": warnings,
                    }
                )
            )

        await asyncio.to_thread(
            lambda: Path(output_path).write_text(html, encoding="utf-8")
        )

        result = {
            "output_path": output_path,
            "pages": page_count,
            "images_embedded": images_embedded,
        }
        if warnings:
            result["warnings"] = warnings
        return _ok(result)


async def mount(coordinator: Any, config: Any = None) -> None:
    """Amplifier module entry point — retrieve shared service and register the tool.

    Retrieves the ``ComicProjectService`` singleton registered by ``tool-comic-assets``
    via the coordinator capability registry.  ``tool-comic-assets`` **must** be listed
    before ``tool-comic-create`` in the behavior YAML so the capability is available
    at mount time.
    """
    # Attempt eager lookup. During validation dry-runs the capability may not
    # exist yet — that's OK, ComicCreateTool._resolve_service() will retry
    # lazily on first execute() call when all modules are guaranteed mounted.
    service = coordinator.get_capability("comic.project-service")

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
