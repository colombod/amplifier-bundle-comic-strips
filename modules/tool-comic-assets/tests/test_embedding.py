"""Tests for cosine_similarity utility in amplifier_module_comic_assets.service."""

from __future__ import annotations

import base64
import json
import math
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amplifier_module_comic_assets import (
    ComicAssetTool,
    ComicCharacterTool,
    ComicStyleTool,
    _strip_embedding,
)
from amplifier_module_comic_assets.service import (
    ComicProjectService,
    EmbeddingCircuitBreaker,
    cosine_similarity,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

# Minimal keyword args for store_character
_CHAR_META: dict[str, Any] = dict(
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
        contents = call_kwargs.kwargs["contents"]
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


# ===========================================================================
# TestStoreCharacterEmbedding
# ===========================================================================


class TestStoreCharacterEmbedding:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_without_embedding_has_no_embedding_fields(
        self, service: ComicProjectService
    ) -> None:
        """compute_embedding=False: metadata.json has no embedding fields."""
        pid, iid = await _new_issue(service)
        await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            compute_embedding=False,
        )
        char_slug = "hero"
        meta_text = await service._storage.read_text(
            f"projects/{pid}/characters/{char_slug}/manga_v1/metadata.json"
        )
        meta = json.loads(meta_text)
        assert "embedding" not in meta
        assert "embedding_model" not in meta
        assert "embedding_dimensions" not in meta

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_with_embedding_writes_vector(
        self, service: ComicProjectService
    ) -> None:
        """compute_embedding=True with client: embedding vector written to metadata.json."""
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 4
        mock_result = MagicMock()
        mock_result.embeddings = [mock_embedding]
        client = MagicMock()
        client.aio = MagicMock()
        client.aio.models = MagicMock()
        client.aio.models.embed_content = AsyncMock(return_value=mock_result)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            compute_embedding=True,
        )
        char_slug = "hero"
        meta_text = await service._storage.read_text(
            f"projects/{pid}/characters/{char_slug}/manga_v1/metadata.json"
        )
        meta = json.loads(meta_text)
        assert meta["embedding"] == pytest.approx([0.1] * 4)
        assert meta["embedding_model"] == "gemini-embedding-2-preview"
        assert meta["embedding_dimensions"] == 4

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_with_embedding_noop_when_no_client(
        self, service: ComicProjectService
    ) -> None:
        """compute_embedding=True but no client: store still succeeds, no embedding."""
        assert service._genai_client is None
        pid, iid = await _new_issue(service)
        result = await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            compute_embedding=True,
        )
        assert "uri" in result  # store succeeded
        char_slug = "hero"
        meta_text = await service._storage.read_text(
            f"projects/{pid}/characters/{char_slug}/manga_v1/metadata.json"
        )
        meta = json.loads(meta_text)
        assert "embedding" not in meta

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_with_embedding_uses_correct_text(
        self, service: ComicProjectService
    ) -> None:
        """Verify embed text includes visual_traits, distinctive_features, personality."""
        captured_args: list[tuple[str | None, str | None]] = []

        async def mock_compute(image_path: str | None, text: str | None) -> list[float]:
            captured_args.append((image_path, text))
            return [0.1] * 4

        # Give the service a non-None client so the compute_embedding branch fires.
        service._genai_client = MagicMock()

        pid, iid = await _new_issue(service)
        char_meta: dict[str, Any] = dict(
            role="protagonist",
            character_type="main",
            bundle="comic-strips",
            visual_traits="tall blue eyes",
            team_markers="hero badge",
            distinctive_features="scar on left cheek",
            personality="brave and bold",
        )
        with patch.object(service, "_compute_embedding", side_effect=mock_compute):
            await service.store_character(
                pid,
                iid,
                "Hero",
                "manga",
                **char_meta,
                data=_PNG,
                compute_embedding=True,
            )

        assert captured_args, "Expected _compute_embedding to be called"
        _, text = captured_args[0]
        assert text is not None
        assert "tall blue eyes" in text
        assert "scar on left cheek" in text
        assert "brave and bold" in text


# ===========================================================================
# TestStoreAssetEmbedding
# ===========================================================================


class TestStoreAssetEmbedding:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_panel_with_embedding(
        self, service: ComicProjectService
    ) -> None:
        """compute_embedding=True with client: embedding written to panel metadata.json."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall", "description": "Scene 1"},
            compute_embedding=True,
        )

        # Find and read the metadata.json for the panel
        version_dir = f"projects/{pid}/issues/{iid}/panels/panel01_v1"
        meta_text = await service._storage.read_text(f"{version_dir}/metadata.json")
        meta = json.loads(meta_text)
        assert "embedding" in meta
        assert meta["embedding"] == pytest.approx([0.1 * (i + 1) for i in range(4)])
        assert meta["embedding_model"] == "gemini-embedding-2-preview"
        assert meta["embedding_dimensions"] == 4

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_panel_without_embedding(
        self, service: ComicProjectService
    ) -> None:
        """Default compute_embedding=False: metadata.json has no embedding fields."""
        pid, iid = await _new_issue(service)
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
        )

        version_dir = f"projects/{pid}/issues/{iid}/panels/panel01_v1"
        meta_text = await service._storage.read_text(f"{version_dir}/metadata.json")
        meta = json.loads(meta_text)
        assert "embedding" not in meta
        assert "embedding_model" not in meta
        assert "embedding_dimensions" not in meta

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_structured_asset_skips_embedding(
        self, service: ComicProjectService
    ) -> None:
        """Research asset with compute_embedding=True: embed_content is NOT called."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        await service.store_asset(
            pid,
            iid,
            "research",
            "research",
            content={"data": "some research"},
            metadata={"description": "research data"},
            compute_embedding=True,
        )

        # embed_content should NOT have been called for structured assets
        client.aio.models.embed_content.assert_not_called()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_asset_embedding_noop_when_no_client(
        self, service: ComicProjectService
    ) -> None:
        """compute_embedding=True but no client: store still succeeds, no embedding."""
        assert service._genai_client is None

        pid, iid = await _new_issue(service)
        result = await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
            compute_embedding=True,
        )
        assert "uri" in result  # store succeeded

        version_dir = f"projects/{pid}/issues/{iid}/panels/panel01_v1"
        meta_text = await service._storage.read_text(f"{version_dir}/metadata.json")
        meta = json.loads(meta_text)
        assert "embedding" not in meta


# ===========================================================================
# TestCompareCharacters
# ===========================================================================


class TestCompareCharacters:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_compare_identical_embeddings(
        self, service: ComicProjectService
    ) -> None:
        """Two characters with the same embedding vector: similarity should be ~1.0."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        # Both chars get the same mock embedding ([0.1, 0.2, 0.3, 0.4])
        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )
        await service.store_character(
            pid, iid, "Beta", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )

        result = await service.compare_characters(pid, "Alpha", "Beta", style="manga")

        assert result["similarity"] == pytest.approx(1.0)
        assert "a_uri" in result
        assert "b_uri" in result
        assert result["a_uri"].startswith("comic://")
        assert result["b_uri"].startswith("comic://")

    @pytest.mark.asyncio(loop_scope="function")
    async def test_compare_missing_embedding_returns_null(
        self, service: ComicProjectService
    ) -> None:
        """Characters without embeddings return reason='missing_embedding'."""
        pid, iid = await _new_issue(service)

        # Store two characters WITHOUT embeddings (default compute_embedding=False)
        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG
        )
        await service.store_character(
            pid, iid, "Beta", "manga", **_CHAR_META, data=_PNG
        )

        result = await service.compare_characters(pid, "Alpha", "Beta", style="manga")

        assert result["similarity"] is None
        assert result["reason"] == "missing_embedding"
        assert "a_uri" in result
        assert "b_uri" in result

    @pytest.mark.asyncio(loop_scope="function")
    async def test_compare_dimension_mismatch(
        self, service: ComicProjectService
    ) -> None:
        """Alpha has 4-dim embedding, Beta has 8-dim: returns reason='dimension_mismatch'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        # Store Alpha with a 4-dim embedding
        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )

        # Store Beta without embedding first, then manually inject an 8-dim vector
        await service.store_character(
            pid, iid, "Beta", "manga", **_CHAR_META, data=_PNG
        )
        beta_meta_path = f"projects/{pid}/characters/beta/manga_v1/metadata.json"
        beta_meta = json.loads(await service._storage.read_text(beta_meta_path))
        beta_meta["embedding"] = [0.1] * 8
        await service._storage.write_text(
            beta_meta_path, json.dumps(beta_meta, indent=2)
        )

        result = await service.compare_characters(pid, "Alpha", "Beta", style="manga")

        assert result["similarity"] is None
        assert result["reason"] == "dimension_mismatch"
        assert "a_uri" in result
        assert "b_uri" in result


