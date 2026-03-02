"""Tests for URI fields in service responses."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio(loop_scope="function")
async def test_store_asset_returns_uri(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    result = await service.store_asset(
        "test-proj", "issue-001", "panel", "panel_01",
        source_path=sample_png,
    )
    assert "uri" in result
    assert result["uri"] == "comic://test-proj/issue-001/panel/panel_01?v=1"


@pytest.mark.asyncio(loop_scope="function")
async def test_list_assets_returns_uris(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_asset("test-proj", "issue-001", "panel", "panel_01", source_path=sample_png)
    result = await service.list_assets("test-proj", "issue-001")
    assert len(result) == 1
    assert "uri" in result[0]
    assert result[0]["uri"].startswith("comic://test-proj/issue-001/panel/panel_01")


@pytest.mark.asyncio(loop_scope="function")
async def test_store_character_returns_uri(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    result = await service.store_character(
        "test-proj", "issue-001", "Explorer", "manga",
        role="hero", character_type="main", bundle="foundation",
        visual_traits="tall", team_markers="badge",
        distinctive_features="scar", source_path=sample_png,
    )
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/issue-001/character/explorer")


@pytest.mark.asyncio(loop_scope="function")
async def test_store_style_returns_uri(service) -> None:
    await service.create_issue("test-proj", "Issue 1")
    result = await service.store_style(
        "test-proj", "issue-001", "manga", {"palette": "vibrant"},
    )
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/issue-001/style/manga")


@pytest.mark.asyncio(loop_scope="function")
async def test_get_asset_returns_uri(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_asset("test-proj", "issue-001", "panel", "panel_01", source_path=sample_png)
    result = await service.get_asset("test-proj", "issue-001", "panel", "panel_01")
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/issue-001/panel/panel_01")


@pytest.mark.asyncio(loop_scope="function")
async def test_get_character_returns_uri(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_character(
        "test-proj", "issue-001", "Explorer", "manga",
        role="hero", character_type="main", bundle="foundation",
        visual_traits="tall", team_markers="badge",
        distinctive_features="scar", source_path=sample_png,
    )
    result = await service.get_character("test-proj", "Explorer")
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/issue-001/character/explorer")


@pytest.mark.asyncio(loop_scope="function")
async def test_list_characters_returns_uris(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_character(
        "test-proj", "issue-001", "Explorer", "manga",
        role="hero", character_type="main", bundle="foundation",
        visual_traits="tall", team_markers="badge",
        distinctive_features="scar", source_path=sample_png,
    )
    result = await service.list_characters("test-proj")
    assert len(result) == 1
    assert "uri" in result[0]
    assert "explorer" in result[0]["uri"]


@pytest.mark.asyncio(loop_scope="function")
async def test_get_style_returns_uri(service) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_style("test-proj", "issue-001", "manga", {"palette": "vibrant"})
    result = await service.get_style("test-proj", "manga")
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/issue-001/style/manga")


@pytest.mark.asyncio(loop_scope="function")
async def test_list_styles_returns_uris(service) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_style("test-proj", "issue-001", "manga", {"palette": "vibrant"})
    result = await service.list_styles("test-proj")
    assert len(result) == 1
    assert "uri" in result[0]
    assert "manga" in result[0]["uri"]
