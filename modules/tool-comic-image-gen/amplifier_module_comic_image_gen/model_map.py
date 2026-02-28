"""Model registry for comic image generation backends.

Maps every supported image-generation model to its capabilities so the
router can pick the best model for a given request.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ApiSurface = Literal[
    "openai-images", "gemini-generate-content", "gemini-generate-images"
]
DetailCeiling = Literal["low", "medium", "high", "ultra"]
TextAvoidance = Literal["poor", "fair", "good", "excellent"]


@dataclass(frozen=True)
class ModelEntry:
    """Immutable descriptor for a single image-generation model."""

    provider: str
    model_id: str
    api_surface: ApiSurface
    cost_tier: int  # 1 (cheapest) .. 5 (most expensive)
    reference_images: bool
    max_refs: int
    style_strengths: tuple[str, ...]
    detail_ceiling: DetailCeiling
    text_avoidance: TextAvoidance


MODEL_MAP: dict[str, ModelEntry] = {
    # ── OpenAI models (5) ────────────────────────────────────────────
    "gpt-image-1.5": ModelEntry(
        provider="openai",
        model_id="gpt-image-1.5",
        api_surface="openai-images",
        cost_tier=5,
        reference_images=True,
        max_refs=16,
        style_strengths=("photorealistic", "illustration", "comic", "abstract"),
        detail_ceiling="ultra",
        text_avoidance="excellent",
    ),
    "gpt-image-1": ModelEntry(
        provider="openai",
        model_id="gpt-image-1",
        api_surface="openai-images",
        cost_tier=4,
        reference_images=True,
        max_refs=16,
        style_strengths=("photorealistic", "illustration", "comic"),
        detail_ceiling="high",
        text_avoidance="good",
    ),
    "gpt-image-1-mini": ModelEntry(
        provider="openai",
        model_id="gpt-image-1-mini",
        api_surface="openai-images",
        cost_tier=3,
        reference_images=True,
        max_refs=16,
        style_strengths=("illustration", "comic"),
        detail_ceiling="medium",
        text_avoidance="good",
    ),
    "dall-e-3": ModelEntry(
        provider="openai",
        model_id="dall-e-3",
        api_surface="openai-images",
        cost_tier=3,
        reference_images=False,
        max_refs=0,
        style_strengths=("photorealistic", "illustration"),
        detail_ceiling="high",
        text_avoidance="fair",
    ),
    "dall-e-2": ModelEntry(
        provider="openai",
        model_id="dall-e-2",
        api_surface="openai-images",
        cost_tier=2,
        reference_images=True,
        max_refs=1,
        style_strengths=("illustration",),
        detail_ceiling="medium",
        text_avoidance="poor",
    ),
    # ── Google Gemini generateContent models (4) ─────────────────────
    "gemini-3-pro-image-preview": ModelEntry(
        provider="google",
        model_id="gemini-3-pro-image-preview",
        api_surface="gemini-generate-content",
        cost_tier=4,
        reference_images=True,
        max_refs=10,
        style_strengths=("photorealistic", "illustration", "comic"),
        detail_ceiling="high",
        text_avoidance="good",
    ),
    "gemini-3.1-flash-image-preview": ModelEntry(
        provider="google",
        model_id="gemini-3.1-flash-image-preview",
        api_surface="gemini-generate-content",
        cost_tier=3,
        reference_images=True,
        max_refs=10,
        style_strengths=("illustration", "comic"),
        detail_ceiling="high",
        text_avoidance="good",
    ),
    "gemini-2.5-flash-image": ModelEntry(
        provider="google",
        model_id="gemini-2.5-flash-image",
        api_surface="gemini-generate-content",
        cost_tier=2,
        reference_images=True,
        max_refs=10,
        style_strengths=("illustration", "comic"),
        detail_ceiling="medium",
        text_avoidance="fair",
    ),
    "gemini-2.0-flash": ModelEntry(
        provider="google",
        model_id="gemini-2.0-flash",
        api_surface="gemini-generate-content",
        cost_tier=2,
        reference_images=True,
        max_refs=10,
        style_strengths=("illustration",),
        detail_ceiling="medium",
        text_avoidance="fair",
    ),
    # ── Google Imagen generateImages models (3) ──────────────────────
    "imagen-4.0-ultra-generate-001": ModelEntry(
        provider="google",
        model_id="imagen-4.0-ultra-generate-001",
        api_surface="gemini-generate-images",
        cost_tier=4,
        reference_images=False,
        max_refs=0,
        style_strengths=("photorealistic", "illustration"),
        detail_ceiling="high",
        text_avoidance="good",
    ),
    "imagen-4.0-generate-001": ModelEntry(
        provider="google",
        model_id="imagen-4.0-generate-001",
        api_surface="gemini-generate-images",
        cost_tier=2,
        reference_images=False,
        max_refs=0,
        style_strengths=("photorealistic", "illustration"),
        detail_ceiling="high",
        text_avoidance="good",
    ),
    "imagen-4.0-fast-generate-001": ModelEntry(
        provider="google",
        model_id="imagen-4.0-fast-generate-001",
        api_surface="gemini-generate-images",
        cost_tier=1,
        reference_images=False,
        max_refs=0,
        style_strengths=("illustration",),
        detail_ceiling="medium",
        text_avoidance="fair",
    ),
}