# ===========================================================================
# TestCompareAssets
# ===========================================================================


class TestCompareAssets:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_compare_identical_panel_embeddings(
        self, service: ComicProjectService
    ) -> None:
        """Two panels with the same embedding vector: similarity should be ~1.0."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        # Both panels get the same mock embedding ([0.1, 0.2, 0.3, 0.4])
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
            compute_embedding=True,
        )
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel02",
            data=_PNG,
            metadata={"prompt": "A villain looms"},
            compute_embedding=True,
        )

        result = await service.compare_assets(pid, iid, "panel", "panel01", "panel02")

        assert result["similarity"] == pytest.approx(1.0)
        assert "a_uri" in result
        assert "b_uri" in result
        assert result["a_uri"].startswith("comic://")
        assert result["b_uri"].startswith("comic://")

    @pytest.mark.asyncio(loop_scope="function")
    async def test_compare_assets_missing_embedding(
        self, service: ComicProjectService
    ) -> None:
        """Panels without embeddings return reason='missing_embedding'."""
        pid, iid = await _new_issue(service)

        # Store two panels WITHOUT embeddings (default compute_embedding=False)
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
        )
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel02",
            data=_PNG,
            metadata={"prompt": "A villain looms"},
        )

        result = await service.compare_assets(pid, iid, "panel", "panel01", "panel02")

        assert result["similarity"] is None
        assert result["reason"] == "missing_embedding"
        assert "a_uri" in result
        assert "b_uri" in result


# ===========================================================================
# TestSearchSimilarCharacters
# ===========================================================================


class TestSearchSimilarCharacters:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_sorted_results(self, service: ComicProjectService) -> None:
        """3 characters with same embedding, top_k=2: returns top 2 sorted descending."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        # All three get the same mock embedding → similarity 1.0
        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )
        await service.store_character(
            pid, iid, "Beta", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )
        await service.store_character(
            pid, iid, "Gamma", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )

        result = await service.search_similar_characters(pid, "Alpha", top_k=2)

        assert "query_uri" in result
        assert "results" in result
        assert len(result["results"]) == 2
        # All should have similarity ~1.0 since they all use the same mock embedding
        for r in result["results"]:
            assert r["similarity"] == pytest.approx(1.0)
        # Verify sorted descending
        sims = [r["similarity"] for r in result["results"]]
        assert sims == sorted(sims, reverse=True)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_excludes_source_character(
        self, service: ComicProjectService
    ) -> None:
        """Source character URI is not included in results."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )
        await service.store_character(
            pid, iid, "Beta", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )

        result = await service.search_similar_characters(pid, "Alpha", top_k=5)

        query_uri = result["query_uri"]
        result_uris = [r["uri"] for r in result["results"]]
        assert query_uri not in result_uris

    @pytest.mark.asyncio(loop_scope="function")
    async def test_missing_source_embedding_returns_error(
        self, service: ComicProjectService
    ) -> None:
        """Returns error dict when source character has no embedding."""
        pid, iid = await _new_issue(service)

        # Store without embedding (no client / compute_embedding=False)
        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG
        )

        result = await service.search_similar_characters(pid, "Alpha")

        assert result["similarity"] is None
        assert result["reason"] == "missing_embedding"
        assert "query_uri" in result

    @pytest.mark.asyncio(loop_scope="function")
    async def test_skips_characters_without_embeddings(
        self, service: ComicProjectService
    ) -> None:
        """Beta (no embedding) is skipped; Gamma (with embedding) is returned."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )
        # Beta stored without embedding (temporarily remove client)
        service._genai_client = None
        await service.store_character(
            pid, iid, "Beta", "manga", **_CHAR_META, data=_PNG
        )
        # Restore client for Gamma
        service.set_embedding_client(client, embedding_dim=4)
        await service.store_character(
            pid, iid, "Gamma", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )

        result = await service.search_similar_characters(pid, "Alpha", top_k=5)

        result_names = [r["name"] for r in result["results"]]
        assert "Beta" not in result_names
        assert "Gamma" in result_names


# ===========================================================================
# TestSearchSimilarAssets
# ===========================================================================


class TestSearchSimilarAssets:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_sorted_panel_results(
        self, service: ComicProjectService
    ) -> None:
        """3 panels, top_k=2: returns top 2 results sorted descending by similarity."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        # All three panels get the same mock embedding → similarity 1.0
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "hero stands tall"},
            compute_embedding=True,
        )
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel02",
            data=_PNG,
            metadata={"prompt": "villain looms"},
            compute_embedding=True,
        )
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel03",
            data=_PNG,
            metadata={"prompt": "battle scene"},
            compute_embedding=True,
        )

        result = await service.search_similar_assets(
            pid, iid, "panel", "panel01", top_k=2
        )

        assert "query_uri" in result
        assert "results" in result
        assert len(result["results"]) == 2
        # All should have similarity ~1.0 since they all use the same mock embedding
        for r in result["results"]:
            assert r["similarity"] == pytest.approx(1.0)
        # Verify sorted descending
        sims = [r["similarity"] for r in result["results"]]
        assert sims == sorted(sims, reverse=True)
        # Verify each result has required fields
        for r in result["results"]:
            assert "uri" in r
            assert "name" in r
            assert "asset_type" in r
            assert r["asset_type"] == "panel"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_excludes_source_asset(self, service: ComicProjectService) -> None:
        """Source asset is not included in results (skipped by name)."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "hero stands tall"},
            compute_embedding=True,
        )
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel02",
            data=_PNG,
            metadata={"prompt": "villain looms"},
            compute_embedding=True,
        )

        result = await service.search_similar_assets(
            pid, iid, "panel", "panel01", top_k=5
        )

        query_uri = result["query_uri"]
        result_uris = [r["uri"] for r in result["results"]]
        assert query_uri not in result_uris
        # Verify source asset name is not in results
        result_names = [r["name"] for r in result["results"]]
        assert "panel01" not in result_names

    @pytest.mark.asyncio(loop_scope="function")
    async def test_missing_source_embedding(self, service: ComicProjectService) -> None:
        """Returns error dict when source asset has no embedding."""
        pid, iid = await _new_issue(service)

        # Store panel without embedding (no client / compute_embedding=False)
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "hero stands tall"},
        )

        result = await service.search_similar_assets(pid, iid, "panel", "panel01")

        assert result["similarity"] is None
        assert result["reason"] == "missing_embedding"
        assert "query_uri" in result


# ===========================================================================
# TestEmbedCharacter
# ===========================================================================


