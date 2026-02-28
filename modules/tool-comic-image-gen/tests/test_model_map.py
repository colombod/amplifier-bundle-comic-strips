"""Tests for the model_map module — data integrity, distribution, and spot checks."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from amplifier_comic_image_gen.model_map import MODEL_MAP, ModelEntry


# ── Structure & immutability ─────────────────────────────────────────


class TestModelMapStructure:
    """Basic structural tests for MODEL_MAP and ModelEntry."""

    def test_model_map_has_exactly_12_entries(self) -> None:
        assert len(MODEL_MAP) == 12

    def test_all_entries_are_model_entry_instances(self) -> None:
        for key, entry in MODEL_MAP.items():
            assert isinstance(entry, ModelEntry), f"{key} is not a ModelEntry"

    def test_model_entry_is_frozen(self) -> None:
        """ModelEntry should be immutable (frozen dataclass)."""
        entry = next(iter(MODEL_MAP.values()))
        with pytest.raises(FrozenInstanceError):
            entry.provider = "hacked"  # type: ignore[misc]

    def test_all_keys_match_model_id(self) -> None:
        """Each dict key must equal the entry's model_id field."""
        for key, entry in MODEL_MAP.items():
            assert key == entry.model_id, f"Key {key!r} != model_id {entry.model_id!r}"

    def test_all_required_fields_present(self) -> None:
        """Every entry must have all nine fields populated."""
        required_fields = {
            "provider",
            "model_id",
            "api_surface",
            "cost_tier",
            "reference_images",
            "max_refs",
            "style_strengths",
            "detail_ceiling",
            "text_avoidance",
        }
        for key, entry in MODEL_MAP.items():
            actual = set(vars(entry).keys())
            assert required_fields.issubset(actual), (
                f"{key} missing fields: {required_fields - actual}"
            )


# ── Provider distribution ────────────────────────────────────────────


class TestProviderDistribution:
    """Verify the correct number of models per provider."""

    def test_five_openai_models(self) -> None:
        openai = [e for e in MODEL_MAP.values() if e.provider == "openai"]
        assert len(openai) == 5

    def test_seven_google_models(self) -> None:
        google = [e for e in MODEL_MAP.values() if e.provider == "google"]
        assert len(google) == 7


# ── API surface distribution ─────────────────────────────────────────


class TestAPISurfaceDistribution:
    """Verify the correct number of models per API surface."""

    def test_five_openai_images_surface(self) -> None:
        count = sum(1 for e in MODEL_MAP.values() if e.api_surface == "openai-images")
        assert count == 5

    def test_four_gemini_generate_content_surface(self) -> None:
        count = sum(
            1 for e in MODEL_MAP.values() if e.api_surface == "gemini-generate-content"
        )
        assert count == 4

    def test_three_gemini_generate_images_surface(self) -> None:
        count = sum(
            1 for e in MODEL_MAP.values() if e.api_surface == "gemini-generate-images"
        )
        assert count == 3

    def test_api_surfaces_are_only_valid_values(self) -> None:
        valid = {"openai-images", "gemini-generate-content", "gemini-generate-images"}
        for key, entry in MODEL_MAP.items():
            assert entry.api_surface in valid, (
                f"{key} has invalid api_surface: {entry.api_surface!r}"
            )


# ── Reference image support ─────────────────────────────────────────


