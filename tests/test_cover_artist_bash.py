from pathlib import Path

COVER_ARTIST_PATH = Path(__file__).parent.parent / "agents" / "cover-artist.md"


def test_cover_artist_shows_bash_base64_example() -> None:
    """cover-artist instructions must include a bash base64 example for avatar encoding."""
    content = COVER_ARTIST_PATH.read_text()
    assert "base64" in content, (
        "cover-artist must show how to base64-encode the avatar PNG using bash"
    )
    assert "bash" in content.lower(), (
        "cover-artist must reference the bash tool for base64 encoding"
    )
