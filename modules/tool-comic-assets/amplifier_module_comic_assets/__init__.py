"""Comic asset management tools — facade over ComicProjectService.

Exposes four tools (comic_project, comic_character, comic_asset, comic_style)
that manage comic project structure, character designs, issue-scoped assets,
and style guide definitions.  Each tool is a thin facade that validates
input and delegates all business logic to :class:`ComicProjectService`.

Registration entry point: :func:`mount` (called by the Amplifier module loader).
"""

from __future__ import annotations

import json
import logging
import os
import platform
from dataclasses import dataclass
from typing import Any

try:
    import google.genai as genai  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover — optional dependency
    genai = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

try:
    from amplifier_core.models import ToolResult  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover — runs without amplifier_core in tests

    @dataclass
    class ToolResult:  # type: ignore[no-redef]
        """Minimal stand-in used when amplifier_core is not installed."""

        success: bool = False
        output: Any = ""


from .comic_uri import (  # noqa: E402
    COMIC_URI_TYPES,
    ISSUE_SCOPED_TYPES,
    PROJECT_SCOPED_TYPES,
    ComicURI,
    InvalidComicURI,
    parse_comic_uri,
    pluralize_type,
    singularize_type,
)
from .encoding import base64_to_bytes  # noqa: E402
from .service import ComicProjectService  # noqa: E402
from .storage import FileSystemStorage, PathTraversalError, StorageProtocol  # noqa: E402

__amplifier_module_type__ = "tool"

__all__ = [
    "mount",
    "ComicProjectTool",
    "ComicCharacterTool",
    "ComicAssetTool",
    "ComicStyleTool",
    "PathTraversalError",
    "ComicURI",
    "InvalidComicURI",
    "parse_comic_uri",
    "PROJECT_SCOPED_TYPES",
    "ISSUE_SCOPED_TYPES",
    "COMIC_URI_TYPES",
    "pluralize_type",
    "singularize_type",
    "_strip_embedding",
]


# ── Internal helpers ────────────────────────────────────────────────────────


def _require(params: dict[str, Any], *keys: str) -> str | None:
    """Return the name of the first missing key, or *None* if all present."""
    for k in keys:
        if k not in params:
            return k
    return None


def _parse_uri_params(params: dict[str, Any]) -> "ToolResult | None":
    """Populate decomposed params from a ``uri`` entry using :func:`parse_comic_uri`.

    Applies :meth:`dict.setdefault` so that any params already supplied by the
    caller are left untouched (explicit params take priority over URI values).

    Scope-aware behaviour:
    - Project-scoped URIs (characters, styles): ``parsed.issue`` is ``None``
      and ``params["issue"]`` is **not** set.
    - Issue-scoped URIs (panels, covers, etc.): ``parsed.issue`` is present
      and ``params["issue"]`` is set via ``setdefault``.

    The ``type`` param is always singularized so the service layer (which uses
    singular forms such as ``"panel"``) receives the correct value.

    Returns a ``ToolResult`` error if the URI is malformed, or ``None`` when
    the operation succeeds (including when no ``uri`` key is present at all).
    """
    if "uri" not in params:
        return None
    try:
        parsed = parse_comic_uri(params["uri"])
    except ValueError as exc:
        return ToolResult(success=False, output=f"Invalid URI: {exc}")
    params.setdefault("project", parsed.project)
    if parsed.issue is not None:
        params.setdefault("issue", parsed.issue)
    params.setdefault("type", singularize_type(parsed.asset_type))
    params.setdefault("name", parsed.name)
    if parsed.version is not None:
        params.setdefault("version", parsed.version)
    return None


def _missing_error(key: str) -> ToolResult:
    return ToolResult(success=False, output=f"Missing required param: {key}")


def _exc_error(exc: Exception) -> ToolResult:
    return ToolResult(success=False, output=str(exc))


def _ok(result: Any) -> ToolResult:
    return ToolResult(success=True, output=json.dumps(result))


