"""Tests for model_selector — core selection algorithm."""

from __future__ import annotations

from amplifier_comic_image_gen.model_selector import SelectionResult, select_model


# ── SelectionResult dataclass ──────────────────────────────────────────


class TestSelectionResultDataclass:
    """SelectionResult is a proper dataclass with expected fields."""

    def test_has_all_expected_fields(self) -> None:
        r = SelectionResult(
            model_id="m", provider="p", api_surface="a", cost_tier=1, rationale="r"
        )
        assert r.model_id == "m"
        assert r.provider == "p"
        assert r.api_surface == "a"
        assert r.cost_tier == 1
        assert r.rationale == "r"

    def test_none_fields_allowed(self) -> None:
        r = SelectionResult(
            model_id=None,
            provider=None,
            api_surface=None,
            cost_tier=None,
            rationale="r",
        )
        assert r.model_id is None
        assert r.provider is None
        assert r.api_surface is None
        assert r.cost_tier is None


# ── Basic selection ────────────────────────────────────────────────────


class TestBasicSelection:
    """Verify basic happy-path selection behavior."""

    def test_returns_selection_result_type(self) -> None:
        result = select_model(available_providers=["openai", "google"])
        assert isinstance(result, SelectionResult)

    def test_no_providers_returns_none_model(self) -> None:
        result = select_model(available_providers=[])
        assert result.model_id is None
        assert "no providers" in result.rationale.lower()

    def test_cheapest_model_no_constraints(self) -> None:
        """With both providers and no constraints, cheapest model (tier 1) selected."""
        result = select_model(available_providers=["openai", "google"])
        assert result.model_id == "imagen-4.0-fast-generate-001"
        assert result.cost_tier == 1


# ── Explicit model override ───────────────────────────────────────────


class TestExplicitModelOverride:
    """Explicit model bypasses all filtering logic."""

    def test_explicit_known_model(self) -> None:
        result = select_model(
            available_providers=["openai"],
            explicit_model="gpt-image-1.5",
        )
        assert result.model_id == "gpt-image-1.5"
        assert result.provider == "openai"
        assert result.api_surface == "openai-images"

    def test_explicit_unknown_model_trusted(self) -> None:
        result = select_model(
            available_providers=["openai"],
            explicit_model="my-custom-model",
        )
        assert result.model_id == "my-custom-model"
        assert result.provider is None

    def test_explicit_model_ignores_empty_providers(self) -> None:
        """Explicit model works even when no providers available."""
        result = select_model(
            available_providers=[],
            explicit_model="gpt-image-1",
        )
        assert result.model_id == "gpt-image-1"


# ── Reference image filtering ─────────────────────────────────────────


class TestReferenceImageFiltering:
    """needs_reference_images=True filters out non-ref models."""

    def test_needs_refs_excludes_dalle3_and_imagen(self) -> None:
        result = select_model(
            available_providers=["openai", "google"],
            needs_reference_images=True,
        )
        # Result must NOT be dall-e-3 or any imagen model
        assert result.model_id not in (
            "dall-e-3",
            "imagen-4.0-ultra-generate-001",
            "imagen-4.0-generate-001",
            "imagen-4.0-fast-generate-001",
        )

    def test_needs_refs_cheapest_ref_model(self) -> None:
        """Cheapest ref-capable model is dall-e-2 (tier 2)."""
        result = select_model(
            available_providers=["openai", "google"],
            needs_reference_images=True,
        )
        assert result.model_id == "dall-e-2"
        assert result.cost_tier == 2


# ── Style category matching ───────────────────────────────────────────


class TestStyleCategoryMatching:
    """Style category filters to models with matching style_strengths."""

    def test_style_comic_selects_comic_model(self) -> None:
        result = select_model(
            available_providers=["openai", "google"],
            style_category="comic",
        )
        # Cheapest comic model is gemini-2.5-flash-image (tier 2)
        assert result.model_id == "gemini-2.5-flash-image"

    def test_style_photorealistic_selects_cheapest_photo_model(self) -> None:
        result = select_model(
            available_providers=["openai", "google"],
            style_category="photorealistic",
        )
        # Cheapest photorealistic model is imagen-4.0-generate-001 (tier 2)
        assert result.model_id == "imagen-4.0-generate-001"

    def test_unknown_style_fallback_keeps_all(self) -> None:
        """Unknown style falls back to all models — cheapest overall picked."""
        result = select_model(
            available_providers=["openai", "google"],
            style_category="watercolor",
        )
        assert result.model_id == "imagen-4.0-fast-generate-001"
        assert result.cost_tier == 1


