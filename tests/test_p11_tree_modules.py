"""P11: module (tree) CRUD — list / create / edit / delete.

Covers:
- ``list_modules`` client method + ``modules`` CLI
- ``create_module`` / ``edit_module`` / ``delete_module`` client + CLI
"""
from __future__ import annotations

import io
import contextlib
import json
from unittest.mock import patch, MagicMock

import pytest


# ---------- list_modules client --------------------------------------------


def test_list_modules_returns_sons(client):
    inner = {
        "title": "x",
        "sons": [
            {"id": "600", "name": "模块1", "parent": "0", "type": "story"},
            {"id": "601", "name": "模块2", "parent": "0", "type": "story"},
        ],
    }
    with patch.object(client, "_data_unwrap", return_value=inner):
        ok, sons = client.list_modules("36")
    assert ok is True
    assert len(sons) == 2
    assert sons[0]["name"] == "模块1"


def test_list_modules_empty_on_failure(client):
    with patch.object(client, "_data_unwrap", return_value={}):
        ok, sons = client.list_modules("99")
    assert ok is True
    assert sons == []


def test_list_modules_url(client):
    captured = {}

    def fake(path):
        captured["path"] = path
        return {"sons": []}

    with patch.object(client, "_data_unwrap", side_effect=fake):
        client.list_modules("36", "bug")
    assert captured["path"] == "/tree-browse-36-bug.json"


# ---------- create_module client -------------------------------------------


def test_create_module_sends_post(client):
    captured = {}

    def fake(method, path, data=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data or {}
        return True, {"status": "success"}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_module("36", "新模块", view_type="story", parent="0")

    assert captured["method"] == "POST"
    assert "tree-create-36-story" in captured["path"]
    assert captured["data"]["name"] == "新模块"
    assert captured["data"]["parent"] == "0"


def test_create_module_with_parent(client):
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success"}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_module("36", "子模块", parent="600")

    assert captured["data"]["parent"] == "600"


# ---------- edit_module client ---------------------------------------------


def test_edit_module(client):
    captured = {}

    def fake(method, path, data=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data or {}
        return True, {"status": "success"}

    with patch.object(client, "old_request", side_effect=fake):
        client.edit_module("600", "改名")

    assert captured["method"] == "POST"
    assert "tree-update-600" in captured["path"]
    assert captured["data"]["name"] == "改名"


# ---------- delete_module client -------------------------------------------


def test_delete_module(client):
    captured = {}

    def fake(method, path, data=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data
        return True, {"status": "success"}

    with patch.object(client, "old_request", side_effect=fake):
        client.delete_module("600")

    assert captured["method"] == "GET"
    assert "tree-delete-600-story-yes" in captured["path"]
    assert captured["data"] is None


# ---------- CLI: modules ---------------------------------------------------


def test_cli_modules_registered():
    from zentao_api import cli
    assert "modules" in cli.COMMANDS


def test_cli_modules_parser():
    from zentao_api import cli
    parser = cli.build_parser()
    args = parser.parse_args(["modules", "--product-id", "36"])
    assert args.command == "modules"
    assert args.type == "story"


def test_cli_modules_parser_type():
    from zentao_api import cli
    parser = cli.build_parser()
    args = parser.parse_args(["modules", "--product-id", "36", "--type", "bug"])
    assert args.type == "bug"


def test_cli_modules_handler_prints_table():
    from zentao_api import cli
    mock_client = MagicMock()
    mock_client.list_modules.return_value = (True, [
        {"id": "600", "name": "模块1", "parent": "0", "type": "story"},
        {"id": "601", "name": "模块2", "parent": "0", "type": "story"},
    ])
    args = MagicMock(product_id="36", type="story")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.COMMANDS["modules"](mock_client, args)
    payload = json.loads(buf.getvalue())
    assert len(payload) == 2
    assert payload[0]["name"] == "模块1"
    assert payload[1]["name"] == "模块2"


def test_cli_modules_handler_failure():
    from zentao_api import cli
    mock_client = MagicMock()
    mock_client.list_modules.return_value = (False, "no permission")
    args = MagicMock(product_id="99", type="story")
    with pytest.raises(SystemExit) as ei:
        cli.COMMANDS["modules"](mock_client, args)
    assert ei.value.code == 1


# ---------- CLI: create-module ---------------------------------------------


def test_cli_create_module_registered():
    from zentao_api import cli
    assert "create-module" in cli.COMMANDS


def test_cli_create_module_parser():
    from zentao_api import cli
    parser = cli.build_parser()
    args = parser.parse_args([
        "create-module", "--product-id", "36", "--name", "新模块",
    ])
    assert args.command == "create-module"
    assert args.name == "新模块"
    assert args.parent == "0"


def test_cli_create_module_handler():
    from zentao_api import cli
    mock_client = MagicMock()
    mock_client.create_module.return_value = (True, {"status": "success"})
    args = MagicMock()
    args.product_id = "36"
    args.name = "新模块"
    args.type = "story"
    args.parent = "0"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        with patch("zentao_api.cli._confirm", return_value=True):
            cli.COMMANDS["create-module"](mock_client, args)
    mock_client.create_module.assert_called_once_with(
        "36", "新模块", view_type="story", parent="0",
    )
    assert json.loads(buf.getvalue())["status"] == "ok"


def test_cli_create_module_abort():
    from zentao_api import cli
    mock_client = MagicMock()
    args = MagicMock()
    args.product_id = "36"
    args.name = "x"
    args.type = "story"
    args.parent = "0"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        with patch("zentao_api.cli._confirm", return_value=False):
            cli.COMMANDS["create-module"](mock_client, args)
    mock_client.create_module.assert_not_called()
    assert json.loads(buf.getvalue())["status"] == "cancelled"


# ---------- CLI: edit-module -----------------------------------------------


def test_cli_edit_module_registered():
    from zentao_api import cli
    assert "edit-module" in cli.COMMANDS


def test_cli_edit_module_handler():
    from zentao_api import cli
    mock_client = MagicMock()
    mock_client.edit_module.return_value = (True, {})
    args = MagicMock()
    args.module_id = "600"
    args.name = "改名"
    args.type = "story"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        with patch("zentao_api.cli._confirm", return_value=True):
            cli.COMMANDS["edit-module"](mock_client, args)
    mock_client.edit_module.assert_called_once_with("600", "改名", view_type="story")
    assert json.loads(buf.getvalue())["status"] == "ok"


# ---------- CLI: delete-module ---------------------------------------------


def test_cli_delete_module_registered():
    from zentao_api import cli
    assert "delete-module" in cli.COMMANDS


def test_cli_delete_module_handler():
    from zentao_api import cli
    mock_client = MagicMock()
    mock_client.delete_module.return_value = (True, {})
    args = MagicMock(module_id="600", type="story")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        with patch("zentao_api.cli._confirm", return_value=True):
            cli.COMMANDS["delete-module"](mock_client, args)
    mock_client.delete_module.assert_called_once_with("600", view_type="story")
    assert json.loads(buf.getvalue())["status"] == "ok"
