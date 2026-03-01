"""Domain model dataclasses for comic project asset management."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# -- Constants ----------------------------------------------------------------

ASSET_TYPES = frozenset(
    {
        "research",  # story-researcher output (structured JSON)
        "storyboard",  # storyboard-writer output (structured JSON)
        "panel",  # panel-artist output (image + metadata)
        "cover",  # cover-artist output (image + metadata)
        "avatar",  # branding asset (image)
        "qa_screenshot",  # visual review screenshots
        "final",  # assembled HTML comic
    }
)

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")


def slugify(name: str) -> str:
    """Sanitise a display name for use in filesystem paths.

    Lowercase, replace whitespace with underscores, strip anything
    that is not ``[a-z0-9_-]``, collapse runs, and fall back to
    ``"unnamed"`` when nothing is left.
    """
    result = name.lower().replace(" ", "_")
    result = _SLUG_RE.sub("_", result).strip("_")
    # Collapse repeated underscores / hyphens
    result = re.sub(r"[_-]{2,}", "_", result)
    return result or "unnamed"


# -- Domain objects -----------------------------------------------------------


@dataclass
class Project:
    """Top-level container grouping related comics."""

    id: str  # Slugified: "ampliverse-origins"
    name: str  # Display: "AmpliVerse Origins"
    created_at: str  # ISO 8601
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        return cls(
            id=data["id"],
            name=data["name"],
            created_at=data["created_at"],
            description=data.get("description", ""),
        )


@dataclass
class Issue:
    """Individual comic strip creation run within a project."""

    id: str  # "issue-001"
    project_id: str
    title: str
    created_at: str  # ISO 8601
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "created_at": self.created_at,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Issue:
        return cls(
            id=data["id"],
            project_id=data["project_id"],
            title=data["title"],
            created_at=data["created_at"],
            description=data.get("description", ""),
        )


@dataclass
class CharacterDesign:
    """Composite character design — metadata + optional reference image."""

    name: str  # Display name: "The Explorer"
    project_id: str
    style: str  # Freeform: "manga", "cyberpunk", ...
    version: int  # Auto-incremented per (name, style)
    created_at: str  # ISO 8601
    origin_issue_id: str

    # Design metadata (always returned)
    role: str  # "protagonist", "antagonist", "supporting"
    character_type: str  # "main" or "supporting"
    bundle: str  # "foundation", "comic-strips", etc.
    visual_traits: str
    team_markers: str
    distinctive_features: str
    backstory: str = ""
    motivations: str = ""
    personality: str = ""

    # Binary payload path (only populated when include='full')
    image_path: str | None = None  # Relative path within managed storage

    # Review metadata
    review_status: str = ""  # "accepted", "rejected", ""
    review_feedback: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_image: bool = False) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "project_id": self.project_id,
            "style": self.style,
            "version": self.version,
            "created_at": self.created_at,
            "origin_issue_id": self.origin_issue_id,
            "role": self.role,
            "character_type": self.character_type,
            "bundle": self.bundle,
            "visual_traits": self.visual_traits,
            "team_markers": self.team_markers,
            "distinctive_features": self.distinctive_features,
            "backstory": self.backstory,
            "motivations": self.motivations,
            "personality": self.personality,
            "review_status": self.review_status,
            "review_feedback": self.review_feedback,
            "metadata": self.metadata,
        }
        if include_image:
            d["image_path"] = self.image_path
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CharacterDesign:
        return cls(
            name=data["name"],
            project_id=data["project_id"],
            style=data["style"],
            version=data["version"],
            created_at=data["created_at"],
            origin_issue_id=data["origin_issue_id"],
            role=data["role"],
            character_type=data["character_type"],
            bundle=data["bundle"],
            visual_traits=data["visual_traits"],
            team_markers=data["team_markers"],
            distinctive_features=data["distinctive_features"],
            backstory=data.get("backstory", ""),
            motivations=data.get("motivations", ""),
            personality=data.get("personality", ""),
            image_path=data.get("image_path"),
            review_status=data.get("review_status", ""),
            review_feedback=data.get("review_feedback", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class StyleGuide:
    """Full style guide definition — reusable across issues and projects."""

    name: str  # "manga", "custom-noir", etc. (freeform)
    project_id: str
    version: int  # Auto-incremented per (name,) within project
    created_at: str  # ISO 8601
    origin_issue_id: str

    # Complete style definition as structured data
    definition: dict[str, Any] = field(default_factory=dict)

    # Review metadata
    review_status: str = ""
    review_feedback: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_definition: bool = False) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "project_id": self.project_id,
            "version": self.version,
            "created_at": self.created_at,
            "origin_issue_id": self.origin_issue_id,
            "review_status": self.review_status,
            "review_feedback": self.review_feedback,
            "metadata": self.metadata,
        }
        if include_definition:
            d["definition"] = self.definition
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StyleGuide:
        return cls(
            name=data["name"],
            project_id=data["project_id"],
            version=data["version"],
            created_at=data["created_at"],
            origin_issue_id=data["origin_issue_id"],
            definition=data.get("definition", {}),
            review_status=data.get("review_status", ""),
            review_feedback=data.get("review_feedback", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Asset:
    """Issue-scoped artifact with versioning and review metadata."""

    name: str  # "panel_01", "cover", "research"
    asset_type: str  # One of ASSET_TYPES
    project_id: str
    issue_id: str
    version: int  # Auto-incremented per (name, asset_type) within issue
    created_at: str  # ISO 8601
    mime_type: str  # "image/png", "application/json", "text/html"
    size_bytes: int

    # Storage path (relative, for binary assets)
    storage_path: str | None = None

    # Structured content (for JSON assets like research, storyboard)
    content: dict[str, Any] | str | None = None

    # Review metadata
    review_status: str = ""
    review_feedback: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_payload: bool = False) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "asset_type": self.asset_type,
            "project_id": self.project_id,
            "issue_id": self.issue_id,
            "version": self.version,
            "created_at": self.created_at,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "review_status": self.review_status,
            "review_feedback": self.review_feedback,
            "metadata": self.metadata,
        }
        if include_payload:
            d["storage_path"] = self.storage_path
            d["content"] = self.content
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Asset:
        return cls(
            name=data["name"],
            asset_type=data["asset_type"],
            project_id=data["project_id"],
            issue_id=data["issue_id"],
            version=data["version"],
            created_at=data["created_at"],
            mime_type=data["mime_type"],
            size_bytes=data["size_bytes"],
            storage_path=data.get("storage_path"),
            content=data.get("content"),
            review_status=data.get("review_status", ""),
            review_feedback=data.get("review_feedback", ""),
            metadata=data.get("metadata", {}),
        )
