"""comic:// URI protocol — universal asset identifier.

Format: comic://project/issue/type/name[?v=N]
When version is absent, resolution defaults to latest.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

# All valid asset types in the URI namespace.
COMIC_URI_TYPES = frozenset(
    {
        "panel",
        "cover",
        "avatar",
        "character",
        "storyboard",
        "style",
        "research",
        "final",
        "qa_screenshot",
    }
)


class InvalidComicURI(ValueError):
    """Raised when a string cannot be parsed as a valid comic:// URI."""


@dataclass(frozen=True, slots=True)
class ComicURI:
    """Parsed comic:// URI.

    Attributes:
        project: Project identifier (slugified).
        issue: Issue identifier (e.g. "issue-001").
        asset_type: One of COMIC_URI_TYPES.
        name: Asset name within the type namespace.
        version: Explicit version, or None for latest.
    """

    project: str
    issue: str
    asset_type: str
    name: str
    version: int | None = None

    @property
    def is_latest(self) -> bool:
        """True when no explicit version is pinned."""
        return self.version is None

    def __str__(self) -> str:
        base = f"comic://{self.project}/{self.issue}/{self.asset_type}/{self.name}"
        if self.version is not None:
            return f"{base}?v={self.version}"
        return base

    @classmethod
    def for_asset(
        cls,
        project: str,
        issue: str,
        asset_type: str,
        name: str,
        version: int | None = None,
    ) -> ComicURI:
        """Build a URI for an issue-scoped asset."""
        return cls(project=project, issue=issue, asset_type=asset_type, name=name, version=version)

    @classmethod
    def for_character(
        cls, project: str, issue: str, name: str, version: int | None = None
    ) -> ComicURI:
        """Build a URI for a character asset."""
        return cls(project=project, issue=issue, asset_type="character", name=name, version=version)

    @classmethod
    def for_style(
        cls, project: str, issue: str, name: str, version: int | None = None
    ) -> ComicURI:
        """Build a URI for a style guide asset."""
        return cls(project=project, issue=issue, asset_type="style", name=name, version=version)


def parse_comic_uri(raw: str) -> ComicURI:
    """Parse a ``comic://project/issue/type/name[?v=N]`` string.

    Raises:
        InvalidComicURI: On any malformed input.
    """
    parsed = urlparse(raw)

    if parsed.scheme != "comic":
        raise InvalidComicURI(
            f"Invalid scheme '{parsed.scheme}' — expected 'comic' in: {raw}"
        )

    # urlparse puts everything after comic:// into netloc + path.
    # comic://project/issue/type/name → netloc="project", path="/issue/type/name"
    # We keep empty segments intact so that comic://proj//panel/name triggers the
    # "empty segment" error rather than a segment-count mismatch.
    path_parts = parsed.path.split("/")[1:]  # drop the leading empty string before "/"
    parts = [parsed.netloc] + path_parts

    if len(parts) != 4:
        raise InvalidComicURI(
            f"Invalid format — expected comic://project/issue/type/name, "
            f"got {len(parts)} segments in: {raw}"
        )

    project, issue, asset_type, name = parts

    for segment_name, segment_value in [
        ("project", project),
        ("issue", issue),
        ("asset_type", asset_type),
        ("name", name),
    ]:
        if not segment_value:
            raise InvalidComicURI(f"URI has empty {segment_name} segment in: {raw}")

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

    return ComicURI(
        project=project,
        issue=issue,
        asset_type=asset_type,
        name=name,
        version=version,
    )
