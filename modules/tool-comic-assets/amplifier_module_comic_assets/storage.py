"""Storage protocol and filesystem implementation for comic assets.

V1 uses local filesystem via ``asyncio.to_thread()``.  The protocol
is designed so a cloud backend (S3, Azure Blob, GCS) can be swapped
in without changing the service layer.
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageProtocol(Protocol):
    """Async storage interface.  V1 is filesystem; future is cloud."""

    async def write_bytes(self, rel_path: str, data: bytes) -> int:
        """Write binary data.  Creates parent dirs.  Returns bytes written."""
        ...

    async def write_text(self, rel_path: str, text: str) -> int:
        """Write text data (UTF-8).  Creates parent dirs.  Returns bytes written."""
        ...

    async def read_bytes(self, rel_path: str) -> bytes:
        """Read binary data.  Raises ``FileNotFoundError`` if missing."""
        ...

    async def read_text(self, rel_path: str) -> str:
        """Read text data (UTF-8).  Raises ``FileNotFoundError`` if missing."""
        ...

    async def exists(self, rel_path: str) -> bool:
        """Check if *rel_path* exists."""
        ...

    async def delete(self, rel_path: str) -> bool:
        """Delete file or directory tree.  Returns ``True`` if something was deleted."""
        ...

    async def list_dir(self, rel_path: str) -> list[str]:
        """List immediate children of a directory.  Returns names only."""
        ...

    async def abs_path(self, rel_path: str) -> str:
        """Resolve to an absolute path string (for passing to other tools)."""
        ...


class FileSystemStorage:
    """V1 storage backend — local filesystem via ``asyncio.to_thread()``."""

    def __init__(self, root: str = ".comic-assets") -> None:
        self._root = Path(root).resolve()

    @property
    def root(self) -> Path:
        return self._root

    async def write_bytes(self, rel_path: str, data: bytes) -> int:
        def _write() -> int:
            p = self._root / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            return len(data)

        return await asyncio.to_thread(_write)

    async def write_text(self, rel_path: str, text: str) -> int:
        def _write() -> int:
            p = self._root / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            encoded = text.encode("utf-8")
            p.write_bytes(encoded)
            return len(encoded)

        return await asyncio.to_thread(_write)

    async def read_bytes(self, rel_path: str) -> bytes:
        return await asyncio.to_thread((self._root / rel_path).read_bytes)

    async def read_text(self, rel_path: str) -> str:
        return await asyncio.to_thread(
            lambda: (self._root / rel_path).read_text(encoding="utf-8")
        )

    async def exists(self, rel_path: str) -> bool:
        return await asyncio.to_thread((self._root / rel_path).exists)

    async def delete(self, rel_path: str) -> bool:
        def _delete() -> bool:
            p = self._root / rel_path
            if not p.exists():
                return False
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return True

        return await asyncio.to_thread(_delete)

    async def list_dir(self, rel_path: str) -> list[str]:
        def _list() -> list[str]:
            p = self._root / rel_path
            if not p.is_dir():
                return []
            return sorted(e.name for e in p.iterdir())

        return await asyncio.to_thread(_list)

    async def abs_path(self, rel_path: str) -> str:
        return str((self._root / rel_path).resolve())