def _strip_embedding(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *metadata* with the ``embedding`` vector removed.

    Keeps ``embedding_model`` and ``embedding_dimensions`` so callers can
    still identify which model produced the embedding without leaking the
    potentially-large vector into agent context.
    """
    return {k: v for k, v in metadata.items() if k != "embedding"}


# ── ComicProjectTool ────────────────────────────────────────────────────────


class ComicProjectTool:
    """Manage comic projects and issues.

    Thin facade over :meth:`ComicProjectService` project / issue methods.
    """

    def __init__(self, service: ComicProjectService) -> None:
        self._service = service

    # ── Tool protocol ──────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "comic_project"

    @property
    def description(self) -> str:
        return (
            "Manage comic projects and issues. Create issues (auto-creates project if "
            "needed), list projects/issues, get issue details, and explicitly clean up "
            "stored assets."
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
                        "create_issue",
                        "update_issue",
                        "list_projects",
                        "list_issues",
                        "get_issue",
                        "cleanup_issue",
                        "cleanup_project",
                    ],
                },
                "project": {
                    "type": "string",
                    "description": (
                        "Project name (human-readable, for create_issue) or project ID "
                        "(slugified form returned by create_issue, for all other actions)."
                    ),
                },
                "issue": {
                    "type": "string",
                    "description": (
                        "Issue ID (e.g. 'issue-001'). Required for get_issue, "
                        "cleanup_issue."
                    ),
                },
                "title": {
                    "type": "string",
                    "description": "Issue title. Required for create_issue; optional for update_issue.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional issue description. Used by create_issue.",
                },
                "metadata": {
                    "type": "object",
                    "description": (
                        "Optional metadata dict stored with the issue (e.g. "
                        "generation trigger, session_file, style, original prompt). "
                        "Useful for auditing, re-running, and benchmarking."
                    ),
                },
            },
            "required": ["action"],
        }

    # ── Execution ──────────────────────────────────────────────────────────

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Dispatch to the appropriate project / issue service method."""
        action = params.get("action")

        # ---- action handlers (inner coroutines) ----

        async def _create_issue() -> ToolResult:
            if m := _require(params, "project", "title"):
                return _missing_error(m)
            try:
                result = await self._service.create_issue(
                    params["project"],
                    params["title"],
                    params.get("description", ""),
                    metadata=params.get("metadata"),
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _update_issue() -> ToolResult:
            if m := _require(params, "project", "issue"):
                return _missing_error(m)
            try:
                result = await self._service.update_issue(
                    params["project"],
                    params["issue"],
                    title=params.get("title"),
                    description=params.get("description"),
                    metadata=params.get("metadata"),
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _list_projects() -> ToolResult:
            try:
                result = await self._service.list_projects()
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _list_issues() -> ToolResult:
            if m := _require(params, "project"):
                return _missing_error(m)
            try:
                result = await self._service.list_issues(params["project"])
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _get_issue() -> ToolResult:
            if m := _require(params, "project", "issue"):
                return _missing_error(m)
            try:
                result = await self._service.get_issue(
                    params["project"], params["issue"]
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _cleanup_issue() -> ToolResult:
            if m := _require(params, "project", "issue"):
                return _missing_error(m)
            try:
                result = await self._service.cleanup_issue(
                    params["project"], params["issue"]
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _cleanup_project() -> ToolResult:
            if m := _require(params, "project"):
                return _missing_error(m)
            try:
                result = await self._service.cleanup_project(params["project"])
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        dispatch: dict[str, Any] = {
            "create_issue": _create_issue,
            "update_issue": _update_issue,
            "list_projects": _list_projects,
            "list_issues": _list_issues,
            "get_issue": _get_issue,
            "cleanup_issue": _cleanup_issue,
            "cleanup_project": _cleanup_project,
        }

        handler = dispatch.get(action)  # type: ignore[arg-type]
        if handler is None:
            valid = ", ".join(sorted(dispatch))
            return ToolResult(
                success=False,
                output=f"Unknown action '{action}'. Valid actions: {valid}",
            )
        return await handler()


# ── ComicCharacterTool ──────────────────────────────────────────────────────


class ComicCharacterTool:
    """Store, retrieve, and browse character designs in the project roster.

    Characters are composite: metadata + reference images, versioned by style.
    Supports cross-project retrieval.
    """

    def __init__(self, service: ComicProjectService) -> None:
        self._service = service

    # ── Tool protocol ──────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "comic_character"

    @property
    def description(self) -> str:
        return (
            "Store, retrieve, and browse character designs in the project roster. "
            "Characters are composite: metadata + reference images, versioned by style. "
            "Supports cross-project retrieval."
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
                        "store",
                        "get",
                        "list",
                        "list_versions",
                        "update_metadata",
                        "search",
                    ],
                },
                "project": {
                    "type": "string",
                    "description": "Project ID. Required for all actions.",
                },
                "issue": {
                    "type": "string",
                    "description": "Issue ID. Required for store.",
                },
                "name": {
                    "type": "string",
                    "description": "Character display name. Required for store, get, list_versions, update_metadata.",
                },
                "style": {
                    "type": "string",
                    "description": (
                        "Art style identifier (e.g. 'manga', 'watercolor'). "
                        "Required for store and update_metadata; optional for get."
                    ),
                },
                "version": {
                    "type": "integer",
                    "description": "Explicit version number. Optional for get; required for update_metadata.",
                },
                "role": {
                    "type": "string",
                    "description": "Character narrative role (e.g. 'hero', 'villain'). Required for store.",
                },
                "character_type": {
                    "type": "string",
                    "description": "Character archetype / type tag. Required for store.",
                },
                "bundle": {
                    "type": "string",
                    "description": "Asset bundle the character belongs to. Required for store.",
                },
                "visual_traits": {
                    "type": "string",
                    "description": "Free-text description of visual traits. Required for store.",
                },
                "team_markers": {
                    "type": "string",
                    "description": "Visual team / faction markers. Required for store.",
                },
                "distinctive_features": {
                    "type": "string",
                    "description": "Distinctive visual features used for consistency. Required for store.",
                },
                "backstory": {
                    "type": "string",
                    "description": "Character backstory narrative. Optional for store.",
                },
                "motivations": {
                    "type": "string",
                    "description": "Character motivations. Optional for store.",
                },
                "personality": {
                    "type": "string",
                    "description": "Personality description. Optional for store.",
                },
                "source_path": {
                    "type": "string",
                    "description": "Absolute filesystem path to the reference image. Optional for store.",
                },
                "data": {
                    "type": "string",
                    "description": "Base64-encoded reference image bytes. Optional for store.",
                },
                "include": {
                    "type": "string",
                    "description": "What to include in the response: 'metadata' (default) or 'full' (adds image).",
                    "enum": ["metadata", "full"],
                    "default": "metadata",
                },
                "format": {
                    "type": "string",
                    "description": "Image format when include='full'. Only 'path' is supported.",
                    "enum": ["path"],
                    "default": "path",
                },
                "review_status": {
                    "type": "string",
                    "description": "Review status tag to write (for update_metadata).",
                },
                "review_feedback": {
                    "type": "string",
                    "description": "Review feedback text to write (for update_metadata).",
                },
                "metadata": {
                    "type": "object",
                    "description": "Arbitrary metadata dict (for store and update_metadata). On store, attached to the new character. On update_metadata, merged into existing.",
                },
                "metadata_filter": {
                    "type": "object",
                    "description": "Filter characters by metadata key/value pairs. Only characters whose metadata contains all specified entries are returned. Used with the search action.",
                },
                "uri": {
                    "type": "string",
                    "description": (
                        "comic:// URI (alternative to separate project/name params). "
                        "Project-scoped format: comic://project/characters/name[?v=N]."
                    ),
                },
            },
            "required": ["action"],
        }

    # ── Execution ──────────────────────────────────────────────────────────

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Dispatch to the appropriate character service method."""
        if err := _parse_uri_params(params):
            return err
        action = params.get("action")

        async def _store() -> ToolResult:
            required = (
                "project",
                "issue",
                "name",
                "style",
                "role",
                "character_type",
                "bundle",
                "visual_traits",
                "team_markers",
                "distinctive_features",
            )
            if m := _require(params, *required):
                return _missing_error(m)
            # Decode base64 data if provided
            data_bytes: bytes | None = None
            if "data" in params:
                try:
                    data_bytes = base64_to_bytes(params["data"])
                except Exception as exc:
                    return ToolResult(
                        success=False,
                        output=f"Failed to decode base64 data: {exc}",
                    )
            try:
                result = await self._service.store_character(
                    params["project"],
                    params["issue"],
                    params["name"],
                    params["style"],
                    role=params["role"],
                    character_type=params["character_type"],
                    bundle=params["bundle"],
                    visual_traits=params["visual_traits"],
                    team_markers=params["team_markers"],
                    distinctive_features=params["distinctive_features"],
                    backstory=params.get("backstory", ""),
                    motivations=params.get("motivations", ""),
                    personality=params.get("personality", ""),
                    metadata=params.get("metadata"),
                    source_path=params.get("source_path"),
                    data=data_bytes,
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _get() -> ToolResult:
            if m := _require(params, "project", "name"):
                return _missing_error(m)
            fmt = params.get("format", "path")
            if fmt in ("base64", "data_uri"):
                return ToolResult(
                    success=False,
                    output=f"format='{fmt}' is no longer supported. Use format='path'.",
                )
            version_raw = params.get("version")
            version: int | None = int(version_raw) if version_raw is not None else None
            try:
                result = await self._service.get_character(
                    params["project"],
                    params["name"],
                    style=params.get("style"),
                    version=version,
                    include=params.get("include", "metadata"),
                    format=fmt,
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _list() -> ToolResult:
            if m := _require(params, "project"):
                return _missing_error(m)
            try:
                result = await self._service.list_characters(params["project"])
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _list_versions() -> ToolResult:
            if m := _require(params, "project", "name"):
                return _missing_error(m)
            try:
                result = await self._service.list_character_versions(
                    params["project"], params["name"]
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _update_metadata() -> ToolResult:
            if m := _require(params, "project", "name", "style", "version"):
                return _missing_error(m)
            try:
                result = await self._service.update_character_metadata(
                    params["project"],
                    params["name"],
                    params["style"],
                    int(params["version"]),
                    review_status=params.get("review_status"),
                    review_feedback=params.get("review_feedback"),
                    metadata=params.get("metadata"),
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _search() -> ToolResult:
            result = await self._service.search_characters(
                style=params.get("style"),
                metadata_filter=params.get("metadata_filter"),
                project_id=params.get("project"),
            )
            return _ok(result)

        dispatch: dict[str, Any] = {
            "store": _store,
            "get": _get,
            "list": _list,
            "list_versions": _list_versions,
            "update_metadata": _update_metadata,
            "search": _search,
        }

        handler = dispatch.get(action)  # type: ignore[arg-type]
        if handler is None:
            valid = ", ".join(sorted(dispatch))
            return ToolResult(
                success=False,
                output=f"Unknown action '{action}'. Valid actions: {valid}",
            )
        return await handler()


# ── ComicAssetTool ──────────────────────────────────────────────────────────


class ComicAssetTool:
    """Store, retrieve, and browse issue-scoped assets.

    Covers panels, cover, research, storyboard, QA screenshots, and the
    final comic.  All assets are versioned.  Returns metadata by default —
    opt in to payloads with include='full'.
    """

    def __init__(self, service: ComicProjectService) -> None:
        self._service = service

    # ── Tool protocol ──────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "comic_asset"

    @property
    def description(self) -> str:
        return (
            "Store, retrieve, and browse issue-scoped assets (panels, cover, research, "
            "storyboard, QA screenshots, final comic). All assets are versioned. "
            "Returns metadata by default — opt in to payloads."
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
                        "store",
                        "get",
                        "list",
                        "update_metadata",
                        "preview",
                    ],
                },
                "project": {
                    "type": "string",
                    "description": "Project ID. Required for all actions.",
                },
                "issue": {
                    "type": "string",
                    "description": "Issue ID. Required for all actions.",
                },
                "type": {
                    "type": "string",
                    "description": (
                        "Asset type. One of: panel, cover, avatar, qa_screenshot, "
                        "research, storyboard, final. Required for store, get, "
                        "update_metadata; optional filter for list."
                    ),
                    "enum": [
                        "panel",
                        "cover",
                        "avatar",
                        "qa_screenshot",
                        "research",
                        "storyboard",
                        "final",
                    ],
                },
                "name": {
                    "type": "string",
                    "description": (
                        "Asset name (e.g. 'panel_01'). Required for store, get, "
                        "update_metadata."
                    ),
                },
                "version": {
                    "type": "integer",
                    "description": "Explicit version number. Optional for get; required for update_metadata.",
                },
                "source_path": {
                    "type": "string",
                    "description": "Absolute filesystem path to the asset file. One of source_path/data/content required for store.",
                },
                "data": {
                    "type": "string",
                    "description": "Base64-encoded asset bytes. One of source_path/data/content required for store.",
                },
                "content": {
                    "type": "object",
                    "description": "Structured content dict (for research, storyboard, final asset types). One of source_path/data/content required for store.",
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata dict to attach to the asset (store) or merge (update_metadata).",
                },
                "include": {
                    "type": "string",
                    "description": "What to return: 'metadata' (default) or 'full' (adds payload).",
                    "enum": ["metadata", "full"],
                    "default": "metadata",
                },
                "format": {
                    "type": "string",
                    "description": "Payload format when include='full'. Only 'path' is supported.",
                    "enum": ["path"],
                    "default": "path",
                },
                "review_status": {
                    "type": "string",
                    "description": "Review status tag (for update_metadata).",
                },
                "review_feedback": {
                    "type": "string",
                    "description": "Review feedback text (for update_metadata).",
                },
                "uri": {
                    "type": "string",
                    "description": (
                        "comic:// URI (alternative to separate project/issue/type/name params). "
                        "Issue-scoped format: comic://project/issues/issue-id/collection/name[?v=N]."
                    ),
                },
            },
            "required": ["action"],
        }

    # ── Execution ──────────────────────────────────────────────────────────

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Dispatch to the appropriate asset service method."""
        if err := _parse_uri_params(params):
            return err
        action = params.get("action")

        async def _store() -> ToolResult:
            if m := _require(params, "project", "issue", "type", "name"):
                return _missing_error(m)
            # Exactly one of source_path / data / content must be provided,
            # but we leave that enforcement to the service layer (it raises ValueError).
            data_bytes: bytes | None = None
            if "data" in params:
                try:
                    data_bytes = base64_to_bytes(params["data"])
                except Exception as exc:
                    return ToolResult(
                        success=False,
                        output=f"Failed to decode base64 data: {exc}",
                    )
            try:
                result = await self._service.store_asset(
                    params["project"],
                    params["issue"],
                    params["type"],
                    params["name"],
                    source_path=params.get("source_path"),
                    data=data_bytes,
                    content=params.get("content"),
                    metadata=params.get("metadata"),
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _get() -> ToolResult:
            if m := _require(params, "project", "issue", "type", "name"):
                return _missing_error(m)
            fmt = params.get("format", "path")
            if fmt in ("base64", "data_uri"):
                return ToolResult(
                    success=False,
                    output=f"format='{fmt}' is no longer supported. Use format='path'.",
                )
            version_raw = params.get("version")
            version: int | None = int(version_raw) if version_raw is not None else None
            try:
                result = await self._service.get_asset(
                    params["project"],
                    params["issue"],
                    params["type"],
                    params["name"],
                    version=version,
                    include=params.get("include", "metadata"),
                    format=fmt,
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _list() -> ToolResult:
            if m := _require(params, "project", "issue"):
                return _missing_error(m)
            try:
                result = await self._service.list_assets(
                    params["project"],
                    params["issue"],
                    asset_type=params.get("type"),
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _update_metadata() -> ToolResult:
            if m := _require(params, "project", "issue", "type", "name", "version"):
                return _missing_error(m)
            try:
                result = await self._service.update_asset_metadata(
                    params["project"],
                    params["issue"],
                    params["type"],
                    params["name"],
                    int(params["version"]),
                    review_status=params.get("review_status"),
                    review_feedback=params.get("review_feedback"),
                    metadata=params.get("metadata"),
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _preview() -> ToolResult:
            if m := _require(params, "project", "issue", "type", "name"):
                return _missing_error(m)
            try:
                asset = await self._service.get_asset(
                    params["project"],
                    params["issue"],
                    params["type"],
                    params["name"],
                    include="full",
                    format="path",
                )
                hint_cmd = "open" if platform.system() == "Darwin" else "xdg-open"
                return _ok(
                    {
                        "uri": asset.get("uri", ""),
                        "path": asset.get("image", ""),
                        "type": asset.get("mime_type", "application/octet-stream"),
                        "hint": hint_cmd,
                    }
                )
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        dispatch: dict[str, Any] = {
            "store": _store,
            "get": _get,
            "list": _list,
            "update_metadata": _update_metadata,
            "preview": _preview,
        }

        handler = dispatch.get(action)  # type: ignore[arg-type]
        if handler is None:
            valid = ", ".join(sorted(dispatch))
            return ToolResult(
                success=False,
                output=f"Unknown action '{action}'. Valid actions: {valid}",
            )
        return await handler()


# ── ComicStyleTool ──────────────────────────────────────────────────────────


class ComicStyleTool:
    """Store, retrieve, and browse style guide definitions.

    Style guides are full visual language definitions reusable across issues
    and retrievable across projects.
    """

    def __init__(self, service: ComicProjectService) -> None:
        self._service = service

    # ── Tool protocol ──────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "comic_style"

    @property
    def description(self) -> str:
        return (
            "Store, retrieve, and browse style guide definitions. Style guides are full "
            "visual language definitions reusable across issues and retrievable across "
            "projects."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Operation to perform.",
                    "enum": ["store", "get", "list"],
                },
                "project": {
                    "type": "string",
                    "description": "Project ID. Required for all actions.",
                },
                "issue": {
                    "type": "string",
                    "description": "Issue ID that originates this style guide. Required for store.",
                },
                "name": {
                    "type": "string",
                    "description": "Style guide name (e.g. 'manga-action'). Required for store and get.",
                },
                "definition": {
                    "type": "object",
                    "description": "Full style guide definition dict. Required for store.",
                },
                "version": {
                    "type": "integer",
                    "description": "Explicit version to retrieve. Optional for get; defaults to latest.",
                },
                "include": {
                    "type": "string",
                    "description": "What to return: 'metadata' (default) or 'full' (adds definition dict).",
                    "enum": ["metadata", "full"],
                    "default": "metadata",
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata dict to attach to the style guide (for store).",
                },
                "uri": {
                    "type": "string",
                    "description": (
                        "comic:// URI (alternative to separate project/name params). "
                        "Project-scoped format: comic://project/styles/name[?v=N]."
                    ),
                },
            },
            "required": ["action"],
        }

    # ── Execution ──────────────────────────────────────────────────────────

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Dispatch to the appropriate style service method."""
        if err := _parse_uri_params(params):
            return err
        action = params.get("action")

        async def _store() -> ToolResult:
            if m := _require(params, "project", "issue", "name", "definition"):
                return _missing_error(m)
            try:
                result = await self._service.store_style(
                    params["project"],
                    params["issue"],
                    params["name"],
                    params["definition"],
                    metadata=params.get("metadata"),
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _get() -> ToolResult:
            if m := _require(params, "project", "name"):
                return _missing_error(m)
            version_raw = params.get("version")
            version: int | None = int(version_raw) if version_raw is not None else None
            try:
                result = await self._service.get_style(
                    params["project"],
                    params["name"],
                    version=version,
                    include=params.get("include", "metadata"),
                )
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        async def _list() -> ToolResult:
            if m := _require(params, "project"):
                return _missing_error(m)
            try:
                result = await self._service.list_styles(params["project"])
                return _ok(result)
            except (ValueError, FileNotFoundError) as exc:
                return _exc_error(exc)

        dispatch: dict[str, Any] = {
            "store": _store,
            "get": _get,
            "list": _list,
        }

        handler = dispatch.get(action)  # type: ignore[arg-type]
        if handler is None:
            valid = ", ".join(sorted(dispatch))
            return ToolResult(
                success=False,
                output=f"Unknown action '{action}'. Valid actions: {valid}",
            )
        return await handler()


# ── Module mount point ──────────────────────────────────────────────────────


def _build_storage(storage_cfg: dict[str, Any]) -> StorageProtocol:
    """Instantiate the correct storage backend from configuration.

    Config shape::

        storage:
          backend: filesystem        # default; future: "s3", "azure-blob", …
          filesystem:
            root: ".comic-assets"    # optional, defaults to .comic-assets in CWD
          # s3:                      # future
          #   bucket: "my-comics"
          #   prefix: "assets/"

    If *storage_cfg* is empty or missing, falls back to filesystem with
    default root (``.comic-assets`` relative to CWD).
    """
    backend = storage_cfg.get("backend", "filesystem")

    if backend == "filesystem":
        fs_cfg = storage_cfg.get("filesystem", {})
        root = fs_cfg.get("root", ".comic-assets")
        return FileSystemStorage(root=root)

    raise ValueError(
        f"Unknown storage backend '{backend}'. Supported backends: filesystem"
    )


async def mount(coordinator: Any, config: Any = None) -> Any:
    """Amplifier module entry point — build service and register all four tools.

    Returns a cleanup callable that performs any necessary teardown.
    The capability registered under ``"comic.project-service"`` is automatically
    removed by the coordinator at session end; no explicit unregistration needed.
    """
    cfg = config or {}
    storage = _build_storage(cfg.get("storage", {}))
    service = ComicProjectService(storage=storage)

    # ── Gemini embedding-client discovery ────────────────────────────────────
    embedding_dim: int = cfg.get("asset_embedding_dimension", 1536)
    genai_client: Any = None

    # Phase 1 – coordinator providers
    providers = coordinator.get("providers") if callable(getattr(coordinator, "get", None)) else None
    if providers and hasattr(providers, "items"):
        for name, provider in providers.items():
            name_lower = name.lower() if isinstance(name, str) else ""
            if "gemini" in name_lower or "google" in name_lower:
                client = getattr(provider, "client", None)
                if client is not None:
                    genai_client = client
                    break

    # Phase 2 – environment-variable fallback
    if genai_client is None and genai is not None:
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai_client = genai.Client(api_key=api_key)

    if genai_client is not None:
        service.set_embedding_client(genai_client, embedding_dim=embedding_dim)
        logger.info(
            "tool-comic-assets: Gemini embedding client configured (dim=%d)", embedding_dim
        )
    else:
        logger.debug("tool-comic-assets: No Gemini client found; embeddings disabled")
    # ─────────────────────────────────────────────────────────────────────────

    tools = [
        ComicProjectTool(service),
        ComicCharacterTool(service),
        ComicAssetTool(service),
        ComicStyleTool(service),
    ]
    for tool in tools:
        await coordinator.mount("tools", tool, name=tool.name)

    coordinator.register_capability("comic.project-service", service)

    def _cleanup() -> None:
        logger.debug("tool-comic-assets: cleanup called")

    return _cleanup
