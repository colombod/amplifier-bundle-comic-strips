"""Comic image generation tool — BRIDGE MODULE for Issue #90.

Exposes a ``generate_image`` tool that delegates to provider-specific
image backends (OpenAI, Gemini).  The tool is registered via :func:`mount`
which the Amplifier module loader calls at startup.

This entire module is a *bridge* — it exists only because the kernel does
not yet have a first-class image-generation capability.  Remove it once
Issue #90 lands a native solution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from amplifier_core.models import ToolResult
except ImportError:  # pragma: no cover – bridge runs without amplifier_core in tests

    @dataclass
    class ToolResult:  # type: ignore[no-redef]
        """Minimal stand-in used when amplifier_core is not installed."""

        success: bool = False
        output: Any = ""


from ._version import __version__  # noqa: F401
from .providers import discover_image_backends

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

        backends = list(self._backends)

        # Sort backends so the preferred provider comes first
        if preferred_provider and len(backends) > 1:
            pref = preferred_provider.lower()
            backends.sort(key=lambda b: pref not in b.provider.name.lower())

        if not backends:
            return ToolResult(
                success=False,
                output="No image-capable providers available. Configure an OpenAI or Google provider.",
            )

        gen_kwargs: dict[str, Any] = {
            "prompt": prompt,
            "output_path": output_path,
            "size": size,
            "style": style,
            "reference_images": reference_images,
        }
        if explicit_model is not None:
            gen_kwargs["model"] = explicit_model

        errors: list[str] = []
        for backend in backends:
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
    """Amplifier module entry point — discover backends and register tool."""
    import logging

    _log = logging.getLogger(__name__)

    providers: dict[str, Any] = coordinator.get("providers") or {}

    # Diagnostic: show what providers the coordinator exposes
    if providers:
        _log.info(
            "generate_image: coordinator providers available: %s",
            list(providers.keys()),
        )
        for pname, pobj in providers.items():
            obj_name = getattr(pobj, "name", None)
            _log.info(
                "  provider key=%r  .name=%r  type=%s",
                pname,
                obj_name,
                type(pobj).__name__,
            )
    else:
        _log.warning(
            "generate_image: coordinator.get('providers') returned empty or None"
        )

    backends = discover_image_backends(providers)

    if backends:
        _log.info(
            "generate_image: discovered %d image backend(s): %s",
            len(backends),
            [type(b).__name__ for b in backends],
        )
    else:
        provider_keys = list(providers.keys())
        msg = (
            "Comic strip generation requires an image-generation provider (OpenAI or Google/Gemini), "
            "but none were found. "
            + (
                f"Configured provider keys {provider_keys!r} did not match 'openai', 'google', or 'gemini'."
                if provider_keys
                else "No providers are configured. Add an OpenAI or Google provider to your settings."
            )
            + " Comics cannot be created without image generation access."
        )
        _log.error("generate_image: %s", msg)
        raise RuntimeError(msg)

    tool = ComicImageGenTool(backends)
    await coordinator.mount("tools", tool, name=tool.name)