# ── Detail level filtering ────────────────────────────────────────────


class TestDetailLevelFiltering:
    """detail_level filters by detail_ceiling rank."""

    def test_detail_high_excludes_dall_e_2(self) -> None:
        """dall-e-2 (medium ceiling) excluded when detail=high."""
        result = select_model(
            available_providers=["openai"],
            detail_level="high",
        )
        assert result.model_id != "dall-e-2"
        # Cheapest openai model with high+ ceiling is dall-e-3 (tier 3)
        assert result.model_id == "dall-e-3"

    def test_detail_ultra_selects_gpt_image_15(self) -> None:
        """Only gpt-image-1.5 has ultra ceiling."""
        result = select_model(
            available_providers=["openai", "google"],
            detail_level="ultra",
        )
        assert result.model_id == "gpt-image-1.5"

    def test_detail_low_includes_all(self) -> None:
        """All models have at least medium ceiling — low includes everything."""
        result = select_model(
            available_providers=["openai", "google"],
            detail_level="low",
        )
        # Same as no constraint — cheapest overall
        assert result.model_id == "imagen-4.0-fast-generate-001"


# ── Fallback behavior ─────────────────────────────────────────────────


class TestFallbackBehavior:
    """Fallback relaxes filters when no exact match exists."""

    def test_style_fallback_no_google_abstract(self) -> None:
        """No google model has 'abstract' — fallback keeps all google models."""
        result = select_model(
            available_providers=["google"],
            style_category="abstract",
        )
        # Fallback to cheapest google model: imagen-4.0-fast (tier 1)
        assert result.model_id == "imagen-4.0-fast-generate-001"

    def test_detail_fallback_no_google_ultra(self) -> None:
        """No google model has ultra ceiling — fallback keeps all google models."""
        result = select_model(
            available_providers=["google"],
            detail_level="ultra",
        )
        assert result.model_id == "imagen-4.0-fast-generate-001"


# ── Cost minimization ─────────────────────────────────────────────────


class TestCostMinimization:
    """Selection always picks cheapest viable model."""

    def test_cheapest_viable_no_constraints(self) -> None:
        result = select_model(available_providers=["openai", "google"])
        assert result.cost_tier is not None
        assert result.cost_tier <= 2


# ── Combined requirement scenarios ────────────────────────────────────


class TestCombinedScenarios:
    """Real-world scenarios combining multiple requirements."""

    def test_panel_gen_refs_manga_medium(self) -> None:
        """Panel generation: refs + manga style + medium detail."""
        result = select_model(
            available_providers=["openai", "google"],
            needs_reference_images=True,
            style_category="manga",
            detail_level="medium",
        )
        assert result.model_id is not None
        # manga doesn't match → fallback; medium keeps all refs; cheapest ref = dall-e-2
        assert result.model_id == "dall-e-2"

    def test_cover_gen_refs_superhero_high(self) -> None:
        """Cover generation: refs + superhero style + high detail."""
        result = select_model(
            available_providers=["openai", "google"],
            needs_reference_images=True,
            style_category="superhero",
            detail_level="high",
        )
        assert result.model_id is not None
        # superhero doesn't match → fallback; high excludes medium-ceiling refs
        # Remaining: gpt-image-1(4), gpt-image-1.5(5), gemini-3-pro(4), gemini-3.1-flash(3)
        assert result.model_id == "gemini-3.1-flash-image-preview"

    def test_character_design_refs_comic(self) -> None:
        """Character design: refs + comic style."""
        result = select_model(
            available_providers=["openai", "google"],
            needs_reference_images=True,
            style_category="comic",
        )
        assert result.model_id is not None
        # Comic ref models: cheapest is gemini-2.5-flash-image (tier 2)
        assert result.model_id == "gemini-2.5-flash-image"
