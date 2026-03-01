"""Tests for amplifier_module_comic_assets.storage.FileSystemStorage."""

from __future__ import annotations

import pytest

from amplifier_module_comic_assets.storage import FileSystemStorage


# ---------------------------------------------------------------------------
# write / read roundtrips
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_write_read_bytes_roundtrip(tmp_storage: FileSystemStorage) -> None:
    data = b"\x89PNG\r\n\x1a\nHello"
    await tmp_storage.write_bytes("panel.png", data)
    result = await tmp_storage.read_bytes("panel.png")
    assert result == data


@pytest.mark.asyncio(loop_scope="function")
async def test_write_read_text_roundtrip(tmp_storage: FileSystemStorage) -> None:
    text = '{"key": "value", "emoji": "🎨"}'
    await tmp_storage.write_text("meta.json", text)
    result = await tmp_storage.read_text("meta.json")
    assert result == text


@pytest.mark.asyncio(loop_scope="function")
async def test_write_creates_parent_dirs(tmp_storage: FileSystemStorage) -> None:
    await tmp_storage.write_text("nested/path/file.txt", "content")
    result = await tmp_storage.read_text("nested/path/file.txt")
    assert result == "content"


# ---------------------------------------------------------------------------
# read missing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_read_missing_raises(tmp_storage: FileSystemStorage) -> None:
    with pytest.raises(FileNotFoundError):
        await tmp_storage.read_bytes("does_not_exist.bin")


# ---------------------------------------------------------------------------
# exists
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_exists_true_false(tmp_storage: FileSystemStorage) -> None:
    await tmp_storage.write_bytes("present.bin", b"x")
    assert await tmp_storage.exists("present.bin") is True
    assert await tmp_storage.exists("absent.bin") is False


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_file(tmp_storage: FileSystemStorage) -> None:
    await tmp_storage.write_bytes("todelete.bin", b"x")
    deleted = await tmp_storage.delete("todelete.bin")
    assert deleted is True
    assert await tmp_storage.exists("todelete.bin") is False


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_directory(tmp_storage: FileSystemStorage) -> None:
    await tmp_storage.write_bytes("subdir/file.txt", b"content")
    deleted = await tmp_storage.delete("subdir")
    assert deleted is True
    assert await tmp_storage.exists("subdir") is False


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_missing_returns_false(tmp_storage: FileSystemStorage) -> None:
    result = await tmp_storage.delete("nonexistent_path")
    assert result is False


# ---------------------------------------------------------------------------
# list_dir
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_list_dir(tmp_storage: FileSystemStorage) -> None:
    await tmp_storage.write_text("mydir/beta.txt", "b")
    await tmp_storage.write_text("mydir/alpha.txt", "a")
    await tmp_storage.write_text("mydir/gamma.txt", "g")
    names = await tmp_storage.list_dir("mydir")
    assert names == sorted(names)
    assert set(names) == {"alpha.txt", "beta.txt", "gamma.txt"}


@pytest.mark.asyncio(loop_scope="function")
async def test_list_dir_empty(tmp_storage: FileSystemStorage) -> None:
    names = await tmp_storage.list_dir("nonexistent_dir")
    assert names == []


# ---------------------------------------------------------------------------
# abs_path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_abs_path(tmp_storage: FileSystemStorage) -> None:
    abs_p = await tmp_storage.abs_path("some/file.txt")
    # Must be absolute and end with the relative path
    assert abs_p.startswith("/")
    assert abs_p.endswith("some/file.txt")
    # Must be under the storage root
    assert abs_p.startswith(str(tmp_storage.root))
