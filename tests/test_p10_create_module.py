"""P10: create-story / create-bug must always send ``module`` in body.

Server requires module field. CLI exposes ``--module`` as required param.
Client methods always include module in POST body (no more "0" sentinel skip).
"""
from __future__ import annotations

import io
import contextlib
from unittest.mock import patch, MagicMock

import pytest


# ---------- create_story client: module always in body -------------------


def test_create_story_module_in_body_when_explicit(client):
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(product_id="36", title="x", module="[模块1]")

    assert captured["data"]["module"] == "[模块1]"


def test_create_story_module_not_in_url(client):
    """P10: URL always uses 0 for module positions; real value only in body."""
    captured = {}

    def fake(method, path, data=None):
        captured["path"] = path
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(product_id="36", title="x", module="[模块2]")

    assert "[模块2]" not in captured["path"]
    assert captured["data"]["module"] == "[模块2]"


# ---------- create_bug client: module always in body ---------------------


def test_create_bug_default_module_in_body(client):
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_bug(product_id="36", title="test bug")

    # default module is "[模块1]" — always in body
    assert captured["data"]["module"] == "[模块1]"


def test_create_bug_explicit_module_in_body(client):
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_bug(product_id="36", title="test", module="[模块2]")

    assert captured["data"]["module"] == "[模块2]"


def test_create_bug_url_uses_product_id(client):
    captured = {}

    def fake(method, path, data=None):
        captured["method"] = method
        captured["path"] = path
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_bug(product_id="36", title="test")

    assert captured["method"] == "POST"
    assert "bug-create-36" in captured["path"]


# ---------- CLI create-story: --module required --------------------------


def test_cli_create_story_requires_module():
    from zentao_api import cli

    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "create-story",
            "--product-id", "36",
            "--execution-id", "281",
            "--title", "test",
            # --module missing → should fail
        ])


def test_cli_create_story_accepts_module():
    from zentao_api import cli

    parser = cli.build_parser()
    args = parser.parse_args([
        "create-story",
        "--product-id", "36",
        "--execution-id", "281",
        "--title", "test",
        "--module", "[模块1]",
    ])
    assert args.module == "[模块1]"


# ---------- CLI create-bug: new subcommand -------------------------------


def test_cli_create_bug_registered():
    from zentao_api import cli

    parser = cli.build_parser()
    args = parser.parse_args([
        "create-bug",
        "--product-id", "36",
        "--title", "test bug",
        "--module", "[模块2]",
    ])
    assert args.command == "create-bug"
    assert args.module == "[模块2]"


def test_cli_create_bug_requires_module():
    from zentao_api import cli

    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "create-bug",
            "--product-id", "36",
            "--title", "test",
            # --module missing → should fail
        ])


def test_cli_create_bug_handler_calls_client():
    from zentao_api import cli

    mock_client = MagicMock()
    mock_client.create_bug.return_value = (True, {"id": "999"})
    args = MagicMock(
        product_id="36", title="test", module="[模块1]",
        severity="3", pri="3", project_id=None, assigned_to=None,
    )

    with patch("zentao_api.cli._confirm", return_value=True):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS["create-bug"](mock_client, args)

    mock_client.create_bug.assert_called_once()
    call_kwargs = mock_client.create_bug.call_args
    assert call_kwargs[1]["module"] == "[模块1]"
    import json
    assert json.loads(buf.getvalue())["status"] == "ok"


def test_cli_create_bug_aborts_on_decline():
    from zentao_api import cli

    mock_client = MagicMock()
    args = MagicMock(
        product_id="36", title="test", module="[模块1]",
        severity="3", pri="3", project_id=None, assigned_to=None,
    )

    with patch("zentao_api.cli._confirm", return_value=False):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS["create-bug"](mock_client, args)

    mock_client.create_bug.assert_not_called()
    import json
    assert json.loads(buf.getvalue())["status"] == "cancelled"


def test_cli_create_story_handler_passes_module():
    """Regression: cmd_create_story must pass args.module to client.create_story."""
    import inspect
    from zentao_api import cli

    src = inspect.getsource(cli.cmd_create_story)
    assert "module=args.module" in src, (
        "cmd_create_story must pass module=args.module to client.create_story"
    )
