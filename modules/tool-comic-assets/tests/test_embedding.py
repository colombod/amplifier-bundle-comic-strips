"""Tests for cosine_similarity utility in amplifier_module_comic_assets.service."""

from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock

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


# ===========================================================================
# TestSetEmbeddingClient
# ===========================================================================


class TestSetEmbeddingClient:
    def test_initially_no_client(self, service: ComicProjectService) -> None:
        assert service._genai_client is None
        assert service._embedding_dim == 1536

    def test_set_client_stores_client(self, service: ComicProjectService) -> None:
        mock_client = MagicMock()
        service.set_embedding_client(mock_client)
        assert service._genai_client is mock_client
        assert service._embedding_dim == 1536  # default preserved when dim omitted

    def test_set_client_with_custom_dim(self, service: ComicProjectService) -> None:
        mock_client = MagicMock()
        service.set_embedding_client(mock_client, embedding_dim=768)
        assert service._embedding_dim == 768

    def test_set_client_none_resets(self, service: ComicProjectService) -> None:
        mock_client = MagicMock()
        service.set_embedding_client(mock_client, embedding_dim=768)
        service.set_embedding_client(None)
        assert service._genai_client is None
        assert service._embedding_dim == 1536  # default restored


# ===========================================================================
# _make_embedding_client helper
# ===========================================================================


def _make_embedding_client(dim: int = 4) -> MagicMock:
    """Create a mock genai client that returns a dim-dimensional embedding."""
    embedding_values = [0.1 * (i + 1) for i in range(dim)]
    mock_embedding = MagicMock()
    mock_embedding.values = embedding_values
    mock_result = MagicMock()
    mock_result.embeddings = [mock_embedding]

    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.embed_content = AsyncMock(return_value=mock_result)
    return client


# ===========================================================================
# TestComputeEmbedding
# ===========================================================================


class TestComputeEmbedding:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_none_when_no_client(
        self, service: ComicProjectService
    ) -> None:
        """Returns None when no genai client is set."""
        assert service._genai_client is None
        result = await service._compute_embedding(None, "test text")
        assert result is None

    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_none_when_no_parts(
        self, service: ComicProjectService
    ) -> None:
        """Returns None when neither image_path nor text is provided."""
        client = _make_embedding_client()
        service.set_embedding_client(client, embedding_dim=4)
        result = await service._compute_embedding(None, None)
        assert result is None

    @pytest.mark.asyncio(loop_scope="function")
    async def test_text_only_embedding(self, service: ComicProjectService) -> None:
        """Returns a float list embedding for text-only input."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)
        result = await service._compute_embedding(None, "hello world")
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 4
        assert result == pytest.approx([0.1 * (i + 1) for i in range(4)])

    @pytest.mark.asyncio(loop_scope="function")
    async def test_image_only_embedding(
        self, service: ComicProjectService, sample_png: str
    ) -> None:
        """Returns embedding for image-only input using sample_png fixture."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)
        result = await service._compute_embedding(sample_png, None)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 4

    @pytest.mark.asyncio(loop_scope="function")
    async def test_interleaved_image_and_text(
        self, service: ComicProjectService, sample_png: str
    ) -> None:
        """Verifies that 2 content parts are sent when both image and text provided."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)
        result = await service._compute_embedding(sample_png, "caption text")
        assert result is not None
        # Verify embed_content was called with exactly 2 parts
        call_kwargs = client.aio.models.embed_content.call_args
        contents = call_kwargs.kwargs.get("contents") or call_kwargs.args[1]
        assert len(contents) == 2

    @pytest.mark.asyncio(loop_scope="function")
    async def test_api_error_returns_none(self, service: ComicProjectService) -> None:
        """Returns None when the API raises an exception (caught and logged)."""
        client = MagicMock()
        client.aio = MagicMock()
        client.aio.models = MagicMock()
        client.aio.models.embed_content = AsyncMock(
            side_effect=RuntimeError("API error")
        )
        service.set_embedding_client(client, embedding_dim=4)
        result = await service._compute_embedding(None, "hello")
        assert result is None