class TestEmbedCharacter:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_backfill_adds_embedding(self, service: ComicProjectService) -> None:
        """Store character without embedding, backfill, verify embedding present."""
        pid, iid = await _new_issue(service)

        # Store character WITHOUT embedding (no client)
        await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
        )

        # Now set up client and backfill
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        result = await service.embed_character(pid, "Hero")

        # Verify return dict
        assert result["embedded"] is True
        assert "uri" in result
        assert result["uri"].startswith("comic://")
        assert "style" in result

        # Verify metadata.json now has embedding fields
        char_slug = "hero"
        style_slug = "manga"
        meta_text = await service._storage.read_text(
            f"projects/{pid}/characters/{char_slug}/{style_slug}_v1/metadata.json"
        )
        meta = json.loads(meta_text)
        assert "embedding" in meta
        assert meta["embedding"] == pytest.approx([0.1 * (i + 1) for i in range(4)])
        assert meta["embedding_model"] == "gemini-embedding-2-preview"
        assert meta["embedding_dimensions"] == 4

    @pytest.mark.asyncio(loop_scope="function")
    async def test_backfill_noop_when_no_client(
        self, service: ComicProjectService
    ) -> None:
        """Returns {embedded: False, reason: 'no_client'} when no client set."""
        pid, iid = await _new_issue(service)

        await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
        )

        # No client set (default)
        assert service._genai_client is None

        result = await service.embed_character(pid, "Hero")

        assert result["embedded"] is False
        assert result["reason"] == "no_client"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_backfill_with_specific_style(
        self, service: ComicProjectService
    ) -> None:
        """Backfill with style='manga' only affects the manga version."""
        pid, iid = await _new_issue(service)

        # Store character with manga style
        await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
        )

        # Set up client and backfill with explicit style
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        result = await service.embed_character(pid, "Hero", style="manga")

        assert result["embedded"] is True
        assert result["style"] == "manga"
        assert "uri" in result

        # Verify embedding was written to the manga version
        char_slug = "hero"
        meta_text = await service._storage.read_text(
            f"projects/{pid}/characters/{char_slug}/manga_v1/metadata.json"
        )
        meta = json.loads(meta_text)
        assert "embedding" in meta


# ===========================================================================
# TestEmbedAsset
# ===========================================================================


class TestEmbedAsset:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_backfill_adds_embedding_to_panel(
        self, service: ComicProjectService
    ) -> None:
        """Store panel without embedding, backfill, verify embedding present."""
        pid, iid = await _new_issue(service)

        # Store panel WITHOUT embedding (no client)
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall", "description": "Scene 1"},
        )

        # Now set up client and backfill
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        result = await service.embed_asset(pid, iid, "panel", "panel01")

        # Verify return dict
        assert result["embedded"] is True
        assert "uri" in result
        assert result["uri"].startswith("comic://")

        # Verify metadata.json now has embedding fields
        version_dir = f"projects/{pid}/issues/{iid}/panels/panel01_v1"
        meta_text = await service._storage.read_text(f"{version_dir}/metadata.json")
        meta = json.loads(meta_text)
        assert "embedding" in meta
        assert meta["embedding"] == pytest.approx([0.1 * (i + 1) for i in range(4)])
        assert meta["embedding_model"] == "gemini-embedding-2-preview"
        assert meta["embedding_dimensions"] == 4

    @pytest.mark.asyncio(loop_scope="function")
    async def test_backfill_noop_when_no_client(
        self, service: ComicProjectService
    ) -> None:
        """Returns {embedded: False, reason: 'no_client'} when no client set."""
        pid, iid = await _new_issue(service)

        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
        )

        # No client set (default)
        assert service._genai_client is None

        result = await service.embed_asset(pid, iid, "panel", "panel01")

        assert result["embedded"] is False
        assert result["reason"] == "no_client"


# ===========================================================================
# TestMountEmbeddingDiscovery
# ===========================================================================


