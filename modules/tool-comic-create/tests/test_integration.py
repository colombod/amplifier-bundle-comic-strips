"""Integration test: full pipeline with mocked image gen.

Proves the core design invariant:
  - base64 image data is embedded in the final HTML file on disk
  - base64 NEVER appears in any tool result returned to the agent
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_module_comic_create import ComicCreateTool

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def _make_mock_gen(tmp_path):
    async def _generate(**kwargs):
        out = Path(kwargs["output_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(_PNG)
        return {"success": True, "path": str(out), "provider_used": "mock"}

    mock = MagicMock()
    mock.generate = AsyncMock(side_effect=_generate)
    return mock


@pytest.mark.asyncio(loop_scope="function")
async def test_full_pipeline_no_base64_in_tool_results(service, tmp_path) -> None:
    """End-to-end: create characters, panels, cover, assemble — verify no base64 in any tool result."""
    await service.create_issue("e2e-proj", "E2E Issue")
    mock_gen = _make_mock_gen(tmp_path)
    tool = ComicCreateTool(service=service, image_gen=mock_gen)

    all_outputs: list[str] = []

    # 1. Create character
    r1 = await tool.execute(
        {
            "action": "create_character_ref",
            "project": "e2e-proj",
            "issue": "issue-001",
            "name": "Explorer",
            "prompt": "A seasoned scout",
            "visual_traits": "tall, blue eyes",
            "distinctive_features": "compass pendant",
        }
    )
    assert r1.success
    all_outputs.append(r1.output)
    char_uri = json.loads(r1.output)["uri"]

    # 2. Create panel with character reference
    r2 = await tool.execute(
        {
            "action": "create_panel",
            "project": "e2e-proj",
            "issue": "issue-001",
            "name": "panel_01",
            "prompt": "Explorer faces errors",
            "character_uris": [char_uri],
        }
    )
    assert r2.success
    all_outputs.append(r2.output)
    panel_uri = json.loads(r2.output)["uri"]

    # 3. Create cover
    r3 = await tool.execute(
        {
            "action": "create_cover",
            "project": "e2e-proj",
            "issue": "issue-001",
            "prompt": "Dramatic group shot",
            "title": "E2E Test Comic",
            "character_uris": [char_uri],
        }
    )
    assert r3.success
    all_outputs.append(r3.output)
    cover_uri = json.loads(r3.output)["uri"]

    # 4. Assemble
    output_path = str(tmp_path / "final.html")
    r4 = await tool.execute(
        {
            "action": "assemble_comic",
            "project": "e2e-proj",
            "issue": "issue-001",
            "output_path": output_path,
            "style_uri": "comic://e2e-proj/styles/default",
            "layout": {
                "title": "E2E Comic",
                "cover": {"uri": cover_uri},
                "pages": [
                    {"layout": "1x1", "panels": [{"uri": panel_uri, "overlays": []}]}
                ],
            },
        }
    )
    assert r4.success
    all_outputs.append(r4.output)

    # CRITICAL ASSERTION: No base64 data in any tool result returned to the agent
    for output in all_outputs:
        assert "data:image" not in output, (
            f"Base64 data URI found in tool result: {output[:200]}"
        )
        # A real base64 image would be thousands of chars; all results must stay compact
        assert len(output) < 1000, (
            f"Tool result suspiciously large ({len(output)} chars): {output[:200]}"
        )

    # Verify the final HTML exists and does contain base64 (internal, not in context)
    html = Path(output_path).read_text()
    assert "data:image/png;base64," in html
    assert "<!DOCTYPE html>" in html
    assert len(html) > 200
