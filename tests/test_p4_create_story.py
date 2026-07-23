"""Tests for the P4 create_story consolidation.

There must be exactly one create_story method on ZenTaoClient, and it must
accept (product_id, title, ...) so that both old call-sites and the CLI's
cmd_create_story can reach it.
"""
from __future__ import annotations

import inspect

from zentao_api.client import ZenTaoClient


def test_create_story_defined_once():
    """Python classes don't store duplicate definitions twice — only the last
    one survives. Verify the parameter names of the live one match the
    generalised signature, and that the older positional-only form is gone."""
    methods = [
        (name, obj)
        for name, obj in inspect.getmembers(ZenTaoClient, predicate=inspect.isfunction)
        if name == "create_story"
    ]
    assert len(methods) == 1, f"expected 1 create_story, found {len(methods)}"
    _, fn = methods[0]
    sig = inspect.signature(fn)
    params = [p for p in sig.parameters.keys() if p != "self"]
    # Generalised signature starts with product_id, title.
    assert params[:2] == ["product_id", "title"], params
    # And must accept arbitrary extra fields via **kwargs so existing callers
    # passing reviewer / execution_id / etc. still work.
    assert any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    ), "create_story must accept **kwargs"


def test_create_story_accepts_kwargs_and_routes(client):
    """Calling the live create_story must hit old_request with the product_id
    interpolated in the URL — that's the only behavioural contract the CLI
    relies on."""
    from unittest.mock import patch

    captured = {}

    def fake(method, path, data=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data
        return True, {"status": "success", "data": '{"id": 42}'}

    with patch.object(client, "old_request", side_effect=fake):
        ok, result = client.create_story(
            product_id="21",
            title="登录流程",
            execution_id="200",
            reviewer="alice",
        )

    assert ok is True
    assert captured["method"] == "POST"
    assert "21" in captured["path"]  # product_id shows up in URL
    assert captured["data"]["title"] == "登录流程"


def test_cli_create_story_uses_known_signature():
    """Regression: cli.py's cmd_create_story used to call
    ``client.create_story(product_id, execution_id, title, plan_id, reviewer)``
    which under the new (product_id, title, ...) signature would silently
    swap title and execution_id. The CLI must pass title in the title slot."""
    import inspect
    from zentao_api import cli

    src = inspect.getsource(cli.cmd_create_story)
    # title must be in the call, and execution_id must NOT be the 2nd positional.
    assert "title=title" in src or "title=" in src, (
        "cli.cmd_create_story must pass title to create_story"
    )
    # The old broken call pattern must be gone.
    assert "create_story(product_id, execution_id, title" not in src, (
        "cli.cmd_create_story still uses the old positional ordering"
    )