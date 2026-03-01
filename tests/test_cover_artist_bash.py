from pathlib import Path

COVER_ARTIST_PATH = Path(__file__).parent.parent / "agents" / "cover-artist.md"


def test_cover_artist_uses_asset_manager_not_bash() -> None:
    """cover-artist must use asset manager for base64, not bash."""
    content = COVER_ARTIST_PATH.read_text()

    # Should reference comic_asset for storing the avatar
    assert "comic_asset" in content, (
        "cover-artist must reference comic_asset tool for asset storage"
    )

    # Should NOT have bash in tools list (check frontmatter)
    # Find YAML frontmatter
    assert content.startswith("---")
    end = content.index("---", 3)
    frontmatter = content[3:end]
    assert "bash" not in frontmatter, (
        "cover-artist tools: should not include bash — "
        "base64 encoding is handled by the asset manager"
    )


def test_cover_artist_shows_bash_base64_example() -> None:
    """cover-artist Step 4 must include an explicit bash base64 encoding command.

    NOTE: This test preserves backward compatibility check. The existing
    Step 4 body still contains the bash example for reference, but the
    new Asset Integration section takes precedence.
    """
    content = COVER_ARTIST_PATH.read_text()

    # Find Step 4 (avatar fetch and embed)
    marker = "### Step 4:"
    start = content.find(marker)
    assert start != -1, f"Could not find '{marker}' section in cover-artist.md"
    end = content.find("\n### ", start + len(marker))
    step4_section = content[start:end] if end != -1 else content[start:]

    assert 'bash(command="base64' in step4_section, (
        'Step 4 must include an explicit bash(command="base64 ...") invocation'
    )
    assert "web_fetch" in step4_section, (
        "Step 4 must reference web_fetch before the base64 step"
    )
