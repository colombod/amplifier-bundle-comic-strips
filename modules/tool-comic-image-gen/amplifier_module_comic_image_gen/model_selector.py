"""Core model selection algorithm for comic image generation.

Picks the cheapest viable model from MODEL_MAP based on provider
availability, reference-image needs, style category, and detail level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .model_map import MODEL_MAP, ApiSurface, ModelEntry

_DETAIL_RANK: Final[dict[str, int]] = {"low": 1, "medium": 2, "high": 3, "ultra": 4}
_COMPOSITION_RANK: Final[dict[str, int]] = {
    "poor": 1,
    "fair": 2,
    "good": 3,
    "excellent": 4,
}

# Maps Amplifier canonical provider names to MODEL_MAP provider names
_PROVIDER_NORMALIZER: Final[dict[str, str]] = {
    "gemini": "google",
    "azure-openai": "openai",
}


@dataclass(frozen=True)
class SelectionResult:
    """Outcome of a model selection request."""

    model_id: str | None
    provider: str | None
    api_surface: ApiSurface | None
    cost_tier: int | None
    rationale: str


def select_model(
    *,
    available_providers: list[str],
    needs_reference_images: bool = False,
    style_category: str | None = None,
    detail_level: str | None = None,
    explicit_model: str | None = None,
    task_hint: str | None = None,
) -> SelectionResult:
    """Select the best model for the given requirements.

    Parameters
    ----------
    task_hint:
        Optional hint about the *kind* of image work being done.
        Currently recognised values:

        * ``"composition"`` — multi-element scenes, panel framing,
          negative-space planning, cover layouts.  Biases selection
          toward models with strong spatial reasoning (e.g.
          gemini-3-pro-image-preview, rated "Nano Banana Pro" by
          StrongDM Weather Report for UX Ideation).
        * ``None`` (default) — no bias; cheapest viable model wins.

        Unknown hints are silently ignored (future-proof).

    Returns a :class:`SelectionResult` with the chosen model's details,
    or ``model_id=None`` when no viable model exists.
    """

    # (1) Explicit override — bypass all logic
    if explicit_model is not None:
        entry = MODEL_MAP.get(explicit_model)
        if entry is not None:
            return SelectionResult(
                model_id=entry.model_id,
                provider=entry.provider,
                api_surface=entry.api_surface,
                cost_tier=entry.cost_tier,
                rationale="explicit model override",
            )
        return SelectionResult(
            model_id=explicit_model,
            provider=None,
            api_surface=None,
            cost_tier=None,
            rationale="explicit model override (unknown model)",
        )

    # (2) No providers — nothing to do
    if not available_providers:
        return SelectionResult(
            model_id=None,
            provider=None,
            api_surface=None,
            cost_tier=None,
            rationale="no providers available",
        )

    # (3) Filter by available providers
    normalized_providers = [_PROVIDER_NORMALIZER.get(p, p) for p in available_providers]
    candidates: list[ModelEntry] = [
        e for e in MODEL_MAP.values() if e.provider in normalized_providers
    ]

    if not candidates:
        return SelectionResult(
            model_id=None,
            provider=None,
            api_surface=None,
            cost_tier=None,
            rationale="no models match available providers",
        )

    # (4) Reference-image filter (with fallback)
    if needs_reference_images:
        filtered = [e for e in candidates if e.reference_images]
        if filtered:
            candidates = filtered

    # (5) Style-category filter (with fallback)
    if style_category is not None:
        filtered = [e for e in candidates if style_category in e.style_strengths]
        if filtered:
            candidates = filtered

    # (6) Detail-level filter (with fallback)
    if detail_level is not None:
        # Unknown detail levels default to rank 0 (least restrictive),
        # so unrecognised values effectively skip the filter.
        required_rank = _DETAIL_RANK.get(detail_level, 0)
        filtered = [
            e
            for e in candidates
            if _DETAIL_RANK.get(e.detail_ceiling, 0) >= required_rank
        ]
        if filtered:
            candidates = filtered

    # (7) Task-hint bias — prefer models strong at the requested task
    #     This is a *soft* preference: it re-sorts among viable candidates
    #     rather than filtering.  The cheapest-viable tiebreaker still
    #     applies within each composition tier.
    if task_hint == "composition":
        # Sort by composition_strength DESC, then cost ASC, then model_id
        candidates.sort(
            key=lambda e: (
                -_COMPOSITION_RANK.get(e.composition_strength, 0),
                e.cost_tier,
                e.model_id,
            )
        )
        winner = candidates[0]
        comp = winner.composition_strength
        return SelectionResult(
            model_id=winner.model_id,
            provider=winner.provider,
            api_surface=winner.api_surface,
            cost_tier=winner.cost_tier,
            rationale=f"best composition model ({comp}, tier {winner.cost_tier})",
        )

    # (8) Default: sort by cost ascending, pick cheapest (model_id breaks ties)
    candidates.sort(key=lambda e: (e.cost_tier, e.model_id))
    winner = candidates[0]

    return SelectionResult(
        model_id=winner.model_id,
        provider=winner.provider,
        api_surface=winner.api_surface,
        cost_tier=winner.cost_tier,
        rationale=f"cheapest viable model (tier {winner.cost_tier})",
    )
