"""Tests for amplifier_module_comic_assets.encoding module."""

from __future__ import annotations

import base64

from amplifier_module_comic_assets.encoding import (
    base64_to_bytes,
    bytes_to_base64,
    bytes_to_data_uri,
    file_to_base64,
    file_to_data_uri,
    guess_mime,
)

# ---------------------------------------------------------------------------
# bytes_to_base64 / base64_to_bytes
# ---------------------------------------------------------------------------


def test_bytes_to_base64_roundtrip() -> None:
    data = b"hello, comic world!"
    encoded = bytes_to_base64(data)
    decoded = base64_to_bytes(encoded)
    assert decoded == data


def test_base64_to_bytes() -> None:
    original = b"\x00\x01\x02\xff"
    encoded = base64.b64encode(original).decode("ascii")
    assert base64_to_bytes(encoded) == original


# ---------------------------------------------------------------------------
# bytes_to_data_uri
# ---------------------------------------------------------------------------


def test_bytes_to_data_uri_format() -> None:
    data = b"\x89PNG\r\n\x1a\n"
    uri = bytes_to_data_uri(data, "image/png")
    assert uri.startswith("data:image/png;base64,")
    # Verify the payload decodes back to the original bytes
    payload = uri[len("data:image/png;base64,") :]
    assert base64.b64decode(payload) == data


# ---------------------------------------------------------------------------
# file_to_base64 / file_to_data_uri
# ---------------------------------------------------------------------------


def test_file_to_base64(sample_png) -> None:
    from pathlib import Path

    expected_bytes = Path(sample_png).read_bytes()
    result = file_to_base64(sample_png)
    assert base64_to_bytes(result) == expected_bytes


def test_file_to_data_uri(sample_png) -> None:
    uri = file_to_data_uri(sample_png)
    assert uri.startswith("data:image/png;base64,")


# ---------------------------------------------------------------------------
# guess_mime
# ---------------------------------------------------------------------------


def test_guess_mime_png() -> None:
    assert guess_mime("picture.png") == "image/png"


def test_guess_mime_json() -> None:
    assert guess_mime("data.json") == "application/json"


def test_guess_mime_html() -> None:
    assert guess_mime("comic.html") == "text/html"


def test_guess_mime_unknown() -> None:
    # Use a deliberately nonsensical extension that no MIME database knows
    assert guess_mime("file.zzz_no_such_ext") == "application/octet-stream"
