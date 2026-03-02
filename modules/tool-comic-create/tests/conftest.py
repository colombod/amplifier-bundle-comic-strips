"""Shared pytest fixtures for tool-comic-create tests."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from amplifier_module_comic_assets.service import ComicProjectService
from amplifier_module_comic_assets.storage import FileSystemStorage

_MINIMAL_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture()
def tmp_storage(tmp_path):
    """FileSystemStorage rooted at tmp_path / '.comic-assets'."""
    return FileSystemStorage(str(tmp_path / ".comic-assets"))


@pytest.fixture()
def service(tmp_storage):
    """ComicProjectService backed by a fresh temporary storage."""
    return ComicProjectService(tmp_storage)


@pytest.fixture()
def sample_png(tmp_path):
    """Write a minimal PNG file and return its path as a string."""
    png_path = tmp_path / "test.png"
    png_path.write_bytes(_MINIMAL_PNG)
    return str(png_path)


@pytest_asyncio.fixture(autouse=True)
async def _drain_executor() -> None:
    """Ensure the default executor is shut down after each test.

    ``asyncio.to_thread()`` in ``FileSystemStorage`` creates a
    ``ThreadPoolExecutor`` per event loop.  With ``loop_scope="function"``
    each test gets a fresh loop; without explicit shutdown, thread stacks
    (8 MB each on Linux) accumulate across the suite.
    """
    yield
    loop = asyncio.get_event_loop()
    await loop.shutdown_default_executor()
