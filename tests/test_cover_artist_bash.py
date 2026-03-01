from pathlib import Path

COVER_ARTIST_PATH = Path(__file__).parent.parent / "agents" / "cover-artist.md"


def test_cover_artist_shows_bash_base64_example() -> None:
    """cover-artist Step 4 must include an explicit bash base64 encoding command."""
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
