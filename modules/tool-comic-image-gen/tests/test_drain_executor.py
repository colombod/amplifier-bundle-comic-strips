"""Tests for the _drain_executor conftest fixture."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio(loop_scope="function")
async def test_drain_executor_fixture_is_applied(_drain_executor: None) -> None:
    """_drain_executor autouse fixture must be registered in conftest.

    This test explicitly requests the fixture to ensure it exists.
    If conftest.py is missing the fixture, collection fails with
    'fixture _drain_executor not found'.
    """
    # Nothing to assert — the fixture's cleanup runs in teardown.
    # Reaching this line means the fixture was successfully resolved.