class TestMountEmbeddingDiscovery:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_mount_sets_client_from_provider(self) -> None:
        """FakeProvider with a mock client: mount() sets service._genai_client."""
        mock_client = MagicMock()

        class FakeProvider:
            client = mock_client

        captured: dict[str, Any] = {}

        coordinator = MagicMock()
        coordinator.mount = AsyncMock()
        coordinator.register_capability = MagicMock(
            side_effect=lambda name, svc: captured.update({name: svc})
        )
        coordinator.get = MagicMock(return_value={"gemini-flash": FakeProvider()})

        from amplifier_module_comic_assets import (
            mount,
        )  # import inline to avoid early-mount side effects

        await mount(coordinator)

        service = captured["comic.project-service"]
        assert service._genai_client is mock_client

    @pytest.mark.asyncio(loop_scope="function")
    async def test_mount_works_without_provider(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No providers, no env vars: mount() leaves service._genai_client as None."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        captured: dict[str, Any] = {}

        coordinator = MagicMock()
        coordinator.mount = AsyncMock()
        coordinator.register_capability = MagicMock(
            side_effect=lambda name, svc: captured.update({name: svc})
        )
        coordinator.get = MagicMock(return_value=None)

        from amplifier_module_comic_assets import (
            mount,
        )  # import inline to avoid early-mount side effects

        await mount(coordinator)

        service = captured["comic.project-service"]
        assert service._genai_client is None


# ===========================================================================
# TestEmbeddingIsolation — tool layer must strip embedding vectors
# ===========================================================================


class TestEmbeddingIsolation:
    """Verify that all get/list/search tool actions strip the embedding vector.

    Characters and assets can carry an ``embedding`` field in their stored
    metadata. That vector is large and must not be returned to agent context.
    ``embedding_model`` and ``embedding_dimensions`` *should* be preserved so
    callers can still identify the model used.

    Tests use mocked service methods so the tool layer is tested in isolation:
    the mock simulates a service that returns raw metadata including an embedding
    vector, and we verify the tool strips the vector before returning to the LLM.
    """

    @pytest.mark.asyncio(loop_scope="function")
    async def test_get_character_strips_embedding(
        self, service: ComicProjectService
    ) -> None:
        """ComicCharacterTool get: 'embedding' absent; embedding_model/dimensions present."""
        # Arrange — mock get_character to return metadata that includes an embedding vector
        raw_char_meta = {
            "name": "Hero",
            "project_id": "test_proj",
            "style": "manga",
            "version": 1,
            "created_at": "2025-01-01T00:00:00+00:00",
            "origin_issue_id": "issue-001",
            "role": "protagonist",
            "character_type": "main",
            "bundle": "comic-strips",
            "visual_traits": "tall, blue eyes",
            "team_markers": "hero badge",
            "distinctive_features": "scar",
            "backstory": "",
            "motivations": "",
            "personality": "",
            "review_status": "",
            "review_feedback": "",
            "metadata": {},
            "uri": "comic://test_proj/characters/hero?v=1",
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "embedding_model": "gemini-embedding-2-preview",
            "embedding_dimensions": 4,
        }
        service.get_character = AsyncMock(return_value=raw_char_meta)  # type: ignore[method-assign]

        tool = ComicCharacterTool(service)
        result = await tool.execute(
            {"action": "get", "project": "test_proj", "name": "Hero"}
        )

        assert result.success is True
        data = json.loads(result.output)
        assert "embedding" not in data
        assert "embedding_model" in data
        assert "embedding_dimensions" in data

    @pytest.mark.asyncio(loop_scope="function")
    async def test_list_characters_strips_embedding(
        self, service: ComicProjectService
    ) -> None:
        """ComicCharacterTool list: no entry in the list contains an 'embedding' key."""
        # Arrange — mock list_characters to return entries with embedding vectors
        raw_entries = [
            {
                "name": "Alpha",
                "char_slug": "alpha",
                "styles": {"manga": 1},
                "total_versions": 1,
                "uri": "comic://proj/characters/alpha?v=1",
                "embedding": [0.1, 0.2, 0.3, 0.4],
                "embedding_model": "gemini-embedding-2-preview",
                "embedding_dimensions": 4,
            },
            {
                "name": "Beta",
                "char_slug": "beta",
                "styles": {"manga": 1},
                "total_versions": 1,
                "uri": "comic://proj/characters/beta?v=1",
                "embedding": [0.5, 0.6, 0.7, 0.8],
                "embedding_model": "gemini-embedding-2-preview",
                "embedding_dimensions": 4,
            },
        ]
        service.list_characters = AsyncMock(return_value=raw_entries)  # type: ignore[method-assign]

        tool = ComicCharacterTool(service)
        result = await tool.execute({"action": "list", "project": "test_proj"})

        assert result.success is True
        entries = json.loads(result.output)
        assert len(entries) == 2
        for entry in entries:
            assert "embedding" not in entry

    @pytest.mark.asyncio(loop_scope="function")
    async def test_get_asset_strips_embedding(
        self, service: ComicProjectService
    ) -> None:
        """ComicAssetTool get: 'embedding' absent; embedding_model/dimensions present."""
        # Arrange — mock get_asset to return metadata that includes an embedding vector
        raw_asset_meta = {
            "name": "panel01",
            "asset_type": "panel",
            "project_id": "test_proj",
            "issue_id": "issue-001",
            "version": 1,
            "created_at": "2025-01-01T00:00:00+00:00",
            "mime_type": "image/png",
            "size_bytes": 108,
            "review_status": "",
            "review_feedback": "",
            "metadata": {"prompt": "A hero stands tall"},
            "uri": "comic://test_proj/issues/issue-001/panels/panel01?v=1",
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "embedding_model": "gemini-embedding-2-preview",
            "embedding_dimensions": 4,
        }
        service.get_asset = AsyncMock(return_value=raw_asset_meta)  # type: ignore[method-assign]

        tool = ComicAssetTool(service)
        result = await tool.execute(
            {
                "action": "get",
                "project": "test_proj",
                "issue": "issue-001",
                "type": "panel",
                "name": "panel01",
            }
        )

        assert result.success is True
        data = json.loads(result.output)
        assert "embedding" not in data
        assert "embedding_model" in data
        assert "embedding_dimensions" in data


# ===========================================================================
# TestToolComputeEmbedding — tool layer must pass compute_embedding through
# ===========================================================================


class TestToolComputeEmbedding:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_character_tool_passes_compute_embedding(
        self, service: ComicProjectService
    ) -> None:
        """store via tool with compute_embedding=True writes embedding to metadata.json."""
        # Arrange: give the service an embedding client
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        # Create a project/issue so the store can succeed
        r = await service.create_issue("test_project", "Issue 1")
        pid = r["project_id"]
        iid = r["issue_id"]

        tool = ComicCharacterTool(service)
        png_b64 = base64.b64encode(_PNG).decode()

        # Act: invoke the tool with compute_embedding=True
        result = await tool.execute(
            {
                "action": "store",
                "project": pid,
                "issue": iid,
                "name": "Hero",
                "style": "manga",
                "role": "protagonist",
                "character_type": "main",
                "bundle": "comic-strips",
                "visual_traits": "tall, blue eyes",
                "team_markers": "hero badge",
                "distinctive_features": "scar on left cheek",
                "data": png_b64,
                "compute_embedding": True,
            }
        )

        assert result.success is True, f"Tool store failed: {result.output}"

        # Assert: verify the embedding was written to metadata.json on disk
        char_slug = "hero"
        meta_text = await service._storage.read_text(
            f"projects/{pid}/characters/{char_slug}/manga_v1/metadata.json"
        )
        meta = json.loads(meta_text)
        assert "embedding" in meta, "embedding key missing from metadata.json on disk"
        assert len(meta["embedding"]) == 4
        assert meta["embedding_model"] == "gemini-embedding-2-preview"
        assert meta["embedding_dimensions"] == 4

    @pytest.mark.asyncio(loop_scope="function")
    async def test_asset_tool_passes_compute_embedding(
        self, service: ComicProjectService
    ) -> None:
        """store panel via tool with compute_embedding=True writes embedding to metadata.json."""
        # Arrange: give the service an embedding client
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        # Create a project/issue so the store can succeed
        r = await service.create_issue("test_project", "Issue 1")
        pid = r["project_id"]
        iid = r["issue_id"]

        tool = ComicAssetTool(service)
        png_b64 = base64.b64encode(_PNG).decode()

        # Act: invoke the tool with compute_embedding=True
        result = await tool.execute(
            {
                "action": "store",
                "project": pid,
                "issue": iid,
                "type": "panel",
                "name": "panel01",
                "data": png_b64,
                "compute_embedding": True,
            }
        )

        assert result.success is True, f"Tool store failed: {result.output}"

        # Assert: verify the embedding was written to metadata.json on disk
        version_dir = f"projects/{pid}/issues/{iid}/panels/panel01_v1"
        meta_text = await service._storage.read_text(f"{version_dir}/metadata.json")
        meta = json.loads(meta_text)
        assert "embedding" in meta, "embedding key missing from metadata.json on disk"
        assert len(meta["embedding"]) == 4
        assert meta["embedding_model"] == "gemini-embedding-2-preview"
        assert meta["embedding_dimensions"] == 4


# ===========================================================================
# TestToolCompareAction — tool layer compare action
# ===========================================================================


class TestToolCompareAction:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_character_compare_action(self, service: ComicProjectService) -> None:
        """Two characters with identical embeddings: compare via tool returns similarity ~1.0 with no 'embedding' in output."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        # Both characters receive the same mock embedding → similarity 1.0
        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )
        await service.store_character(
            pid, iid, "Beta", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )

        tool = ComicCharacterTool(service)
        result = await tool.execute(
            {
                "action": "compare",
                "project": pid,
                "name": "Alpha",
                "name_b": "Beta",
                "style": "manga",
            }
        )

        assert result.success is True, f"compare action failed: {result.output}"
        data = json.loads(result.output)
        assert data["similarity"] == pytest.approx(1.0)
        assert "embedding" not in data

    @pytest.mark.asyncio(loop_scope="function")
    async def test_character_compare_missing_name_b(
        self, service: ComicProjectService
    ) -> None:
        """compare action without name_b returns a clean error, not an exception."""
        tool = ComicCharacterTool(service)
        result = await tool.execute(
            {
                "action": "compare",
                "project": "some_project",
                "name": "Alpha",
                # name_b intentionally omitted
            }
        )

        assert result.success is False
        assert "name_b" in result.output

    @pytest.mark.asyncio(loop_scope="function")
    async def test_asset_compare_action(
        self, service: ComicProjectService, sample_png: str
    ) -> None:
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)
        pid, iid = await _new_issue(service, "tool_cmp_asset", "I1")
        await service.store_asset(
            pid,
            iid,
            "panel",
            "p01",
            source_path=sample_png,
            metadata={"prompt": "hero"},
            compute_embedding=True,
        )
        await service.store_asset(
            pid,
            iid,
            "panel",
            "p02",
            source_path=sample_png,
            metadata={"prompt": "hero"},
            compute_embedding=True,
        )
        tool = ComicAssetTool(service)
        result = await tool.execute(
            {
                "action": "compare",
                "project": pid,
                "issue": iid,
                "type": "panel",
                "name": "p01",
                "name_b": "p02",
            }
        )
        assert result.success is True
        data = json.loads(result.output)
        assert data["similarity"] == pytest.approx(1.0)


# ===========================================================================
# TestToolSearchSimilarAction — tool layer search_similar action
# ===========================================================================


class TestToolSearchSimilarAction:
    """Verify search_similar action works through the tool layer."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_character_search_similar_action(
        self, service: ComicProjectService, sample_png: str
    ) -> None:
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)
        pid, iid = await _new_issue(service, "tool_ss_char", "I1")
        for char_name in ["Alpha", "Beta"]:
            await service.store_character(
                pid,
                iid,
                char_name,
                "manga",
                **_CHAR_META,
                source_path=sample_png,
                compute_embedding=True,
            )
        tool = ComicCharacterTool(service)
        result = await tool.execute(
            {
                "action": "search_similar",
                "project": pid,
                "name": "Alpha",
                "top_k": 1,
            }
        )
        assert result.success is True
        data = json.loads(result.output)
        assert data["query_uri"].startswith("comic://")
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "Beta"
        for r in data["results"]:
            assert "embedding" not in r

    @pytest.mark.asyncio(loop_scope="function")
    async def test_asset_search_similar_action(
        self, service: ComicProjectService, sample_png: str
    ) -> None:
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)
        pid, iid = await _new_issue(service, "tool_ss_asset", "I1")
        for n in ["p01", "p02"]:
            await service.store_asset(
                pid,
                iid,
                "panel",
                n,
                source_path=sample_png,
                metadata={"prompt": "hero"},
                compute_embedding=True,
            )
        tool = ComicAssetTool(service)
        result = await tool.execute(
            {
                "action": "search_similar",
                "project": pid,
                "issue": iid,
                "type": "panel",
                "name": "p01",
                "top_k": 1,
            }
        )
        assert result.success is True
        data = json.loads(result.output)
        assert len(data["results"]) == 1
        assert data["query_uri"].startswith("comic://")
        assert data["results"][0]["name"] == "p02"
        for r in data["results"]:
            assert "embedding" not in r


