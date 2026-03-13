"""Test that pyproject.toml has the required google-genai dependency."""

import tomllib
from pathlib import Path


def test_google_genai_dependency_present():
    """google-genai>=1.0.0 must be listed in optional-dependencies[embeddings]."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        config = tomllib.load(f)

    optional = config["project"].get("optional-dependencies", {})
    embeddings = optional.get("embeddings", [])
    assert "google-genai>=1.0.0" in embeddings, (
        f"Expected 'google-genai>=1.0.0' in optional-dependencies.embeddings, got: {embeddings}"
    )
