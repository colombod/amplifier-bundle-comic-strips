"""Concurrency tests for ComicProjectService.

Verifies that per-project locking prevents version collisions when multiple
coroutines write to the same project simultaneously.
"""

from __future__ import annotations

import asyncio

import pytest

from amplifier_module_comic_assets.service import ComicProjectService

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

_CHAR_META = dict(
    role="protagonist",
    character_type="main",
    bundle="comic-strips",
    visual_traits="tall, blue eyes",
    team_markers="hero badge",
    distinctive_features="scar",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _new_issue(service: ComicProjectService, project: str, title: str = "I1"):
    r = await service.create_issue(project, title)
    return r["project_id"], r["issue_id"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_concurrent_character_stores(service: ComicProjectService) -> None:
    """Storing two *different* characters simultaneously should work without errors."""
    pid, iid = await _new_issue(service, "concurrent_chars_proj")

    r1, r2 = await asyncio.gather(
        service.store_character(pid, iid, "Alpha", "manga", data=_PNG, **_CHAR_META),
        service.store_character(pid, iid, "Beta", "manga", data=_PNG, **_CHAR_META),
    )

    assert r1["version"] == 1
    assert r2["version"] == 1
    # Both slugs should be registered in the project
    chars = await service.list_characters(pid)
    slugs = {c["char_slug"] for c in chars}
    assert "alpha" in slugs
    assert "beta" in slugs


@pytest.mark.asyncio(loop_scope="function")
async def test_concurrent_asset_stores_same_name(service: ComicProjectService) -> None:
    """Storing the same (name, type) asset simultaneously must assign distinct versions."""
    pid, iid = await _new_issue(service, "concurrent_assets_proj")

    r1, r2 = await asyncio.gather(
        service.store_asset(pid, iid, "panel", "panel_01", data=_PNG),
        service.store_asset(pid, iid, "panel", "panel_01", data=_PNG),
    )

    versions = {r1["version"], r2["version"]}
    # Must have gotten version 1 and version 2, not both 1
    assert versions == {1, 2}


@pytest.mark.asyncio(loop_scope="function")
async def test_batch_encode_respects_semaphore(service: ComicProjectService) -> None:
    """batch_encode with 8 panels must encode all of them (semaphore should not block)."""
    pid, iid = await _new_issue(service, "batch_semaphore_proj")

    # Store 8 panels
    for i in range(1, 9):
        await service.store_asset(pid, iid, "panel", f"panel_{i:02d}", data=_PNG)

    results = await service.batch_encode(pid, iid, "panel", format="base64")

    assert len(results) == 8
    # All must have been encoded (non-empty encoded field)
    for r in results:
        assert r["encoded"] != ""
    # Results must be sorted by name
    names = [r["name"] for r in results]
    assert names == sorted(names)