# ===========================================================================
# TestToolEmbedAction — tool layer embed action
# ===========================================================================


class TestToolEmbedAction:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_character_embed_action(
        self, service: ComicProjectService, sample_png: str
    ) -> None:
        pid, iid = await _new_issue(service, "tool_bf_char", "I1")
        await service.store_character(
            pid, iid, "Hero", "manga", **_CHAR_META, source_path=sample_png
        )
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)
        tool = ComicCharacterTool(service)
        result = await tool.execute({"action": "embed", "project": pid, "name": "Hero"})
        assert result.success is True
        data = json.loads(result.output)
        assert data["embedded"] is True
        assert "embedding" not in data

    @pytest.mark.asyncio(loop_scope="function")
    async def test_asset_embed_action(
        self, service: ComicProjectService, sample_png: str
    ) -> None:
        pid, iid = await _new_issue(service, "tool_bf_asset", "I1")
        await service.store_asset(
            pid,
            iid,
            "panel",
            "p01",
            source_path=sample_png,
            metadata={"prompt": "hero on cliff"},
        )
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)
        tool = ComicAssetTool(service)
        result = await tool.execute(
            {
                "action": "embed",
                "project": pid,
                "issue": iid,
                "type": "panel",
                "name": "p01",
            }
        )
        assert result.success is True
        data = json.loads(result.output)
        assert data["embedded"] is True
        assert "embedding" not in data


# ===========================================================================
# TestCircuitBreaker — EmbeddingCircuitBreaker unit tests
# ===========================================================================


class TestCircuitBreaker:
    def test_initial_state_is_closed(self) -> None:
        """New breaker starts in closed state."""
        breaker = EmbeddingCircuitBreaker()
        assert breaker.state == "closed"
        assert breaker.allow_request() is True

    def test_single_failure_stays_closed(self) -> None:
        """One failure does not trip the breaker."""
        breaker = EmbeddingCircuitBreaker()
        breaker.record_failure()
        assert breaker.state == "closed"
        assert breaker.allow_request() is True

    def test_trips_after_3_consecutive_failures(self) -> None:
        """Three consecutive failures trip the breaker (state becomes 'open')."""
        breaker = EmbeddingCircuitBreaker()
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"
        assert breaker.allow_request() is False

    def test_success_resets_failure_count(self) -> None:
        """Success after 2 failures resets count; breaker stays closed."""
        breaker = EmbeddingCircuitBreaker()
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        assert breaker.state == "closed"
        assert breaker.allow_request() is True

    def test_half_open_after_cooldown(self) -> None:
        """After cooldown expires, open breaker transitions to half_open."""
        breaker = EmbeddingCircuitBreaker(cooldown_seconds=0.1)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"
        time.sleep(0.15)
        assert breaker.state == "half_open"
        assert breaker.allow_request() is True

    def test_successful_probe_closes_breaker(self) -> None:
        """A successful probe in half_open state closes the breaker."""
        breaker = EmbeddingCircuitBreaker(cooldown_seconds=0.1)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        time.sleep(0.15)
        assert breaker.state == "half_open"
        breaker.record_success()
        assert breaker.state == "closed"
        assert breaker.allow_request() is True

    def test_failed_probe_reopens_breaker(self) -> None:
        """A failed probe in half_open state re-opens the breaker."""
        breaker = EmbeddingCircuitBreaker(cooldown_seconds=0.1)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        time.sleep(0.15)
        assert breaker.state == "half_open"
        breaker.record_failure()
        assert breaker.state == "open"
        assert breaker.allow_request() is False


# ===========================================================================
# TestCircuitBreakerIntegration — breaker wired into ComicProjectService
# ===========================================================================


class TestCircuitBreakerIntegration:
    def test_service_has_breaker_attribute(self, service: ComicProjectService) -> None:
        """ComicProjectService.__init__ creates a _breaker as EmbeddingCircuitBreaker."""
        assert hasattr(service, "_breaker")
        assert isinstance(service._breaker, EmbeddingCircuitBreaker)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_open_breaker_skips_embedding_and_doesnt_call_api(
        self, service: ComicProjectService
    ) -> None:
        """Open breaker causes _compute_embedding to return None without calling the API."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        # Trip the breaker by recording 3 failures
        service._breaker.record_failure()
        service._breaker.record_failure()
        service._breaker.record_failure()
        assert service._breaker.state == "open"

        # _compute_embedding should return None without calling the API
        result = await service._compute_embedding(None, "hello world")
        assert result is None
        client.aio.models.embed_content.assert_not_called()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_api_failures_record_on_breaker_and_trip_it(
        self, service: ComicProjectService
    ) -> None:
        """Three API failures record on the breaker and trip it to 'open' state."""
        client = MagicMock()
        client.aio = MagicMock()
        client.aio.models = MagicMock()
        client.aio.models.embed_content = AsyncMock(
            side_effect=RuntimeError("API error")
        )
        service.set_embedding_client(client, embedding_dim=4)

        # Breaker starts closed
        assert service._breaker.state == "closed"

        # 3 consecutive failures should trip the breaker
        await service._compute_embedding(None, "text 1")
        assert service._breaker.state == "closed"  # still closed after 1

        await service._compute_embedding(None, "text 2")
        assert service._breaker.state == "closed"  # still closed after 2

        await service._compute_embedding(None, "text 3")
        assert service._breaker.state == "open"  # tripped after 3

    @pytest.mark.asyncio(loop_scope="function")
    async def test_api_success_calls_record_success_keeping_breaker_closed(
        self, service: ComicProjectService
    ) -> None:
        """Successful API call records success, keeping the breaker closed."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        # Record 2 failures to get close to the threshold
        service._breaker.record_failure()
        service._breaker.record_failure()
        assert service._breaker.state == "closed"

        # A successful call should record success (reset failure count)
        result = await service._compute_embedding(None, "hello world")
        assert result is not None
        assert service._breaker.state == "closed"
        # Breaker failure count should be reset — verify by checking we can
        # take 2 more failures before tripping (would trip at 3 total if reset)
        service._breaker.record_failure()
        service._breaker.record_failure()
        assert service._breaker.state == "closed"  # would be open if not reset


# ===========================================================================
# TestAutoEmbeddingDefault — compute_embedding defaults to True
# ===========================================================================


