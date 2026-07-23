"""Pytest fixtures for the zentao_api test suite."""
from __future__ import annotations

import pytest

from zentao_api.client import ZenTaoClient


@pytest.fixture
def client(tmp_path):
    """A ZenTaoClient that never touches the network.

    The session is created with an isolated tmp directory so no real session
    files leak, and `sid` is injected so old_request skips the login flow.
    """
    c = ZenTaoClient(
        endpoint="http://test.local",
        username="tester",
        password="secret",
        session_dir=str(tmp_path),
        auto_save=False,
        auto_load=False,
    )
    c.sid = "fake-sid"
    c.session = __import__("requests").Session()
    return c