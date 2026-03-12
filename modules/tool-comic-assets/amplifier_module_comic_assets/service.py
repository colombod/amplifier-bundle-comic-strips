"""Business-logic service for comic-asset management.

All methods are async-safe.  Writes acquire a per-project lock to prevent
concurrent manifest corruption.  Reads are always lock-free.

Filesystem layout (relative to storage root `.comic-assets/`):

    workspace.json
    projects/{project_id}/
        project.json
        characters/{char_slug}/{style_slug}_v{n}/
            metadata.json
            reference.png
        styles/{style_slug}_v{n}/
            definition.json
        issues/{issue_id}/
            issue.json
            research/v{n}/data.json
            storyboard/v{n}/data.json
            final/v{n}/comic.html
            panels/{name}_v{n}/metadata.json + image.*
            cover/{name}_v{n}/metadata.json + image.*
            avatar/{name}_v{n}/metadata.json + image.*
            qa_screenshots/{name}_v{n}/metadata.json + image.*
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.genai.types import EmbedContentConfig, Part

from .comic_uri import ComicURI
from .encoding import bytes_to_base64, bytes_to_data_uri, guess_mime
from .models import (
    ASSET_TYPES,
    Asset,
    CharacterDesign,
    StyleGuide,
    slugify,
)
from .storage import StorageProtocol

logger = logging.getLogger(__name__)

_SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Return the cosine similarity between two vectors.

    Returns 0.0 if either vector has zero norm (to avoid division by zero).
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _validate_id(value: str, label: str) -> str:
    """Validate that value is a safe identifier."""
    if not value or not _SAFE_ID_RE.match(value):
        raise ValueError(
            f"Invalid {label}: {value!r}. "
            f"Must match [a-z0-9][a-z0-9_-]* (no slashes, no '..', no uppercase)."
        )
    return value


# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

# Structured assets: single versioned file, no name subdirectory.
_STRUCTURED_TYPES: frozenset[str] = frozenset({"research", "storyboard", "final"})

# Filesystem subdirectory name per asset type (within the issue directory).
_ASSET_SUBDIR: dict[str, str] = {
    "research": "research",
    "storyboard": "storyboard",
    "final": "final",
    "panel": "panels",
    "cover": "cover",
    "avatar": "avatar",
    "qa_screenshot": "qa_screenshots",
}

# File name for structured content inside the versioned directory.
_STRUCTURED_FILENAME: dict[str, str] = {
    "research": "data.json",
    "storyboard": "data.json",
    "final": "comic.html",
}

# MIME type for structured content files.
_STRUCTURED_MIME: dict[str, str] = {
    "research": "application/json",
    "storyboard": "application/json",
    "final": "text/html",
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ComicProjectService:
    """Core service — all business logic for comic asset management.

    STATELESS about 'current' project/issue.  Every method receives
    project_id and/or issue_id explicitly.
    """

    def __init__(self, storage: StorageProtocol) -> None:
        self._storage = storage
        self._locks: dict[str, asyncio.Lock] = {}
        self._meta_lock = asyncio.Lock()
        self._genai_client: Any | None = None
        self._embedding_dim: int = 1536

    def set_embedding_client(
        self, client: Any | None, embedding_dim: int = 1536
    ) -> None:
        """Set the generative AI client and embedding dimension for embeddings."""
        self._genai_client = client
        self._embedding_dim = embedding_dim

    async def _compute_embedding(
        self, image_path: str | None, text: str | None
    ) -> list[float] | None:
        """Compute a multimodal embedding via the Gemini Embedding 2 API.

        Returns None when no client is configured, no input is provided, or
        the API call raises an exception (error is logged at DEBUG level).
        """
        if self._genai_client is None:
            return None

        parts: list[Any] = []
        if image_path is not None:
            image_bytes = await asyncio.to_thread(Path(image_path).read_bytes)
            parts.append(
                Part.from_bytes(data=image_bytes, mime_type=guess_mime(image_path))
            )
        if text is not None:
            parts.append(Part.from_text(text=text))

        if not parts:
            return None

        try:
            result = await self._genai_client.aio.models.embed_content(
                model="gemini-embedding-2-preview",
                contents=parts,
                config=EmbedContentConfig(
                    output_dimensionality=self._embedding_dim,
                    task_type="SEMANTIC_SIMILARITY",
                ),
            )
            return list(result.embeddings[0].values)
        except Exception:
            logger.debug("_compute_embedding failed", exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_lock(self, project_id: str) -> asyncio.Lock:
        """Get or create a per-project asyncio.Lock (meta-lock protected)."""
        async with self._meta_lock:
            if project_id not in self._locks:
                self._locks[project_id] = asyncio.Lock()
            return self._locks[project_id]

    def _now(self) -> str:
        """Return current UTC time as ISO 8601 string."""
        return datetime.now(timezone.utc).isoformat()

    async def _read_workspace(self) -> dict[str, Any]:
        """Read workspace.json; return empty structure if missing."""
        try:
            text = await self._storage.read_text("workspace.json")
            return json.loads(text)
        except FileNotFoundError:
            return {"version": 1, "projects": [], "updated_at": self._now()}

    async def _write_workspace(self, data: dict[str, Any]) -> None:
        """Write workspace.json."""
        await self._storage.write_text("workspace.json", json.dumps(data, indent=2))

    async def _read_project_manifest(self, project_id: str) -> dict[str, Any]:
        """Read projects/{project_id}/project.json."""
        path = f"projects/{project_id}/project.json"
        text = await self._storage.read_text(path)
        return json.loads(text)

    async def _write_project_manifest(
        self, project_id: str, data: dict[str, Any]
    ) -> None:
        """Write projects/{project_id}/project.json."""
        path = f"projects/{project_id}/project.json"
        await self._storage.write_text(path, json.dumps(data, indent=2))

    async def _read_issue_manifest(
        self, project_id: str, issue_id: str
    ) -> dict[str, Any]:
        """Read projects/{project_id}/issues/{issue_id}/issue.json."""
        path = f"projects/{project_id}/issues/{issue_id}/issue.json"
        text = await self._storage.read_text(path)
        return json.loads(text)

    async def _write_issue_manifest(
        self, project_id: str, issue_id: str, data: dict[str, Any]
    ) -> None:
        """Write projects/{project_id}/issues/{issue_id}/issue.json."""
        path = f"projects/{project_id}/issues/{issue_id}/issue.json"
        await self._storage.write_text(path, json.dumps(data, indent=2))

    def _asset_version_dir(
        self,
        project_id: str,
        issue_id: str,
        asset_type: str,
        name: str,
        version: int,
    ) -> str:
        """Build the relative path to a versioned asset directory."""
        subdir = _ASSET_SUBDIR[asset_type]
        base = f"projects/{project_id}/issues/{issue_id}"
        if asset_type in _STRUCTURED_TYPES:
            # research/v1, storyboard/v1, final/v1
            return f"{base}/{subdir}/v{version}"
        else:
            # panels/panel_01_v1, cover/cover_v1, …
            return f"{base}/{subdir}/{name}_v{version}"

    # ------------------------------------------------------------------
    # Project & Issue
    # ------------------------------------------------------------------

    async def create_issue(
        self,
        project_name: str,
        title: str,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new issue, auto-creating the project if needed.

        Generates issue_id as "issue-NNN" (zero-padded, sequential).

        *metadata* is an optional dict of arbitrary key/value pairs stored
        alongside the issue manifest (e.g. generation trigger, style, session
        file).  Useful for auditing, re-running, and benchmarking.

        Returns:
            {"project_id", "issue_id", "created"} where *created* indicates
            whether the **project** was newly created.
        """
        project_id = slugify(project_name)
        _validate_id(project_id, "project_id")
        lock = await self._get_lock(project_id)

        async with lock:
            workspace = await self._read_workspace()
            now = self._now()

            project_created = project_id not in workspace.get("projects", [])

            if project_created:
                project_manifest: dict[str, Any] = {
                    "version": 1,
                    "id": project_id,
                    "name": project_name,
                    "created_at": now,
                    "description": "",
                    "issues": [],
                    "characters": [],
                    "styles": [],
                }
                workspace.setdefault("projects", []).append(project_id)
                workspace["updated_at"] = now
                await self._write_project_manifest(project_id, project_manifest)
                await self._write_workspace(workspace)
            else:
                project_manifest = await self._read_project_manifest(project_id)

            # Next sequential issue number
            existing_issues: list[str] = project_manifest.get("issues", [])
            next_num = len(existing_issues) + 1
            issue_id = f"issue-{next_num:03d}"

            issue_manifest: dict[str, Any] = {
                "version": 1,
                "id": issue_id,
                "project_id": project_id,
                "title": title,
                "description": description,
                "created_at": now,
                "assets": {},
            }
            if metadata:
                issue_manifest["metadata"] = metadata
            await self._write_issue_manifest(project_id, issue_id, issue_manifest)

            project_manifest["issues"] = existing_issues + [issue_id]
            await self._write_project_manifest(project_id, project_manifest)

        return {
            "project_id": project_id,
            "issue_id": issue_id,
            "created": project_created,
        }

    async def list_projects(self) -> list[dict[str, Any]]:
        """Return summaries of all projects listed in workspace.json."""
        workspace = await self._read_workspace()
        summaries: list[dict[str, Any]] = []
        for pid in workspace.get("projects", []):
            try:
                manifest = await self._read_project_manifest(pid)
                summaries.append(
                    {
                        "project_id": pid,
                        "name": manifest.get("name", pid),
                        "created_at": manifest.get("created_at", ""),
                        "issue_count": len(manifest.get("issues", [])),
                        "character_count": len(manifest.get("characters", [])),
                        "style_count": len(manifest.get("styles", [])),
                    }
                )
            except FileNotFoundError:
                continue
        return summaries

    async def list_issues(self, project_id: str) -> list[dict[str, Any]]:
        """Return issue summaries for the given project."""
        _validate_id(project_id, "project_id")
        project_manifest = await self._read_project_manifest(project_id)
        summaries: list[dict[str, Any]] = []
        for iid in project_manifest.get("issues", []):
            try:
                manifest = await self._read_issue_manifest(project_id, iid)
                summaries.append(
                    {
                        "issue_id": iid,
                        "project_id": project_id,
                        "title": manifest.get("title", ""),
                        "description": manifest.get("description", ""),
                        "created_at": manifest.get("created_at", ""),
                        "asset_count": len(manifest.get("assets", {})),
                    }
                )
            except FileNotFoundError:
                continue
        return summaries

    async def get_issue(self, project_id: str, issue_id: str) -> dict[str, Any]:
        """Return issue details with asset count breakdown by type."""
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")
        manifest = await self._read_issue_manifest(project_id, issue_id)
        assets: dict[str, Any] = manifest.get("assets", {})

        type_counts: dict[str, int] = {}
        for key in assets:
            atype = key.split(":", 1)[0] if ":" in key else key
            type_counts[atype] = type_counts.get(atype, 0) + 1

        return {
            "issue_id": issue_id,
            "project_id": project_id,
            "title": manifest.get("title", ""),
            "description": manifest.get("description", ""),
            "created_at": manifest.get("created_at", ""),
            "asset_count": len(assets),
            "assets_by_type": type_counts,
        }

    async def update_issue(
        self,
        project_id: str,
        issue_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update mutable fields on an existing issue manifest.

        Only non-``None`` parameters are written.  *metadata* is **merged**
        (not replaced) so callers can add keys without clobbering existing ones.

        Returns the updated manifest dict.
        """
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")
        lock = await self._get_lock(project_id)
        async with lock:
            manifest = await self._read_issue_manifest(project_id, issue_id)
            if title is not None:
                manifest["title"] = title
            if description is not None:
                manifest["description"] = description
            if metadata is not None:
                existing_meta = manifest.get("metadata", {})
                existing_meta.update(metadata)
                manifest["metadata"] = existing_meta
            await self._write_issue_manifest(project_id, issue_id, manifest)
        return manifest

    async def cleanup_issue(self, project_id: str, issue_id: str) -> dict[str, Any]:
        """Delete issue directory tree and remove from project manifest."""
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")
        lock = await self._get_lock(project_id)
        async with lock:
            await self._storage.delete(f"projects/{project_id}/issues/{issue_id}")
            try:
                project_manifest = await self._read_project_manifest(project_id)
                project_manifest["issues"] = [
                    i for i in project_manifest.get("issues", []) if i != issue_id
                ]
                await self._write_project_manifest(project_id, project_manifest)
            except FileNotFoundError:
                pass
        return {"deleted": True, "issue_id": issue_id}

    async def cleanup_project(self, project_id: str) -> dict[str, Any]:
        """Delete entire project directory tree and remove from workspace."""
        _validate_id(project_id, "project_id")
        lock = await self._get_lock(project_id)
        async with lock:
            await self._storage.delete(f"projects/{project_id}")
            workspace = await self._read_workspace()
            workspace["projects"] = [
                p for p in workspace.get("projects", []) if p != project_id
            ]
            workspace["updated_at"] = self._now()
            await self._write_workspace(workspace)
        return {"deleted": True, "project_id": project_id}

    # ------------------------------------------------------------------
    # Characters
    # ------------------------------------------------------------------

    async def store_character(
        self,
        project_id: str,
        issue_id: str,
        name: str,
        style: str,
        *,
        role: str,
        character_type: str,
        bundle: str,
        visual_traits: str,
        team_markers: str,
        distinctive_features: str,
        backstory: str = "",
        motivations: str = "",
        personality: str = "",
        metadata: dict[str, Any] | None = None,
        source_path: str | None = None,
        data: bytes | None = None,
        compute_embedding: bool = False,
    ) -> dict[str, Any]:
        """Store a character design (metadata.json + reference.png).

        Image source priority: source_path → data → no image written.
        Version is auto-incremented per (slugify(name), slugify(style)) within project.
        """
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")
        char_slug = slugify(name)
        _validate_id(char_slug, "name")
        style_slug = slugify(style)
        _validate_id(style_slug, "style")

        # Read source file ONCE before acquiring the lock — no double reads.
        image_bytes: bytes | None = None
        if source_path is not None:
            image_bytes = await asyncio.to_thread(Path(source_path).read_bytes)
        elif data is not None:
            image_bytes = data

        lock = await self._get_lock(project_id)
        async with lock:
            project_manifest = await self._read_project_manifest(project_id)
            now = self._now()

            # Determine next version by scanning existing dirs on storage.
            char_base_dir = f"projects/{project_id}/characters/{char_slug}"
            existing_dirs = await self._storage.list_dir(char_base_dir)
            prefix = f"{style_slug}_v"
            existing_versions = [
                int(d[len(prefix) :])
                for d in existing_dirs
                if d.startswith(prefix) and d[len(prefix) :].isdigit()
            ]
            version = max(existing_versions, default=0) + 1

            version_dir = f"{char_base_dir}/{style_slug}_v{version}"
            image_rel = (
                f"{version_dir}/reference.png" if image_bytes is not None else None
            )
            metadata_rel = f"{version_dir}/metadata.json"

            design = CharacterDesign(
                name=name,
                project_id=project_id,
                style=style,
                version=version,
                created_at=now,
                origin_issue_id=issue_id,
                role=role,
                character_type=character_type,
                bundle=bundle,
                visual_traits=visual_traits,
                team_markers=team_markers,
                distinctive_features=distinctive_features,
                backstory=backstory,
                motivations=motivations,
                personality=personality,
                image_path=image_rel,
                metadata=metadata or {},
            )

            # Write metadata first, then image.
            await self._storage.write_text(
                metadata_rel, json.dumps(design.to_dict(include_image=True), indent=2)
            )
            if image_bytes is not None:
                await self._storage.write_bytes(image_rel, image_bytes)  # type: ignore[arg-type]

            # Optionally compute and persist a multimodal embedding.
            if compute_embedding and self._genai_client is not None:
                emb_text = ". ".join([visual_traits, distinctive_features, personality])
                abs_image: str | None = (
                    await self._storage.abs_path(image_rel)
                    if image_rel is not None
                    else None
                )
                vec = await self._compute_embedding(abs_image, emb_text)
                if vec is not None:
                    meta_dict = json.loads(await self._storage.read_text(metadata_rel))
                    meta_dict["embedding"] = vec
                    meta_dict["embedding_model"] = "gemini-embedding-2-preview"
                    meta_dict["embedding_dimensions"] = self._embedding_dim
                    await self._storage.write_text(
                        metadata_rel, json.dumps(meta_dict, indent=2)
                    )

            # Register char_slug in project manifest (idempotent).
            if char_slug not in project_manifest.get("characters", []):
                project_manifest.setdefault("characters", []).append(char_slug)
                await self._write_project_manifest(project_id, project_manifest)

        uri = ComicURI.for_character(project_id, char_slug, version=version)
        return {
            "name": name,
            "style": style,
            "version": version,
            "storage_path": version_dir,
            "uri": str(uri),
        }

    async def get_character(
        self,
        project_id: str,
        name: str,
        *,
        style: str | None = None,
        version: int | None = None,
        include: str = "metadata",
        format: str = "path",
    ) -> dict[str, Any]:
        """Retrieve a character design.

        Resolution rules:
        - style + version: exact version.
        - style only: latest version of that style.
        - neither: latest version of any style (most recent created_at).
        """
        _validate_id(project_id, "project_id")
        char_slug = slugify(name)
        _validate_id(char_slug, "name")
        char_base_dir = f"projects/{project_id}/characters/{char_slug}"

        if style is not None and version is not None:
            style_slug = slugify(style)
            version_dir = f"{char_base_dir}/{style_slug}_v{version}"

        elif style is not None:
            style_slug = slugify(style)
            existing_dirs = await self._storage.list_dir(char_base_dir)
            prefix = f"{style_slug}_v"
            versions = [
                int(d[len(prefix) :])
                for d in existing_dirs
                if d.startswith(prefix) and d[len(prefix) :].isdigit()
            ]
            if not versions:
                raise FileNotFoundError(
                    f"No versions found for character '{name}' style '{style}' "
                    f"in project '{project_id}'"
                )
            version = max(versions)
            version_dir = f"{char_base_dir}/{style_slug}_v{version}"

        else:
            # Latest of any style — compare created_at from metadata files.
            existing_dirs = await self._storage.list_dir(char_base_dir)
            if not existing_dirs:
                raise FileNotFoundError(
                    f"No versions found for character '{name}' in project '{project_id}'"
                )
            best_dir: str | None = None
            best_created = ""
            for d in existing_dirs:
                try:
                    meta_text = await self._storage.read_text(
                        f"{char_base_dir}/{d}/metadata.json"
                    )
                    created = json.loads(meta_text).get("created_at", "")
                    if created > best_created:
                        best_created = created
                        best_dir = d
                except (FileNotFoundError, json.JSONDecodeError):
                    continue
            if best_dir is None:
                raise FileNotFoundError(
                    f"No valid design found for character '{name}' in project '{project_id}'"
                )
            version_dir = f"{char_base_dir}/{best_dir}"

        # Read and reconstruct CharacterDesign.
        meta_text = await self._storage.read_text(f"{version_dir}/metadata.json")
        design = CharacterDesign.from_dict(json.loads(meta_text))
        result: dict[str, Any] = design.to_dict()
        result["uri"] = str(
            ComicURI.for_character(project_id, char_slug, version=design.version)
        )

        if include == "full":
            image_rel = design.image_path
            if image_rel is None:
                result["image"] = None
            else:
                try:
                    if format == "path":
                        result["image"] = await self._storage.abs_path(image_rel)
                    elif format == "base64":
                        img = await self._storage.read_bytes(image_rel)
                        result["image"] = bytes_to_base64(img)
                    elif format == "data_uri":
                        img = await self._storage.read_bytes(image_rel)
                        result["image"] = bytes_to_data_uri(img, "image/png")
                except FileNotFoundError:
                    result["image"] = None

        return result

    async def list_characters(self, project_id: str) -> list[dict[str, Any]]:
        """List all characters with style/version summaries."""
        _validate_id(project_id, "project_id")
        project_manifest = await self._read_project_manifest(project_id)
        char_slugs: list[str] = project_manifest.get("characters", [])
        result: list[dict[str, Any]] = []

        for char_slug in char_slugs:
            char_base_dir = f"projects/{project_id}/characters/{char_slug}"
            dirs = await self._storage.list_dir(char_base_dir)
            if not dirs:
                continue

            # Group dirs by style slug → list of version ints.
            # Dir format: {style_slug}_v{n}
            styles: dict[str, list[int]] = {}
            for d in dirs:
                idx = d.rfind("_v")
                if idx == -1:
                    continue
                style_part = d[:idx]
                ver_part = d[idx + 2 :]
                if ver_part.isdigit():
                    styles.setdefault(style_part, []).append(int(ver_part))

            # Resolve display name from any available metadata file.
            display_name = char_slug
            for d in reversed(dirs):
                try:
                    meta = json.loads(
                        await self._storage.read_text(
                            f"{char_base_dir}/{d}/metadata.json"
                        )
                    )
                    display_name = meta.get("name", char_slug)
                    break
                except (FileNotFoundError, json.JSONDecodeError):
                    continue

            latest_style_version = (
                max((max(vs) for vs in styles.values()), default=1) if styles else 1
            )
            entry: dict[str, Any] = {
                "name": display_name,
                "char_slug": char_slug,
                "styles": {s: max(vs) for s, vs in styles.items()},
                "total_versions": sum(len(vs) for vs in styles.values()),
                "uri": str(
                    ComicURI.for_character(
                        project_id, char_slug, version=latest_style_version
                    )
                ),
            }
            result.append(entry)

        return result

    async def list_character_versions(
        self, project_id: str, name: str
    ) -> list[dict[str, Any]]:
        """Return all versions across all styles for a given character."""
        _validate_id(project_id, "project_id")
        char_slug = slugify(name)
        _validate_id(char_slug, "name")
        char_base_dir = f"projects/{project_id}/characters/{char_slug}"
        dirs = await self._storage.list_dir(char_base_dir)
        versions: list[dict[str, Any]] = []

        for d in dirs:
            try:
                meta = json.loads(
                    await self._storage.read_text(f"{char_base_dir}/{d}/metadata.json")
                )
                versions.append(meta)
            except (FileNotFoundError, json.JSONDecodeError):
                continue

        return sorted(versions, key=lambda m: (m.get("style", ""), m.get("version", 0)))

    async def update_character_metadata(
        self,
        project_id: str,
        name: str,
        style: str,
        version: int,
        *,
        review_status: str | None = None,
        review_feedback: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Patch review metadata on a specific character version."""
        _validate_id(project_id, "project_id")
        char_slug = slugify(name)
        _validate_id(char_slug, "name")
        style_slug = slugify(style)
        _validate_id(style_slug, "style")
        metadata_rel = (
            f"projects/{project_id}/characters/{char_slug}"
            f"/{style_slug}_v{version}/metadata.json"
        )
        lock = await self._get_lock(project_id)
        async with lock:
            meta = json.loads(await self._storage.read_text(metadata_rel))
            if review_status is not None:
                meta["review_status"] = review_status
            if review_feedback is not None:
                meta["review_feedback"] = review_feedback
            if metadata is not None:
                meta["metadata"] = metadata
            await self._storage.write_text(metadata_rel, json.dumps(meta, indent=2))
        return meta

    async def search_characters(
        self,
        *,
        style: str | None = None,
        metadata_filter: dict[str, Any] | None = None,
        project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for characters across all projects (or a single project).

        Walks ``projects/*/characters/`` directories, reads each character's
        metadata, filters by *style* slug and optional *metadata_filter* fields,
        picks the latest version dir per (character, style), and returns a list
        of matches with URIs, visual traits, metadata, and originating project.
        """
        style_slug = slugify(style) if style is not None else None

        # Determine which projects to scan.
        if project_id is not None:
            project_ids = [project_id]
        else:
            ws = await self._read_workspace()
            project_ids = list(ws.get("projects", []))

        results: list[dict[str, Any]] = []

        for pid in project_ids:
            try:
                manifest = await self._read_project_manifest(pid)
            except FileNotFoundError:
                continue
            char_slugs: list[str] = manifest.get("characters", [])

            for char_slug in char_slugs:
                char_base_dir = f"projects/{pid}/characters/{char_slug}"
                version_dirs = await self._storage.list_dir(char_base_dir)
                if not version_dirs:
                    continue

                # Group by style → pick latest version per style.
                style_latest: dict[str, tuple[int, str]] = {}
                for d in version_dirs:
                    idx = d.rfind("_v")
                    if idx == -1:
                        continue
                    s_part = d[:idx]
                    v_part = d[idx + 2 :]
                    if not v_part.isdigit():
                        continue
                    ver = int(v_part)
                    if s_part not in style_latest or ver > style_latest[s_part][0]:
                        style_latest[s_part] = (ver, d)

                for s_slug, (ver, dirname) in style_latest.items():
                    # Filter by style slug if requested.
                    if style_slug is not None and s_slug != style_slug:
                        continue

                    meta_path = f"{char_base_dir}/{dirname}/metadata.json"
                    try:
                        meta_text = await self._storage.read_text(meta_path)
                        meta = json.loads(meta_text)
                    except (FileNotFoundError, json.JSONDecodeError):
                        continue

                    # Filter by metadata fields if requested.
                    if metadata_filter is not None:
                        char_meta = meta.get("metadata", {})
                        if not all(
                            char_meta.get(k) == v for k, v in metadata_filter.items()
                        ):
                            continue

                    uri = ComicURI.for_character(pid, char_slug, version=ver)
                    results.append(
                        {
                            "name": meta.get("name", char_slug),
                            "char_slug": char_slug,
                            "style": meta.get("style", s_slug),
                            "version": ver,
                            "visual_traits": meta.get("visual_traits", ""),
                            "distinctive_features": meta.get(
                                "distinctive_features", ""
                            ),
                            "metadata": meta.get("metadata", {}),
                            "originating_project": pid,
                            "uri": str(uri),
                        }
                    )

        return results

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    async def store_asset(
        self,
        project_id: str,
        issue_id: str,
        asset_type: str,
        name: str,
        *,
        source_path: str | None = None,
        data: bytes | None = None,
        content: dict[str, Any] | str | None = None,
        metadata: dict[str, Any] | None = None,
        compute_embedding: bool = False,
    ) -> dict[str, Any]:
        """Store a versioned asset under an issue.

        Exactly one of source_path, data, or content must be provided:
        - source_path: read bytes once, store as binary (or text for structured).
        - data: raw bytes already in memory.
        - content: dict or str, serialised to the structured file directly.

        Version is auto-incremented per (asset_type, name) within the issue,
        tracked in issue.json assets dict.
        """
        if asset_type not in ASSET_TYPES:
            raise ValueError(
                f"Invalid asset_type '{asset_type}'. "
                f"Must be one of: {sorted(ASSET_TYPES)}"
            )
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")
        _validate_id(name, "name")

        input_count = sum(x is not None for x in (source_path, data, content))
        if input_count == 0:
            raise ValueError(
                "store_asset requires exactly one of: source_path, data, content"
            )
        if input_count > 1:
            raise ValueError(
                f"store_asset accepts exactly one of: source_path, data, content (got {input_count})"
            )

        # Read source file ONCE before acquiring the lock.
        raw_bytes: bytes | None = None
        if source_path is not None:
            raw_bytes = await asyncio.to_thread(Path(source_path).read_bytes)
        elif data is not None:
            raw_bytes = data

        lock = await self._get_lock(project_id)
        async with lock:
            issue_manifest = await self._read_issue_manifest(project_id, issue_id)
            now = self._now()

            asset_key = f"{asset_type}:{name}"
            existing_entry = issue_manifest.get("assets", {}).get(asset_key, {})
            version = existing_entry.get("latest_version", 0) + 1

            version_dir = self._asset_version_dir(
                project_id, issue_id, asset_type, name, version
            )

            mime_type: str
            size_bytes: int
            storage_path: str

            if asset_type in _STRUCTURED_TYPES:
                # ---- Structured content (JSON or HTML) ----
                filename = _STRUCTURED_FILENAME[asset_type]
                file_rel = f"{version_dir}/{filename}"

                if content is not None:
                    if isinstance(content, dict):
                        text_content = json.dumps(content, indent=2)
                    else:
                        text_content = content
                elif raw_bytes is not None:
                    text_content = raw_bytes.decode("utf-8")
                else:
                    raise ValueError(
                        "store_asset requires source_path, data, or content"
                    )

                mime_type = _STRUCTURED_MIME[asset_type]
                size_bytes = await self._storage.write_text(file_rel, text_content)
                storage_path = file_rel

            else:
                # ---- Binary asset (image) ----
                if raw_bytes is None:
                    raise ValueError(
                        f"Binary asset_type '{asset_type}' requires source_path or data"
                    )
                size_bytes = len(raw_bytes)
                if source_path:
                    mime_type = guess_mime(source_path)
                elif raw_bytes and len(raw_bytes) >= 8:
                    if raw_bytes[:8] == b"\x89PNG\r\n\x1a\n":
                        mime_type = "image/png"
                    elif raw_bytes[:3] == b"\xff\xd8\xff":
                        mime_type = "image/jpeg"
                    elif (
                        raw_bytes[:4] == b"RIFF"
                        and len(raw_bytes) >= 12
                        and raw_bytes[8:12] == b"WEBP"
                    ):
                        mime_type = "image/webp"
                    else:
                        mime_type = "image/png"
                else:
                    mime_type = "image/png"

                # Derive extension from MIME type.
                ext = mime_type.split("/")[-1] if "/" in mime_type else "bin"
                if ext == "jpeg":
                    ext = "jpg"

                image_rel = f"{version_dir}/image.{ext}"
                metadata_rel = f"{version_dir}/metadata.json"
                storage_path = image_rel

                await self._storage.write_bytes(image_rel, raw_bytes)

                asset_obj = Asset(
                    name=name,
                    asset_type=asset_type,
                    project_id=project_id,
                    issue_id=issue_id,
                    version=version,
                    created_at=now,
                    mime_type=mime_type,
                    size_bytes=size_bytes,
                    storage_path=storage_path,
                    metadata=metadata or {},
                )
                await self._storage.write_text(
                    metadata_rel,
                    json.dumps(asset_obj.to_dict(include_payload=True), indent=2),
                )

                # Optionally compute and persist a multimodal embedding.
                if compute_embedding and self._genai_client is not None:
                    emb_text = (metadata or {}).get("prompt") or (metadata or {}).get(
                        "description"
                    )
                    abs_image = await self._storage.abs_path(image_rel)
                    vec = await self._compute_embedding(abs_image, emb_text)
                    if vec is not None:
                        meta_dict = json.loads(
                            await self._storage.read_text(metadata_rel)
                        )
                        meta_dict["embedding"] = vec
                        meta_dict["embedding_model"] = "gemini-embedding-2-preview"
                        meta_dict["embedding_dimensions"] = self._embedding_dim
                        await self._storage.write_text(
                            metadata_rel, json.dumps(meta_dict, indent=2)
                        )

            # Update issue manifest — record latest version for this asset key.
            issue_manifest.setdefault("assets", {})[asset_key] = {
                "latest_version": version
            }
            await self._write_issue_manifest(project_id, issue_id, issue_manifest)

        uri = ComicURI.for_asset(
            project_id, issue_id, asset_type, name, version=version
        )
        return {
            "name": name,
            "asset_type": asset_type,
            "version": version,
            "storage_path": storage_path,
            "size_bytes": size_bytes,
            "uri": str(uri),
        }

    async def get_asset(
        self,
        project_id: str,
        issue_id: str,
        asset_type: str,
        name: str,
        *,
        version: int | None = None,
        include: str = "metadata",
        format: str = "path",
    ) -> dict[str, Any]:
        """Retrieve an asset, optionally with its payload.

        version=None resolves to the latest version tracked in issue.json.
        include='metadata': Asset.to_dict() without payload.
        include='full': adds payload in the requested format.
        """
        if asset_type not in ASSET_TYPES:
            raise ValueError(f"Invalid asset_type '{asset_type}'")
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")
        _validate_id(name, "name")

        if version is None:
            manifest = await self._read_issue_manifest(project_id, issue_id)
            asset_key = f"{asset_type}:{name}"
            entry = manifest.get("assets", {}).get(asset_key)
            if entry is None:
                raise FileNotFoundError(
                    f"Asset '{name}' of type '{asset_type}' not found "
                    f"in issue '{issue_id}'"
                )
            version = entry["latest_version"]

        assert version is not None  # narrowed by the branch above
        resolved_version: int = version
        version_dir = self._asset_version_dir(
            project_id, issue_id, asset_type, name, resolved_version
        )

        if asset_type in _STRUCTURED_TYPES:
            filename = _STRUCTURED_FILENAME[asset_type]
            file_rel = f"{version_dir}/{filename}"
            text = await self._storage.read_text(file_rel)
            mime_type = _STRUCTURED_MIME[asset_type]
            size_bytes = len(text.encode("utf-8"))

            parsed_content: dict[str, Any] | str
            try:
                parsed_content = json.loads(text)
            except json.JSONDecodeError:
                parsed_content = text

            asset_obj = Asset(
                name=name,
                asset_type=asset_type,
                project_id=project_id,
                issue_id=issue_id,
                version=resolved_version,
                created_at="",
                mime_type=mime_type,
                size_bytes=size_bytes,
                storage_path=file_rel,
                content=parsed_content if include == "full" else None,
            )
            result = asset_obj.to_dict(include_payload=(include == "full"))

            # Merge in sidecar metadata.json if it exists (written by update_asset_metadata).
            sidecar_rel = f"{version_dir}/metadata.json"
            try:
                sidecar = json.loads(await self._storage.read_text(sidecar_rel))
                for key in ("review_status", "review_feedback", "metadata"):
                    if key in sidecar:
                        result[key] = sidecar[key]
            except FileNotFoundError:
                pass

            result["uri"] = str(
                ComicURI.for_asset(
                    project_id, issue_id, asset_type, name, version=resolved_version
                )
            )
            return result

        else:
            # Binary asset — read metadata.json written at store time.
            metadata_rel = f"{version_dir}/metadata.json"
            try:
                meta = json.loads(await self._storage.read_text(metadata_rel))
            except FileNotFoundError:
                # Graceful fallback for assets stored without a metadata file.
                meta = {
                    "name": name,
                    "asset_type": asset_type,
                    "project_id": project_id,
                    "issue_id": issue_id,
                    "version": resolved_version,
                    "created_at": "",
                    "mime_type": "image/png",
                    "size_bytes": 0,
                    "storage_path": f"{version_dir}/image.png",
                }

            asset_obj = Asset.from_dict(meta)
            result: dict[str, Any] = asset_obj.to_dict(
                include_payload=(include == "full")
            )

            if include == "full":
                image_rel = asset_obj.storage_path or f"{version_dir}/image.png"
                if format == "path":
                    result["image"] = await self._storage.abs_path(image_rel)
                elif format == "base64":
                    img = await self._storage.read_bytes(image_rel)
                    result["image"] = bytes_to_base64(img)
                elif format == "data_uri":
                    img = await self._storage.read_bytes(image_rel)
                    result["image"] = bytes_to_data_uri(
                        img, asset_obj.mime_type or "image/png"
                    )

            result["uri"] = str(
                ComicURI.for_asset(
                    project_id, issue_id, asset_type, name, version=resolved_version
                )
            )
            return result

    async def list_assets(
        self,
        project_id: str,
        issue_id: str,
        *,
        asset_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """List assets for an issue, optionally filtered by type."""
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")
        manifest = await self._read_issue_manifest(project_id, issue_id)
        assets_map: dict[str, Any] = manifest.get("assets", {})
        result: list[dict[str, Any]] = []

        for key, entry in assets_map.items():
            if ":" in key:
                atype, aname = key.split(":", 1)
            else:
                atype, aname = key, key

            if asset_type is not None and atype != asset_type:
                continue

            latest_ver = entry.get("latest_version", 1)
            uri = ComicURI.for_asset(
                project_id, issue_id, atype, aname, version=latest_ver
            )
            result.append(
                {
                    "name": aname,
                    "asset_type": atype,
                    "latest_version": latest_ver,
                    "uri": str(uri),
                }
            )

        return sorted(result, key=lambda x: (x["asset_type"], x["name"]))

    async def batch_encode(
        self,
        project_id: str,
        issue_id: str,
        asset_type: str,
        *,
        format: str = "data_uri",
    ) -> list[dict[str, Any]]:
        """Encode the latest version of every asset of *asset_type*.

        Uses asyncio.Semaphore(4) to cap concurrent encode operations.
        Returns list sorted by name: [{"name", "version", "encoded"}].
        """
        if asset_type not in ASSET_TYPES:
            raise ValueError(f"Invalid asset_type '{asset_type}'")
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")

        assets = await self.list_assets(project_id, issue_id, asset_type=asset_type)
        semaphore = asyncio.Semaphore(4)

        async def _encode_one(asset_info: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                aname = asset_info["name"]
                ver = asset_info["latest_version"]
                full = await self.get_asset(
                    project_id,
                    issue_id,
                    asset_type,
                    aname,
                    version=ver,
                    include="full",
                    format=format,
                )
                # Binary assets expose "image"; structured expose "content".
                encoded: Any = full.get("image") or full.get("content") or ""
                return {"name": aname, "version": ver, "encoded": encoded}

        results = await asyncio.gather(*[_encode_one(a) for a in assets])
        return sorted(results, key=lambda r: r["name"])

    async def update_asset_metadata(
        self,
        project_id: str,
        issue_id: str,
        asset_type: str,
        name: str,
        version: int,
        *,
        review_status: str | None = None,
        review_feedback: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Patch review metadata on a specific asset version.

        Binary assets update their existing metadata.json in-place.
        Structured assets (research, storyboard, final) store a sibling
        metadata.json alongside their content file so that review_status,
        review_feedback, and custom metadata can be persisted and retrieved.
        """
        if asset_type not in ASSET_TYPES:
            raise ValueError(f"Invalid asset_type '{asset_type}'")
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")
        _validate_id(name, "name")

        if asset_type in _STRUCTURED_TYPES:
            # For structured types, store metadata alongside content
            version_dir = self._asset_version_dir(
                project_id, issue_id, asset_type, name, version
            )
            metadata_rel = f"{version_dir}/metadata.json"
            lock = await self._get_lock(project_id)
            async with lock:
                try:
                    existing = json.loads(await self._storage.read_text(metadata_rel))
                except FileNotFoundError:
                    existing = {
                        "name": name,
                        "asset_type": asset_type,
                        "version": version,
                    }
                if review_status is not None:
                    existing["review_status"] = review_status
                if review_feedback is not None:
                    existing["review_feedback"] = review_feedback
                if metadata is not None:
                    existing.setdefault("metadata", {}).update(metadata)
                await self._storage.write_text(
                    metadata_rel, json.dumps(existing, indent=2)
                )
            return existing

        version_dir = self._asset_version_dir(
            project_id, issue_id, asset_type, name, version
        )
        metadata_rel = f"{version_dir}/metadata.json"

        lock = await self._get_lock(project_id)
        async with lock:
            meta = json.loads(await self._storage.read_text(metadata_rel))
            if review_status is not None:
                meta["review_status"] = review_status
            if review_feedback is not None:
                meta["review_feedback"] = review_feedback
            if metadata is not None:
                meta["metadata"] = metadata
            await self._storage.write_text(metadata_rel, json.dumps(meta, indent=2))

        return meta

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    async def store_style(
        self,
        project_id: str,
        issue_id: str,
        name: str,
        definition: dict[str, Any],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store a style guide definition under the project.

        Version is auto-incremented per slugify(name) within the project.
        """
        _validate_id(project_id, "project_id")
        _validate_id(issue_id, "issue_id")
        style_slug = slugify(name)
        _validate_id(style_slug, "name")
        lock = await self._get_lock(project_id)

        async with lock:
            project_manifest = await self._read_project_manifest(project_id)
            now = self._now()

            # Determine next version by scanning existing style dirs.
            style_base_dir = f"projects/{project_id}/styles"
            existing_dirs = await self._storage.list_dir(style_base_dir)
            prefix = f"{style_slug}_v"
            existing_versions = [
                int(d[len(prefix) :])
                for d in existing_dirs
                if d.startswith(prefix) and d[len(prefix) :].isdigit()
            ]
            version = max(existing_versions, default=0) + 1

            version_dir = f"{style_base_dir}/{style_slug}_v{version}"
            definition_rel = f"{version_dir}/definition.json"

            style_obj = StyleGuide(
                name=name,
                project_id=project_id,
                version=version,
                created_at=now,
                origin_issue_id=issue_id,
                definition=definition,
                metadata=metadata or {},
            )
            await self._storage.write_text(
                definition_rel,
                json.dumps(style_obj.to_dict(include_definition=True), indent=2),
            )

            # Register style_slug in project manifest (idempotent).
            if style_slug not in project_manifest.get("styles", []):
                project_manifest.setdefault("styles", []).append(style_slug)
                await self._write_project_manifest(project_id, project_manifest)

        uri = ComicURI.for_style(project_id, style_slug, version=version)
        return {"name": name, "version": version, "uri": str(uri)}

    async def get_style(
        self,
        project_id: str,
        name: str,
        *,
        version: int | None = None,
        include: str = "metadata",
    ) -> dict[str, Any]:
        """Retrieve a style guide.

        version=None resolves to the latest version of the given style name.
        include='full' adds the definition dict.
        """
        _validate_id(project_id, "project_id")
        style_slug = slugify(name)
        _validate_id(style_slug, "name")
        style_base_dir = f"projects/{project_id}/styles"

        if version is None:
            existing_dirs = await self._storage.list_dir(style_base_dir)
            prefix = f"{style_slug}_v"
            versions = [
                int(d[len(prefix) :])
                for d in existing_dirs
                if d.startswith(prefix) and d[len(prefix) :].isdigit()
            ]
            if not versions:
                raise FileNotFoundError(
                    f"No versions found for style '{name}' in project '{project_id}'"
                )
            version = max(versions)

        definition_rel = f"{style_base_dir}/{style_slug}_v{version}/definition.json"
        data = json.loads(await self._storage.read_text(definition_rel))
        style_obj = StyleGuide.from_dict(data)
        result = style_obj.to_dict(include_definition=(include == "full"))
        result["uri"] = str(
            ComicURI.for_style(project_id, style_slug, version=style_obj.version)
        )
        return result

    async def list_styles(self, project_id: str) -> list[dict[str, Any]]:
        """List all style guides with version summaries."""
        _validate_id(project_id, "project_id")
        project_manifest = await self._read_project_manifest(project_id)
        style_slugs: list[str] = project_manifest.get("styles", [])
        style_base_dir = f"projects/{project_id}/styles"
        existing_dirs = await self._storage.list_dir(style_base_dir)
        result: list[dict[str, Any]] = []

        for style_slug in style_slugs:
            prefix = f"{style_slug}_v"
            versions = [
                int(d[len(prefix) :])
                for d in existing_dirs
                if d.startswith(prefix) and d[len(prefix) :].isdigit()
            ]
            if not versions:
                continue

            latest_version = max(versions)
            definition_rel = (
                f"{style_base_dir}/{style_slug}_v{latest_version}/definition.json"
            )
            try:
                data = json.loads(await self._storage.read_text(definition_rel))
                display_name: str = data.get("name", style_slug)
            except (FileNotFoundError, json.JSONDecodeError):
                display_name = style_slug

            style_entry: dict[str, Any] = {
                "name": display_name,
                "style_slug": style_slug,
                "latest_version": latest_version,
                "total_versions": len(versions),
                "uri": str(
                    ComicURI.for_style(project_id, style_slug, version=latest_version)
                ),
            }
            result.append(style_entry)

        return result
