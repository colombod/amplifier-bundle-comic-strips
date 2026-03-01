"""Base64 encoding/decoding utilities for comic assets.

Replaces all `bash(base64 ...)` calls in the pipeline with
cross-platform pure-Python equivalents.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path


def guess_mime(file_path: str) -> str:
    """Guess MIME type from file extension. Defaults to application/octet-stream."""
    mime, _ = mimetypes.guess_type(file_path)
    return mime or "application/octet-stream"


def bytes_to_base64(data: bytes) -> str:
    """Encode bytes to base64 string."""
    return base64.b64encode(data).decode("ascii")


def bytes_to_data_uri(data: bytes, mime_type: str) -> str:
    """Encode bytes to data URI: ``data:<mime>;base64,<encoded>``."""
    return f"data:{mime_type};base64,{bytes_to_base64(data)}"


def file_to_base64(file_path: str) -> str:
    """Read file and return base64 string.

    Blocking — call via ``asyncio.to_thread`` in async contexts.
    """
    return bytes_to_base64(Path(file_path).read_bytes())


def file_to_data_uri(file_path: str) -> str:
    """Read file and return data URI.

    Blocking — call via ``asyncio.to_thread`` in async contexts.
    """
    data = Path(file_path).read_bytes()
    mime = guess_mime(file_path)
    return bytes_to_data_uri(data, mime)


def base64_to_bytes(encoded: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(encoded)
