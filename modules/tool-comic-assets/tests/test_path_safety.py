"""Tests for WP-1: path traversal guard and input identifier validation."""

from __future__ import annotations

import pytest

from amplifier_module_comic_assets.service import ComicProjectService, _validate_id
from amplifier_module_comic_assets.storage import FileSystemStorage, PathTraversalError


# ---------------------------------------------------------------------------
# WP-1A: FileSystemStorage._safe_resolve — path traversal guard
# ---------------------------------------------------------------------------


def test_traversal_dotdot_rejected(tmp_path: pytest.TempPathFactory) -> None:
    """Direct '../etc/passwd' must raise PathTraversalError."""
    storage = FileSystemStorage(str(tmp_path / ".comic-assets"))
    with pytest.raises(PathTraversalError, match="outside storage root"):
        storage._safe_resolve("../etc/passwd")


def test_traversal_absolute_rejected(tmp_path: pytest.TempPathFactory) -> None:
    """Absolute paths must raise PathTraversalError."""
    storage = FileSystemStorage(str(tmp_path / ".comic-assets"))
    with pytest.raises(PathTraversalError, match="Absolute paths not allowed"):
        storage._safe_resolve("/etc/passwd")


def test_traversal_encoded_dotdot_in_middle(tmp_path: pytest.TempPathFactory) -> None:
    """Deep traversal via 'projects/../../../etc/passwd' must be rejected."""
    storage = FileSystemStorage(str(tmp_path / ".comic-assets"))
    with pytest.raises(PathTraversalError, match="outside storage root"):
        storage._safe_resolve("projects/../../../etc/passwd")


def test_normal_paths_work(tmp_path: pytest.TempPathFactory) -> None:
    """A plain nested path must resolve correctly within the root."""
    root = tmp_path / ".comic-assets"
    storage = FileSystemStorage(str(root))
    resolved = storage._safe_resolve("projects/my-project/project.json")
    expected = (root / "projects/my-project/project.json").resolve()
    assert resolved == expected
    assert resolved.is_relative_to(root.resolve())


def test_nested_dotdot_that_stays_inside(tmp_path: pytest.TempPathFactory) -> None:
    """'projects/foo/../bar' resolves to 'projects/bar' — still within root, must pass."""
    root = tmp_path / ".comic-assets"
    storage = FileSystemStorage(str(root))
    resolved = storage._safe_resolve("projects/foo/../bar")
    expected = (root / "projects/bar").resolve()
    assert resolved == expected
    assert resolved.is_relative_to(root.resolve())


# ---------------------------------------------------------------------------
# Async storage methods raise PathTraversalError at call time (not inside thread)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_write_bytes_rejects_traversal(tmp_storage: FileSystemStorage) -> None:
    with pytest.raises(PathTraversalError):
        await tmp_storage.write_bytes("../escape.bin", b"evil")


@pytest.mark.asyncio(loop_scope="function")
async def test_read_bytes_rejects_traversal(tmp_storage: FileSystemStorage) -> None:
    with pytest.raises(PathTraversalError):
        await tmp_storage.read_bytes("../escape.bin")


@pytest.mark.asyncio(loop_scope="function")
async def test_exists_rejects_traversal(tmp_storage: FileSystemStorage) -> None:
    with pytest.raises(PathTraversalError):
        await tmp_storage.exists("../../shadow")


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_rejects_traversal(tmp_storage: FileSystemStorage) -> None:
    with pytest.raises(PathTraversalError):
        await tmp_storage.delete("../important")


@pytest.mark.asyncio(loop_scope="function")
async def test_list_dir_rejects_traversal(tmp_storage: FileSystemStorage) -> None:
    with pytest.raises(PathTraversalError):
        await tmp_storage.list_dir("../other_root")


@pytest.mark.asyncio(loop_scope="function")
async def test_abs_path_rejects_traversal(tmp_storage: FileSystemStorage) -> None:
    with pytest.raises(PathTraversalError):
        await tmp_storage.abs_path("../other")


# ---------------------------------------------------------------------------
# WP-1B: _validate_id — identifier validation
# ---------------------------------------------------------------------------


def test_validate_id_valid_ids_pass() -> None:
    """Well-formed identifiers must pass without raising."""
    assert _validate_id("my-project", "project_id") == "my-project"
    assert _validate_id("issue-001", "issue_id") == "issue-001"
    assert _validate_id("panel_01", "name") == "panel_01"
    assert _validate_id("a", "x") == "a"
    assert _validate_id("0cool", "x") == "0cool"
    assert _validate_id("abc-def_ghi", "x") == "abc-def_ghi"


def test_validate_id_slashes_rejected() -> None:
    """IDs containing '/' must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid project_id"):
        _validate_id("my/project", "project_id")


def test_validate_id_dotdot_rejected() -> None:
    """IDs starting with '..' must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid name"):
        _validate_id("..project", "name")


def test_validate_id_empty_rejected() -> None:
    """Empty string must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid project_id"):
        _validate_id("", "project_id")


def test_validate_id_uppercase_rejected() -> None:
    """IDs with uppercase letters must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid project_id"):
        _validate_id("MyProject", "project_id")


def test_validate_id_leading_hyphen_rejected() -> None:
    """IDs starting with '-' must raise ValueError (must start with [a-z0-9])."""
    with pytest.raises(ValueError, match="Invalid name"):
        _validate_id("-foo", "name")


def test_validate_id_dot_rejected() -> None:
    """IDs containing '.' must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid issue_id"):
        _validate_id("issue.001", "issue_id")


def test_validate_id_space_rejected() -> None:
    """IDs containing spaces must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid project_id"):
        _validate_id("my project", "project_id")


# ---------------------------------------------------------------------------
# WP-1B Integration: service raises ValueError for unsafe identifiers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_service_rejects_unsafe_project_id(
    service: ComicProjectService,
) -> None:
    """store_character with a malicious project_id must raise ValueError immediately."""
    with pytest.raises(ValueError, match="Invalid project_id"):
        await service.store_character(
            "../evil-project",  # malicious project_id
            "issue-001",
            "Hero",
            "manga",
            role="protagonist",
            character_type="main",
            bundle="test-bundle",
            visual_traits="tall",
            team_markers="none",
            distinctive_features="scar",
        )


@pytest.mark.asyncio(loop_scope="function")
async def test_service_rejects_issue_id_with_slash(
    service: ComicProjectService,
) -> None:
    """list_assets with 'issue/bad' as issue_id must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid issue_id"):
        await service.list_assets("my-project", "issue/bad")


@pytest.mark.asyncio(loop_scope="function")
async def test_service_rejects_asset_name_with_dotdot(
    tmp_path: pytest.TempPathFactory,
    service: ComicProjectService,
) -> None:
    """store_asset with '..name' as asset name must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid name"):
        await service.store_asset(
            "my-project",
            "issue-001",
            "panel",
            "..panel",
            data=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
        )


@pytest.mark.asyncio(loop_scope="function")
async def test_service_rejects_uppercase_project_id(
    service: ComicProjectService,
) -> None:
    """list_issues with uppercase project_id must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid project_id"):
        await service.list_issues("MyProject")