class TestAutoEmbeddingDefault:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_character_embeds_by_default(
        self, service: ComicProjectService
    ) -> None:
        """store_character with client but no compute_embedding arg: embedding is written."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            # compute_embedding NOT specified — should default to True
        )
        char_slug = "hero"
        meta_text = await service._storage.read_text(
            f"projects/{pid}/characters/{char_slug}/manga_v1/metadata.json"
        )
        meta = json.loads(meta_text)
        assert "embedding" in meta, (
            "embedding should be present when client is configured"
        )
        assert "embedding_model" in meta
        assert "embedding_dimensions" in meta

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_character_skips_when_no_client(
        self, service: ComicProjectService
    ) -> None:
        """store_character with no client: silently skips embedding, no error."""
        assert service._genai_client is None

        pid, iid = await _new_issue(service)
        result = await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            # compute_embedding NOT specified — defaults to True but no client
        )
        assert "uri" in result  # store succeeded
        char_slug = "hero"
        meta_text = await service._storage.read_text(
            f"projects/{pid}/characters/{char_slug}/manga_v1/metadata.json"
        )
        meta = json.loads(meta_text)
        assert "embedding" not in meta

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_asset_embeds_by_default_for_binary_types(
        self, service: ComicProjectService
    ) -> None:
        """store_asset (panel) with client but no compute_embedding arg: embedding is written."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
            # compute_embedding NOT specified — should default to True
        )

        version_dir = f"projects/{pid}/issues/{iid}/panels/panel01_v1"
        meta_text = await service._storage.read_text(f"{version_dir}/metadata.json")
        meta = json.loads(meta_text)
        assert "embedding" in meta, (
            "embedding should be present when client is configured"
        )
        assert "embedding_model" in meta
        assert "embedding_dimensions" in meta

    @pytest.mark.asyncio(loop_scope="function")
    async def test_structured_types_skip_embedding_by_default(
        self, service: ComicProjectService
    ) -> None:
        """store_asset for research type: embed_content NOT called even with client configured."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        await service.store_asset(
            pid,
            iid,
            "research",
            "research",
            content={"data": "some research"},
            metadata={"description": "research data"},
            # compute_embedding NOT specified — defaults to True but structured type skips
        )

        # embed_content should NOT have been called for structured assets
        client.aio.models.embed_content.assert_not_called()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_character_can_opt_out_with_compute_embedding_false(
        self, service: ComicProjectService
    ) -> None:
        """store_character with client but compute_embedding=False: no embedding written."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            compute_embedding=False,
        )
        char_slug = "hero"
        meta_text = await service._storage.read_text(
            f"projects/{pid}/characters/{char_slug}/manga_v1/metadata.json"
        )
        meta = json.loads(meta_text)
        assert "embedding" not in meta
        assert "embedding_model" not in meta
        assert "embedding_dimensions" not in meta


# ===========================================================================
# TestEmbeddingStatus — embedding_status field in store_character / store_asset
# ===========================================================================


class TestEmbeddingStatus:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_character_returns_embedded_with_client(
        self, service: ComicProjectService
    ) -> None:
        """store_character with client returns embedding_status='embedded'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        result = await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            compute_embedding=True,
        )
        assert "embedding_status" in result
        assert result["embedding_status"] == "embedded"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_character_returns_skipped_no_client(
        self, service: ComicProjectService
    ) -> None:
        """store_character without client returns embedding_status='skipped_no_client'."""
        assert service._genai_client is None

        pid, iid = await _new_issue(service)
        result = await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            compute_embedding=True,
        )
        assert "embedding_status" in result
        assert result["embedding_status"] == "skipped_no_client"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_character_returns_skipped_circuit_open(
        self, service: ComicProjectService
    ) -> None:
        """store_character with tripped breaker returns embedding_status='skipped_circuit_open'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        # Trip the breaker
        service._breaker.record_failure()
        service._breaker.record_failure()
        service._breaker.record_failure()
        assert service._breaker.state == "open"

        pid, iid = await _new_issue(service)
        result = await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            compute_embedding=True,
        )
        assert "embedding_status" in result
        assert result["embedding_status"] == "skipped_circuit_open"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_asset_structured_returns_skipped_not_applicable(
        self, service: ComicProjectService
    ) -> None:
        """store_asset for structured type returns embedding_status='skipped_not_applicable'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        result = await service.store_asset(
            pid,
            iid,
            "research",
            "research",
            content={"data": "some research"},
            compute_embedding=True,
        )
        assert "embedding_status" in result
        assert result["embedding_status"] == "skipped_not_applicable"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_asset_panel_returns_embedded(
        self, service: ComicProjectService
    ) -> None:
        """store_asset panel with client returns embedding_status='embedded'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        result = await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
            compute_embedding=True,
        )
        assert "embedding_status" in result
        assert result["embedding_status"] == "embedded"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_character_opt_out_returns_skipped_not_requested(
        self, service: ComicProjectService
    ) -> None:
        """store_character with compute_embedding=False returns status != 'embedded'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        result = await service.store_character(
            pid,
            iid,
            "Hero",
            "manga",
            **_CHAR_META,
            data=_PNG,
            compute_embedding=False,
        )
        assert "embedding_status" in result
        assert result["embedding_status"] != "embedded"
        assert result["embedding_status"] == "skipped_not_requested"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_asset_panel_opt_out_returns_skipped_not_requested(
        self, service: ComicProjectService
    ) -> None:
        """store_asset panel with compute_embedding=False returns embedding_status='skipped_not_requested'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)
        result = await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
            compute_embedding=False,
        )
        assert "embedding_status" in result
        assert result["embedding_status"] == "skipped_not_requested"


# ===========================================================================
# TestStyleEmbedding — store_style and embed_style embedding support
# ===========================================================================


