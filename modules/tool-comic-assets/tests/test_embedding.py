"""Tests for cosine_similarity utility in amplifier_module_comic_assets.service."""

from __future__ import annotations

import math

import pytest

from amplifier_module_comic_assets import _strip_embedding
from amplifier_module_comic_assets.service import ComicProjectService, cosine_similarity

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

# Minimal keyword args for store_character
_CHAR_META = dict(
    role="protagonist",
    character_type="main",
    bundle="comic-strips",
    visual_traits="tall, blue eyes",
    team_markers="hero badge",
    distinctive_features="scar on left cheek",
)


async def _new_issue(
    service: ComicProjectService, project: str = "test_project", title: str = "Issue 1"
):
    """Create a project + issue, return (project_id, issue_id)."""
    r = await service.create_issue(project, title)
    return r["project_id"], r["issue_id"]


# ===========================================================================
# cosine_similarity
# ===========================================================================


class TestCosineSimilarity:
    def test_identical_vectors_return_one(self) -> None:
        vec = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec, vec)
        assert result == pytest.approx(1.0)

    def test_orthogonal_vectors_return_zero(self) -> None:
        result = cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert result == pytest.approx(0.0)

    def test_opposite_vectors_return_negative_one(self) -> None:
        result = cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert result == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self) -> None:
        result = cosine_similarity([0.0, 0.0], [1.0, 2.0])
        assert result == pytest.approx(0.0)

    def test_both_zero_vectors_return_zero(self) -> None:
        result = cosine_similarity([0.0, 0.0], [0.0, 0.0])
        assert result == pytest.approx(0.0)

    def test_known_similarity_value(self) -> None:
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        expected = 32.0 / (math.sqrt(14) * math.sqrt(77))
        result = cosine_similarity(a, b)
        assert result == pytest.approx(expected)


# ===========================================================================
# _strip_embedding
# ===========================================================================


class TestStripEmbedding:
    def test_removes_embedding_key(self) -> None:
        metadata = {
            "name": "hero",
            "embedding": [0.1, 0.2, 0.3],
            "embedding_model": "text-embedding-3-small",
            "embedding_dimensions": 3,
        }
        result = _strip_embedding(metadata)
        assert "embedding" not in result

    def test_keeps_embedding_model_and_dimensions(self) -> None:
        metadata = {
            "embedding": [0.1, 0.2, 0.3],
            "embedding_model": "text-embedding-3-small",
            "embedding_dimensions": 3,
        }
        result = _strip_embedding(metadata)
        assert result["embedding_model"] == "text-embedding-3-small"
        assert result["embedding_dimensions"] == 3

    def test_passes_through_metadata_without_embedding(self) -> None:
        metadata = {"name": "hero", "style": "manga", "role": "protagonist"}
        result = _strip_embedding(metadata)
        assert result == metadata

    def test_does_not_mutate_original(self) -> None:
        metadata = {
            "name": "hero",
            "embedding": [0.1, 0.2, 0.3],
            "embedding_model": "text-embedding-3-small",
        }
        original_keys = set(metadata.keys())
        _strip_embedding(metadata)
        assert set(metadata.keys()) == original_keys
        assert "embedding" in metadata
