"""comic:// URI protocol — universal asset identifier (v2: scope-aware).

Project-scoped format (characters, styles):
    comic://project/collection/name[?v=N]

Issue-scoped format (panels, covers, storyboards, etc.):
    comic://project/issues/issue-name/collection/name[?v=N]

When version is absent, resolution defaults to latest.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

# -- Scope-aware type constants -----------------------------------------------

PROJECT_SCOPED_TYPES = frozenset({"characters", "styles"})

ISSUE_SCOPED_TYPES = frozenset(
    {
        "panels",
        "covers",
        "storyboards",
        "research",
        "finals",
        "avatars",
        "qa_screenshots",
    }
)

# Union of all valid URI collection names (plural forms).
COMIC_URI_TYPES = PROJECT_SCOPED_TYPES | ISSUE_SCOPED_TYPES

# Mapping from v1 singular types (used in service layer) to v2 plural URI types.
_SINGULAR_TO_PLURAL: dict[str, str] = {
    "character": "characters",
    "style": "styles",
    "panel": "panels",
    "cover": "covers",
    "storyboard": "storyboards",
    "research": "research",
    "final": "finals",
    "avatar": "avatars",
    "qa_screenshot": "qa_screenshots",
}

_PLURAL_TO_SINGULAR: dict[str, str] = {v: k for k, v in _SINGULAR_TO_PLURAL.items()}


def pluralize_type(singular: str) -> str:
    """Convert a v1 singular asset type to v2 plural collection name.

    Unknown types are returned unchanged (pass-through).
    """
    return _SINGULAR_TO_PLURAL.get(singular, singular)


def singularize_type(plural: str) -> str:
    """Convert a v2 plural collection name to v1 singular asset type.

    Unknown types are returned unchanged (pass-through).
    """
    return _PLURAL_TO_SINGULAR.get(plural, plural)


class InvalidComicURI(ValueError):
    """Raised when a string cannot be parsed as a valid comic:// URI."""


@dataclass(frozen=True, slots=True)
class ComicURI:
    """Parsed comic:// URI (v2: scope-aware).

    Attributes:
        project: Project identifier (slugified).
        asset_type: Pluralized collection name (``"characters"``, ``"panels"``, etc.).
        name: Asset name within the collection.
        issue: Issue identifier, or ``None`` for project-scoped resources.
        version: Explicit version, or ``None`` for latest.
    """

    project: str
    asset_type: str
    name: str
    issue: str | None = None
    version: int | None = None

    @property
    def is_project_scoped(self) -> bool:
        """True for project-level resources (characters, styles)."""
        return self.issue is None

    @property
    def is_issue_scoped(self) -> bool:
        """True for issue-level resources (panels, covers, etc.)."""
        return self.issue is not None

    @property
    def is_latest(self) -> bool:
        """True when no explicit version is pinned."""
        return self.version is None

    def __str__(self) -> str:
        if self.issue is None:
            base = f"comic://{self.project}/{self.asset_type}/{self.name}"
        else:
            base = f"comic://{self.project}/issues/{self.issue}/{self.asset_type}/{self.name}"
        if self.version is not None:
            return f"{base}?v={self.version}"
        return base

    def __repr__(self) -> str:
        return f"ComicURI('{self}')"

    @classmethod
    def for_asset(
        cls,
        project: str,
        issue: str,
        asset_type: str,
        name: str,
        version: int | None = None,
    ) -> "ComicURI":
        """Build a URI for an issue-scoped asset.

        ``asset_type`` accepts both singular (``"panel"``) and plural
        (``"panels"``) — it is normalized to plural internally.
        """
        plural = pluralize_type(asset_type)
        return cls(
            project=project, issue=issue, asset_type=plural, name=name, version=version
        )

    @classmethod
    def for_character(
        cls, project: str, name: str, *, version: int | None = None
    ) -> "ComicURI":
        """Build a project-scoped character URI. No issue segment."""
        return cls(project=project, asset_type="characters", name=name, version=version)

    @classmethod
    def for_style(
        cls, project: str, name: str, *, version: int | None = None
    ) -> "ComicURI":
        """Build a project-scoped style URI. No issue segment."""
        return cls(project=project, asset_type="styles", name=name, version=version)


def parse_comic_uri(raw: str) -> ComicURI:
    """Parse a comic:// URI string into a :class:`ComicURI`.

    Handles two formats:

    - **Project-scoped**: ``comic://project/collection/name[?v=N]``
      (2 path segments)
    - **Issue-scoped**: ``comic://project/issues/issue/collection/name[?v=N]``
      (4 path segments)

    Raises:
        InvalidComicURI: On any malformed input.
    """
    parsed = urlparse(raw)

    if parsed.scheme != "comic":
        raise InvalidComicURI(
            f"Invalid scheme '{parsed.scheme}' — expected 'comic' in: {raw}"
        )

    project = parsed.netloc
    if not project:
        raise InvalidComicURI(f"Missing project in URI: {raw}")

    # Split path into segments, dropping the leading empty string before "/".
    segments = parsed.path.split("/")[1:]

    # Parse version from query string.
    version: int | None = None
    if parsed.query:
        qs = parse_qs(parsed.query)
        v_values = qs.get("v")
        if v_values:
            try:
                version = int(v_values[0])
            except (ValueError, IndexError):
                raise InvalidComicURI(
                    f"Invalid version parameter — expected integer in: {raw}"
                )

    # Route 1: Project-scoped — comic://project/collection/name
    if len(segments) == 2 and segments[0] in PROJECT_SCOPED_TYPES:
        asset_type, name = segments
        if not name:
            raise InvalidComicURI(f"URI has empty name segment in: {raw}")
        return ComicURI(
            project=project, asset_type=asset_type, name=name, version=version
        )

    # Route 2: Issue-scoped — comic://project/issues/issue/collection/name
    if len(segments) == 4 and segments[0] == "issues":
        _, issue, asset_type, name = segments
        if not issue:
            raise InvalidComicURI(f"URI has empty issue segment in: {raw}")
        if not name:
            raise InvalidComicURI(f"URI has empty name segment in: {raw}")
        if asset_type not in ISSUE_SCOPED_TYPES:
            raise InvalidComicURI(
                f"Unknown issue-scoped type: '{asset_type}'. "
                f"Valid: {sorted(ISSUE_SCOPED_TYPES)}"
            )
        return ComicURI(
            project=project,
            issue=issue,
            asset_type=asset_type,
            name=name,
            version=version,
        )

    raise InvalidComicURI(f"Cannot parse URI: '{raw}'")
