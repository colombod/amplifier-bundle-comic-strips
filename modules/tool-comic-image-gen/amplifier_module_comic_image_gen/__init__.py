"""Comic image generation tool — BRIDGE MODULE for Issue #90.

Exposes a ``generate_image`` tool that delegates to provider-specific
image backends (OpenAI, Gemini).  The tool is registered via :func:`mount`
which the Amplifier module loader calls at startup.

This entire module is a *bridge* — it exists only because the kernel does
not yet have a first-class image-generation capability.  Remove it once
Issue #90 lands a native solution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

try:
    from amplifier_core.models import ToolResult  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover – bridge runs without amplifier_core in tests

    @dataclass
    class ToolResult:  # type: ignore[no-redef]
        """Minimal stand-in used when amplifier_core is not installed."""

        success: bool = False
        output: Any = ""


from ._version import __version__  # noqa: F401, E402
from .model_map import MODEL_MAP  # noqa: E402
from .model_selector import select_model  # noqa: E402
from .providers import discover_image_backends  # noqa: E402

# Maps user-facing provider names (from preferred_provider param and MODEL_MAP)
# to the backend provider_type values used for direct routing.
_PROVIDER_TO_BACKEND_TYPE: dict[str, str] = {
    "openai": "openai",
    "google": "gemini",
}

__amplifier_module_type__ = "tool"

__all__ = ["mount", "ComicImageGenTool"]


class ComicImageGenTool:
    """Bridge tool that generates images from text prompts (Issue #90).

    Wraps one or more image-generation backends (OpenAI, Gemini) behind a
    unified ``generate_image`` tool interface so the agent can request
    images without knowing which provider fulfills the request.
    """

    def __init__(self, backends: list[Any]) -> None:
        self._backends = list(backends)

    # ── Tool protocol properties ─────────────────────────────────

    @property
    def name(self) -> str:
        return "generate_image"

    @property
    def description(self) -> str:
        return (
            "Generate an image from a text prompt using an available "
            "image-capable provider. Bridge tool for Issue #90."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description of the image to generate.",
                },
                "output_path": {
                    "type": "string",
                    "description": "File path where the generated image will be saved.",
                },
                "preferred_provider": {
                    "type": "string",
                    "description": "Preferred image provider.",
                    "enum": ["openai", "google"],
                },
                "size": {
                    "type": "string",
                    "description": "Image aspect ratio.",
                    "default": "square",
                    "enum": ["landscape", "portrait", "square"],
                },
                "style": {
                    "type": "string",
                    "description": "Image style (DALL-E only).",
                },
                "reference_images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File paths to character reference images for visual consistency.",
                },
                "model": {
                    "type": "string",
                    "description": "Explicit model ID override, bypasses auto-selection.",
                },
                "requirements": {
                    "type": "object",
                    "description": "Generation requirements for model selection.",
                    "properties": {
                        "needs_reference_images": {
                            "type": "boolean",
                            "description": "Whether the generation needs reference image support.",
                        },
                        "style_category": {
                            "type": "string",
                            "description": "Style category for the image.",
                        },
                        "detail_level": {
                            "type": "string",
                            "description": "Level of detail required.",
                            "enum": ["low", "medium", "high", "ultra"],
                        },
                    },
                },
            },
            "required": ["prompt", "output_path"],
        }

    # ── Execution ────────────────────────────────────────────────

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Run the image generation tool."""
        # Validate required parameters
        missing = [k for k in ("prompt", "output_path") if k not in params]
        if missing:
            return ToolResult(
                success=False,
                output=f"Missing required parameters: {', '.join(missing)}",
            )

        prompt: str = params["prompt"]
        output_path: str = params["output_path"]
        size: str = params.get("size", "square")
        style: str | None = params.get("style")
        reference_images: list[str] | None = params.get("reference_images")
        preferred_provider: str | None = params.get("preferred_provider")
        explicit_model: str | None = params.get("model")
        requirements: dict[str, Any] | None = params.get("requirements")

        backends = list(self._backends)

        if not backends:
            return ToolResult(
                success=False,
                output="No image-capable providers available. Configure an OpenAI or Google provider.",
            )

        # Direct lookup map: provider_type → backend instance (O(1) routing).
        backend_by_type: dict[str, Any] = {
            getattr(b, "provider_type", ""): b
            for b in backends
            if getattr(b, "provider_type", "")
        }

        gen_kwargs: dict[str, Any] = {
            "prompt": prompt,
            "output_path": output_path,
            "size": size,
            "style": style,
            "reference_images": reference_images,
        }

        # Resolve which backend provider_type to target.
        # Later assignments override earlier ones, so explicit_model / requirements
        # take precedence over preferred_provider.
        target_type: str | None = None
        if preferred_provider:
            target_type = _PROVIDER_TO_BACKEND_TYPE.get(preferred_provider.lower())

        if explicit_model is not None:
            gen_kwargs["model"] = explicit_model
            entry = MODEL_MAP.get(explicit_model)
            if entry is not None:
                target_type = _PROVIDER_TO_BACKEND_TYPE.get(entry.provider)
        elif requirements is not None:
            available_providers: list[str] = []
            for b in backends:
                if hasattr(b, "provider_type"):
                    available_providers.append(b.provider_type)
                else:
                    logger.warning(
                        "generate_image: backend %s has no provider_type — "
                        "excluded from model selection",
                        type(b).__name__,
                    )
            selection = select_model(
                available_providers=available_providers,
                needs_reference_images=requirements.get(
                    "needs_reference_images", False
                ),
                style_category=requirements.get("style_category"),
                detail_level=requirements.get("detail_level"),
            )
            if selection.model_id is not None:
                gen_kwargs["model"] = selection.model_id
            if selection.provider is not None:
                target_type = _PROVIDER_TO_BACKEND_TYPE.get(selection.provider)

        # Build ordered backend list: target provider first, others as fallback.
        target = backend_by_type.get(target_type) if target_type is not None else None
        ordered_backends = (
            [target, *(b for b in backends if b is not target)]
            if target is not None
            else backends
        )

        errors: list[str] = []
        for backend in ordered_backends:
            result = await backend.generate(**gen_kwargs)
            if result["success"]:
                return ToolResult(success=True, output=result)
            errors.append(f"{backend.provider.name}: {result['error']}")

        return ToolResult(
            success=False,
            output=f"All image backends failed: {errors}",
        )


# ── Module mount point ───────────────────────────────────────────


async def mount(coordinator: Any, config: Any = None) -> None:
    """Amplifier module entry point — discover backends and register tool.

    Note: the kernel's module validator calls ``mount()`` once with an empty
    ``TestCoordinator`` (protocol compliance dry-run) before the real mount.
    During validation the coordinator has no providers, tools, or orchestrator
    — this is expected and we skip provider discovery in that context.
    """
    import logging

    _log = logging.getLogger(__name__)

    # The kernel validator uses a TestCoordinator with no providers.
    # Detect this by checking if the coordinator type name contains "Test"
    # or if no orchestrator has been mounted yet (real sessions always have
    # orchestrator mounted before tools).
    is_validation = not coordinator.get("orchestrator")

    providers: dict[str, Any] = coordinator.get("providers") or {}

    if is_validation:
        # Validation dry-run — mount with no backends, skip discovery.
        _log.debug("generate_image: validation mount (no providers expected)")
        backends: list[Any] = []
    else:
        backends = discover_image_backends(providers)
        if backends:
            _log.info(
                "generate_image: discovered %d image backend(s): %s",
                len(backends),
                [type(b).__name__ for b in backends],
            )
        else:
            _log.warning(
                "generate_image: no image backends discovered from %d "
                "coordinator providers (keys: %s). The generate_image tool "
                "will not be able to generate images.",
                len(providers),
                list(providers.keys()),
            )

    tool = ComicImageGenTool(backends)
    await coordinator.mount("tools", tool, name=tool.name)