class TestStyleEmbedding:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_style_embeds_by_default(
        self, service: ComicProjectService
    ) -> None:
        """store_style with client writes embedding and embedding_model to definition.json."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        definition = {
            "name": "Manga Action",
            "description": "Fast paced manga style",
            "aesthetic_direction": "bold lines",
            "color_palette": {"primary": "black", "secondary": "white"},
            "panel_conventions": "N/N/N panel grid",
        }
        result = await service.store_style(pid, iid, "manga-action", definition)

        # Verify embedding_status in return dict
        assert "embedding_status" in result
        assert result["embedding_status"] == "embedded"

        # Verify definition.json has embedding and embedding_model
        style_slug = "manga-action"
        version = result["version"]
        def_path = f"projects/{pid}/styles/{style_slug}_v{version}/definition.json"
        def_text = await service._storage.read_text(def_path)
        def_data = json.loads(def_text)
        assert "embedding" in def_data
        assert "embedding_model" in def_data
        assert def_data["embedding_model"] == "gemini-embedding-2-preview"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_store_style_no_client_skips(
        self, service: ComicProjectService
    ) -> None:
        """store_style without client skips embedding; no embedding fields in definition.json."""
        assert service._genai_client is None

        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        definition = {
            "name": "Manga Action",
            "description": "Fast paced manga style",
        }
        result = await service.store_style(pid, iid, "manga-action", definition)

        assert "uri" in result  # store succeeded
        assert "embedding_status" in result
        assert result["embedding_status"] != "embedded"

        # No embedding fields in definition.json
        style_slug = "manga-action"
        version = result["version"]
        def_path = f"projects/{pid}/styles/{style_slug}_v{version}/definition.json"
        def_text = await service._storage.read_text(def_path)
        def_data = json.loads(def_text)
        assert "embedding" not in def_data
        assert "embedding_model" not in def_data

    @pytest.mark.asyncio(loop_scope="function")
    async def test_embed_style_backfills_existing(
        self, service: ComicProjectService
    ) -> None:
        """embed_style backfills embedding for a stored style that has no embedding."""
        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        # Store style without embedding (no client)
        definition = {
            "name": "Manga Action",
            "description": "Fast paced manga style",
            "aesthetic_direction": "bold lines",
        }
        store_result = await service.store_style(pid, iid, "manga-action", definition)
        version = store_result["version"]

        # Now set up client and backfill
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        result = await service.embed_style(pid, "manga-action")

        assert result["embedded"] is True
        assert "uri" in result
        assert result["uri"].startswith("comic://")

        # Verify definition.json now has embedding fields
        style_slug = "manga-action"
        def_path = f"projects/{pid}/styles/{style_slug}_v{version}/definition.json"
        def_text = await service._storage.read_text(def_path)
        def_data = json.loads(def_text)
        assert "embedding" in def_data
        assert def_data["embedding_model"] == "gemini-embedding-2-preview"
        assert "embedding_dimensions" in def_data

    @pytest.mark.asyncio(loop_scope="function")
    async def test_embed_style_no_client_returns_no_client(
        self, service: ComicProjectService
    ) -> None:
        """embed_style without client returns {embedded: False, reason: 'no_client'}."""
        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        definition = {"name": "Manga Action", "description": "Fast paced manga style"}
        await service.store_style(pid, iid, "manga-action", definition)

        # No client set (default)
        assert service._genai_client is None

        result = await service.embed_style(pid, "manga-action")

        assert result["embedded"] is False
        assert result["reason"] == "no_client"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_style_embed_is_text_only(self, service: ComicProjectService) -> None:
        """Style embeddings are text-only: image_path is None in _compute_embedding call."""
        captured_args: list[tuple[str | None, str | None]] = []

        async def mock_compute(image_path: str | None, text: str | None) -> list[float]:
            captured_args.append((image_path, text))
            return [0.1] * 4

        # Give the service a non-None client so the compute_embedding branch fires.
        service._genai_client = MagicMock()

        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        definition = {
            "name": "Manga Action",
            "description": "Fast paced manga style",
            "aesthetic_direction": "bold lines",
            "color_palette": {"primary": "black"},
            "panel_conventions": "N/N/N panel grid",
        }
        with patch.object(service, "_compute_embedding", side_effect=mock_compute):
            await service.store_style(pid, iid, "manga-action", definition)

        assert captured_args, "Expected _compute_embedding to be called"
        image_path, text = captured_args[0]
        # Must be text-only: no image
        assert image_path is None
        # Text must contain definition content
        assert text is not None


# ===========================================================================
# TestCompareStyles — compare_styles service method
# ===========================================================================


class TestCompareStyles:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_compare_identical_styles_returns_similarity(
        self, service: ComicProjectService
    ) -> None:
        """Two styles with the same embedding vector: similarity ~1.0, a_uri and b_uri present."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        definition = {
            "name": "Manga Action",
            "description": "Fast paced manga style",
            "aesthetic_direction": "bold lines",
            "color_palette": {"primary": "black", "secondary": "white"},
            "panel_conventions": "N/N/N panel grid",
        }

        # Both styles get the same mock embedding (identical vectors → similarity 1.0)
        await service.store_style(
            pid, iid, "manga-action", definition, compute_embedding=True
        )
        await service.store_style(
            pid, iid, "superhero", definition, compute_embedding=True
        )

        result = await service.compare_styles(pid, "manga-action", "superhero")

        assert result["similarity"] == pytest.approx(1.0)
        assert "a_uri" in result
        assert "b_uri" in result
        assert result["a_uri"].startswith("comic://")
        assert result["b_uri"].startswith("comic://")

    @pytest.mark.asyncio(loop_scope="function")
    async def test_compare_styles_without_embeddings_returns_missing(
        self, service: ComicProjectService
    ) -> None:
        """Styles without embeddings return similarity=None with reason='missing_embedding'."""
        # No client configured → no embeddings stored
        assert service._genai_client is None

        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        definition = {"name": "Manga Action", "description": "Fast paced manga style"}

        await service.store_style(
            pid, iid, "manga-action", definition, compute_embedding=False
        )
        await service.store_style(
            pid, iid, "superhero", definition, compute_embedding=False
        )

        result = await service.compare_styles(pid, "manga-action", "superhero")

        assert result["similarity"] is None
        assert result["reason"] == "missing_embedding"
        assert "a_uri" in result
        assert "b_uri" in result


# ===========================================================================
# TestSearchSimilarStyles — search_similar_styles service method
# ===========================================================================


class TestSearchSimilarStyles:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_sorted_results_excluding_source(
        self, service: ComicProjectService
    ) -> None:
        """3 styles with same embedding, top_k=2: returns top 2 sorted descending, source excluded."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        definition = {
            "name": "Manga Action",
            "description": "Fast paced manga style",
            "aesthetic_direction": "bold lines",
        }

        # All three styles get the same mock embedding → similarity 1.0
        await service.store_style(
            pid, iid, "manga-action", definition, compute_embedding=True
        )
        await service.store_style(
            pid, iid, "superhero", definition, compute_embedding=True
        )
        await service.store_style(pid, iid, "indie", definition, compute_embedding=True)

        result = await service.search_similar_styles(pid, "manga-action", top_k=2)

        assert "query_uri" in result
        assert "results" in result
        assert len(result["results"]) == 2

        # Source should NOT be in results
        query_uri = result["query_uri"]
        result_uris = [r["uri"] for r in result["results"]]
        assert query_uri not in result_uris

        # All results have similarity ~1.0 (same mock embedding)
        for r in result["results"]:
            assert r["similarity"] == pytest.approx(1.0)
            assert "uri" in r
            assert "name" in r
            assert "originating_project" in r

        # Verify sorted descending
        sims = [r["similarity"] for r in result["results"]]
        assert sims == sorted(sims, reverse=True)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_missing_source_embedding_returns_error(
        self, service: ComicProjectService
    ) -> None:
        """Returns error dict when source style has no embedding."""
        # No client configured → no embeddings stored
        assert service._genai_client is None

        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        definition = {"name": "Manga Action", "description": "Fast paced manga style"}
        await service.store_style(
            pid, iid, "manga-action", definition, compute_embedding=False
        )

        result = await service.search_similar_styles(pid, "manga-action")

        assert result["similarity"] is None
        assert result["reason"] == "missing_embedding"
        assert "query_uri" in result


# ===========================================================================
# TestStyleStripEmbedding — tool layer must strip embedding vectors from style responses
# ===========================================================================


class TestStyleStripEmbedding:
    """Verify that get/list style tool actions strip the embedding vector.

    Styles can carry an ``embedding`` field in their stored definition.
    That vector is large and must not be returned to agent context.
    ``embedding_model`` and ``embedding_dimensions`` *should* be preserved so
    callers can still identify the model used.
    """

    @pytest.mark.asyncio(loop_scope="function")
    async def test_get_style_strips_embedding(
        self, service: ComicProjectService
    ) -> None:
        """ComicStyleTool get with include='full': 'embedding' absent; embedding_model/dimensions present."""
        raw_style = {
            "name": "manga-action",
            "project_id": "test_proj",
            "version": 1,
            "uri": "comic://test_proj/styles/manga-action?v=1",
            "definition": {
                "name": "Manga Action",
                "description": "Fast paced manga style",
            },
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "embedding_model": "gemini-embedding-2-preview",
            "embedding_dimensions": 4,
        }
        service.get_style = AsyncMock(return_value=raw_style)  # type: ignore[method-assign]

        tool = ComicStyleTool(service)
        result = await tool.execute(
            {
                "action": "get",
                "project": "test_proj",
                "name": "manga-action",
                "include": "full",
            }
        )

        assert result.success is True
        data = json.loads(result.output)
        assert "embedding" not in data
        assert "embedding_model" in data
        assert "embedding_dimensions" in data

    @pytest.mark.asyncio(loop_scope="function")
    async def test_list_styles_strips_embedding(
        self, service: ComicProjectService
    ) -> None:
        """ComicStyleTool list: no item in the list contains an 'embedding' key."""
        raw_entries = [
            {
                "name": "manga-action",
                "version": 1,
                "uri": "comic://proj/styles/manga-action?v=1",
                "embedding": [0.1, 0.2, 0.3, 0.4],
                "embedding_model": "gemini-embedding-2-preview",
                "embedding_dimensions": 4,
            },
            {
                "name": "superhero",
                "version": 1,
                "uri": "comic://proj/styles/superhero?v=1",
                "embedding": [0.5, 0.6, 0.7, 0.8],
                "embedding_model": "gemini-embedding-2-preview",
                "embedding_dimensions": 4,
            },
        ]
        service.list_styles = AsyncMock(return_value=raw_entries)  # type: ignore[method-assign]

        tool = ComicStyleTool(service)
        result = await tool.execute({"action": "list", "project": "test_proj"})

        assert result.success is True
        entries = json.loads(result.output)
        assert len(entries) == 2
        for entry in entries:
            assert "embedding" not in entry


# ===========================================================================
# TestSearchCharactersByDescription — cross-modal text search
# ===========================================================================


class TestSearchCharactersByDescription:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_matching_characters_with_embedded_status(
        self, service: ComicProjectService
    ) -> None:
        """Text query is embedded and matched against stored character embeddings; returns embedding_status='embedded'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        # Store two characters with embeddings
        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )
        await service.store_character(
            pid, iid, "Beta", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )

        result = await service.search_characters_by_description(
            pid, "a tall hero with blue eyes", top_k=5
        )

        assert "query_text" in result
        assert result["query_text"] == "a tall hero with blue eyes"
        assert "results" in result
        assert len(result["results"]) >= 1
        assert "embedding_status" in result
        assert result["embedding_status"] == "embedded"

        # Verify result fields
        for r in result["results"]:
            assert "uri" in r
            assert "name" in r
            assert "style" in r
            assert "similarity" in r
            assert "originating_project" in r

        # Verify sorted descending by similarity
        sims = [r["similarity"] for r in result["results"]]
        assert sims == sorted(sims, reverse=True)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_circuit_open_returns_empty_with_skipped_circuit_open(
        self, service: ComicProjectService
    ) -> None:
        """Open circuit breaker: returns empty results with embedding_status='skipped_circuit_open'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        # Trip the circuit breaker
        service._breaker.record_failure()
        service._breaker.record_failure()
        service._breaker.record_failure()
        assert service._breaker.state == "open"

        result = await service.search_characters_by_description(
            "some_project", "a tall hero with blue eyes"
        )

        assert result["query_text"] == "a tall hero with blue eyes"
        assert result["results"] == []
        assert result["embedding_status"] == "skipped_circuit_open"
        assert "message" in result

    @pytest.mark.asyncio(loop_scope="function")
    async def test_no_client_returns_empty_with_skipped_no_client(
        self, service: ComicProjectService
    ) -> None:
        """No embedding client: returns empty results with embedding_status='skipped_no_client'."""
        assert service._genai_client is None

        result = await service.search_characters_by_description(
            "some_project", "a tall hero with blue eyes"
        )

        assert result["query_text"] == "a tall hero with blue eyes"
        assert result["results"] == []
        assert result["embedding_status"] == "skipped_no_client"
        assert "message" in result

    @pytest.mark.asyncio(loop_scope="function")
    async def test_results_exclude_raw_embedding_vectors(
        self, service: ComicProjectService
    ) -> None:
        """Results must not contain raw embedding vectors."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        await service.store_character(
            pid, iid, "Alpha", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )
        await service.store_character(
            pid, iid, "Beta", "manga", **_CHAR_META, data=_PNG, compute_embedding=True
        )

        result = await service.search_characters_by_description(
            pid, "a tall hero with blue eyes", top_k=5
        )

        assert result["embedding_status"] == "embedded"
        assert len(result["results"]) >= 1

        for r in result["results"]:
            assert "embedding" not in r, (
                "Raw embedding vector must not appear in results"
            )


