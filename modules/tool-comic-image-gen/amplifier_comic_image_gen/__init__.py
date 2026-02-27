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

logger = logging.getLogger(__name__)


class ComicImageGenTool:
    """Bridge tool that generates images from text prompts (Issue #90).

    Wraps one or more image-generation backends (OpenAI, Gemini) behind a
    unified ``generate_image`` tool interface so the agent can request
    images without knowing which provider fulfills the request.
    """

    def __init__(self, backends: list[Any], working_dir: str = ".") -> None:
        self._backends = list(backends)
        self._working_dir = working_dir

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
                    "description": "Image dimensions.",
                    "default": "1024x1024",
                    "enum": ["1024x1024", "1792x1024", "1024x1792"],
                },
                "style": {
                    "type": "string",
                    "description": "Image style (DALL-E only).",
                },
            },
            "required": ["prompt", "output_path"],
        }

    # ── Execution ────────────────────────────────────────────────

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        """Run the image generation tool."""
        # Validate required parameters
        missing = [k for k in ("prompt", "output_path") if k not in input]
        if missing:
            return ToolResult(
                success=False,
                output=f"Missing required parameters: {', '.join(missing)}",
            )

        prompt: str = input["prompt"]
        output_path: str = input["output_path"]
        size: str = input.get("size", "1024x1024")
        style: str | None = input.get("style")
        preferred_provider: str | None = input.get("preferred_provider")

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

        errors: list[str] = []
        for backend in backends:
            result = await backend.generate(prompt, output_path, size, style)
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
    working_dir: str = "."
    if config and hasattr(config, "get") and config.get("working_dir"):
        working_dir = config["working_dir"]
    else:
        try:
            working_dir = coordinator.get_capability("session.working_dir") or "."
        except Exception:
            pass

    providers: dict[str, Any] = coordinator.get("providers") or {}
    backends = discover_image_backends(providers)
    tool = ComicImageGenTool(backends, working_dir)
    await coordinator.mount("tools", tool, name=tool.name)
