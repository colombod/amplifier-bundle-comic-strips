"""CRITICAL: Verify tool mount order in the behavior YAML.

Mount order matters for two reasons:
1. tool-comic-create.mount() looks up generate_image from already-mounted tools.
   If tool-comic-image-gen isn't listed before tool-comic-create, image_gen will
   always be None and every create action will fail.
2. tool-comic-create.mount() retrieves the comic.project-service capability
   registered by tool-comic-assets.  If tool-comic-assets isn't listed before
   tool-comic-create, the capability will be missing and mount will raise.
"""

from __future__ import annotations

from pathlib import Path


BEHAVIOR_YAML = (
    Path(__file__).parent.parent.parent.parent / "behaviors" / "comic-strips.yaml"
)


def test_behavior_yaml_contains_tool_comic_image_gen() -> None:
    """tool-comic-image-gen must appear in behaviors/comic-strips.yaml tools list."""
    content = BEHAVIOR_YAML.read_text()
    assert "tool-comic-image-gen" in content, (
        "tool-comic-image-gen is missing from behaviors/comic-strips.yaml. "
        "This means generate_image will be None and all create actions will fail."
    )


def test_tool_image_gen_mounted_before_tool_create() -> None:
    """tool-comic-image-gen must be listed BEFORE tool-comic-create (mount order matters)."""
    content = BEHAVIOR_YAML.read_text()
    idx_image_gen = content.find("tool-comic-image-gen")
    idx_create = content.find("tool-comic-create")
    assert idx_image_gen != -1, "tool-comic-image-gen not found in behavior YAML"
    assert idx_create != -1, "tool-comic-create not found in behavior YAML"
    assert idx_image_gen < idx_create, (
        "tool-comic-image-gen must appear BEFORE tool-comic-create in the tools list "
        f"(found at {idx_image_gen} vs {idx_create})"
    )


def test_behavior_yaml_contains_tool_comic_assets() -> None:
    """tool-comic-assets must appear in behaviors/comic-strips.yaml tools list."""
    content = BEHAVIOR_YAML.read_text()
    assert "tool-comic-assets" in content, (
        "tool-comic-assets is missing from behaviors/comic-strips.yaml. "
        "This means the comic.project-service capability will not be registered "
        "and tool-comic-create.mount() will raise RuntimeError."
    )


def test_tool_assets_mounted_before_tool_create() -> None:
    """tool-comic-assets must be listed BEFORE tool-comic-create (capability registry order).

    tool-comic-assets registers the comic.project-service capability that
    tool-comic-create consumes at mount time.  If assets mounts after create,
    get_capability() returns None and mount() raises RuntimeError.
    """
    content = BEHAVIOR_YAML.read_text()
    idx_assets = content.find("tool-comic-assets")
    idx_create = content.find("tool-comic-create")
    assert idx_assets != -1, "tool-comic-assets not found in behavior YAML"
    assert idx_create != -1, "tool-comic-create not found in behavior YAML"
    assert idx_assets < idx_create, (
        "tool-comic-assets must appear BEFORE tool-comic-create in the tools list "
        f"(found at {idx_assets} vs {idx_create})"
    )