# ===========================================================================
# TestSearchAssetsByDescription — cross-modal text search for assets
# ===========================================================================


class TestSearchAssetsByDescription:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_matching_assets_with_embedded_status(
        self, service: ComicProjectService
    ) -> None:
        """Text query is embedded and matched against stored asset embeddings; returns embedding_status='embedded'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        # Store two panels with embeddings
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
            compute_embedding=True,
        )
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel02",
            data=_PNG,
            metadata={"prompt": "A villain looms"},
            compute_embedding=True,
        )

        result = await service.search_assets_by_description(
            pid, "a tall hero with blue eyes", top_k=5
        )

        assert "query_text" in result
        assert result["query_text"] == "a tall hero with blue eyes"
        assert "results" in result
        assert len(result["results"]) >= 1
        assert "embedding_status" in result
        assert result["embedding_status"] == "embedded"

        # Verify result fields
        for r in result["results"]:
            assert "uri" in r
            assert "name" in r
            assert "asset_type" in r
            assert "similarity" in r
            assert "issue_id" in r

        # Verify sorted descending by similarity
        sims = [r["similarity"] for r in result["results"]]
        assert sims == sorted(sims, reverse=True)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_no_client_returns_empty_with_skipped_no_client(
        self, service: ComicProjectService
    ) -> None:
        """No embedding client: returns empty results with embedding_status='skipped_no_client'."""
        assert service._genai_client is None

        result = await service.search_assets_by_description(
            "some_project", "a tall hero with blue eyes"
        )

        assert result["query_text"] == "a tall hero with blue eyes"
        assert result["results"] == []
        assert result["embedding_status"] == "skipped_no_client"
        assert "message" in result

    @pytest.mark.asyncio(loop_scope="function")
    async def test_asset_type_filter_narrows_results(
        self, service: ComicProjectService
    ) -> None:
        """asset_type filter: stores panel and cover, searches only panel type; cover not in results."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        pid, iid = await _new_issue(service)

        # Store a panel with embedding
        await service.store_asset(
            pid,
            iid,
            "panel",
            "panel01",
            data=_PNG,
            metadata={"prompt": "A hero stands tall"},
            compute_embedding=True,
        )
        # Store a cover with embedding
        await service.store_asset(
            pid,
            iid,
            "cover",
            "cover01",
            data=_PNG,
            metadata={"prompt": "Epic cover art"},
            compute_embedding=True,
        )

        # Search only for panels
        result = await service.search_assets_by_description(
            pid, "a hero standing", top_k=5, asset_type="panel"
        )

        assert result["embedding_status"] == "embedded"
        assert "results" in result

        # Verify all results are panels (no covers)
        result_types = [r["asset_type"] for r in result["results"]]
        assert "cover" not in result_types
        # Panel should be in results
        result_names = [r["name"] for r in result["results"]]
        assert "panel01" in result_names
        assert "cover01" not in result_names


# ===========================================================================
# TestSearchStylesByDescription — cross-modal text search for style guides
# ===========================================================================


class TestSearchStylesByDescription:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_matching_styles_with_embedded_status(
        self, service: ComicProjectService
    ) -> None:
        """Text query is embedded and matched against stored style embeddings; returns embedding_status='embedded'."""
        client = _make_embedding_client(dim=4)
        service.set_embedding_client(client, embedding_dim=4)

        r = await service.create_issue("test_project", "Issue 1")
        pid, iid = r["project_id"], r["issue_id"]

        definition = {
            "name": "Manga Action",
            "description": "Fast paced manga style",
            "aesthetic_direction": "bold lines",
            "color_palette": {"primary": "black", "secondary": "white"},
            "panel_conventions": "N/N/N panel grid",
        }

        # Store two styles with embeddings
        await service.store_style(pid, iid, "manga-action", definition, compute_embedding=True)
        await service.store_style(pid, iid, "superhero", definition, compute_embedding=True)

        result = await service.search_styles_by_description(
            pid, "fast paced bold manga", top_k=5
        )

        assert "query_text" in result
        assert result["query_text"] == "fast paced bold manga"
        assert "results" in result
        assert len(result["results"]) >= 1
        assert "embedding_status" in result
        assert result["embedding_status"] == "embedded"

        # Verify result fields
        for r in result["results"]:
            assert "uri" in r
            assert "name" in r
            assert "similarity" in r
            assert "originating_project" in r

        # Verify sorted descending by similarity
        sims = [r["similarity"] for r in result["results"]]
        assert sims == sorted(sims, reverse=True)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_no_client_returns_empty_with_skipped_no_client(
        self, service: ComicProjectService
    ) -> None:
        """No embedding client: returns empty results with embedding_status='skipped_no_client'."""
        assert service._genai_client is None

        result = await service.search_styles_by_description(
            "some_project", "fast paced bold manga"
        )

        assert result["query_text"] == "fast paced bold manga"
        assert result["results"] == []
        assert result["embedding_status"] == "skipped_no_client"
        assert "message" in result