class TestReferenceImages:
    """Verify reference_images and max_refs constraints per spec."""

    def test_gpt_image_1x_models_support_refs_with_16_max(self) -> None:
        gpt1x = {k: v for k, v in MODEL_MAP.items() if k.startswith("gpt-image-1")}
        assert len(gpt1x) == 3, "Expected 3 gpt-image-1.x models"
        for key, entry in gpt1x.items():
            assert entry.reference_images is True, f"{key} should support refs"
            assert entry.max_refs == 16, f"{key} should have max_refs=16"

    def test_dall_e_3_no_reference_images(self) -> None:
        entry = MODEL_MAP["dall-e-3"]
        assert entry.reference_images is False

    def test_dall_e_2_supports_refs_with_1_max(self) -> None:
        entry = MODEL_MAP["dall-e-2"]
        assert entry.reference_images is True
        assert entry.max_refs == 1

    def test_gemini_content_models_support_refs_with_10_max(self) -> None:
        gemini_content = [
            e for e in MODEL_MAP.values() if e.api_surface == "gemini-generate-content"
        ]
        for entry in gemini_content:
            assert entry.reference_images is True, (
                f"{entry.model_id} should support refs"
            )
            assert entry.max_refs == 10, f"{entry.model_id} should have max_refs=10"

    def test_imagen_models_no_reference_images(self) -> None:
        imagen = [
            e for e in MODEL_MAP.values() if e.api_surface == "gemini-generate-images"
        ]
        assert len(imagen) == 3
        for entry in imagen:
            assert entry.reference_images is False, (
                f"{entry.model_id} should not support refs"
            )
            assert entry.max_refs == 0, f"{entry.model_id} should have max_refs=0"


# ── Cost tier validation ─────────────────────────────────────────────


class TestCostTier:
    """Verify cost_tier constraints."""

    def test_all_cost_tiers_in_range_1_to_5(self) -> None:
        for key, entry in MODEL_MAP.items():
            assert 1 <= entry.cost_tier <= 5, (
                f"{key} cost_tier={entry.cost_tier} out of range"
            )

    def test_imagen_fast_is_cheapest(self) -> None:
        entry = MODEL_MAP["imagen-4.0-fast-generate-001"]
        assert entry.cost_tier == 1

    def test_gpt_image_1_5_is_most_expensive(self) -> None:
        entry = MODEL_MAP["gpt-image-1.5"]
        assert entry.cost_tier == 5


# ── Detail ceiling validation ────────────────────────────────────────


class TestDetailCeiling:
    """Verify detail_ceiling constraints."""

    def test_all_detail_ceilings_are_valid(self) -> None:
        valid = {"low", "medium", "high", "ultra"}
        for key, entry in MODEL_MAP.items():
            assert entry.detail_ceiling in valid, (
                f"{key} has invalid detail_ceiling: {entry.detail_ceiling!r}"
            )

    def test_gpt_image_1_5_has_ultra_ceiling(self) -> None:
        assert MODEL_MAP["gpt-image-1.5"].detail_ceiling == "ultra"


# ── Text avoidance validation ────────────────────────────────────────


class TestTextAvoidance:
    """Verify text_avoidance constraints."""

    def test_all_text_avoidance_are_valid(self) -> None:
        valid = {"poor", "fair", "good", "excellent"}
        for key, entry in MODEL_MAP.items():
            assert entry.text_avoidance in valid, (
                f"{key} has invalid text_avoidance: {entry.text_avoidance!r}"
            )


# ── Spot-check specific models ──────────────────────────────────────


class TestSpotChecks:
    """Spot-check individual model entries for overall correctness."""

    def test_gpt_image_1_5_spot_check(self) -> None:
        e = MODEL_MAP["gpt-image-1.5"]
        assert e.provider == "openai"
        assert e.api_surface == "openai-images"
        assert e.cost_tier == 5
        assert e.reference_images is True
        assert e.max_refs == 16
        assert e.detail_ceiling == "ultra"

    def test_dall_e_3_spot_check(self) -> None:
        e = MODEL_MAP["dall-e-3"]
        assert e.provider == "openai"
        assert e.api_surface == "openai-images"
        assert e.reference_images is False

    def test_imagen_4_ultra_spot_check(self) -> None:
        e = MODEL_MAP["imagen-4.0-ultra-generate-001"]
        assert e.provider == "google"
        assert e.api_surface == "gemini-generate-images"
        assert e.reference_images is False
        assert e.max_refs == 0

    def test_gemini_2_0_flash_spot_check(self) -> None:
        e = MODEL_MAP["gemini-2.0-flash"]
        assert e.provider == "google"
        assert e.api_surface == "gemini-generate-content"
        assert e.reference_images is True
        assert e.max_refs == 10
