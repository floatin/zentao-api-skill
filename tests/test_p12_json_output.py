"""Tests for P12: CLI output must be API/code-friendly (JSON on stdout).

Mirrors the baserow-cli convention:
- stdout is always valid JSON (data objects/arrays, or {"status": ...} envelopes)
- stderr carries human-readable logs, confirm prompts, and error envelopes
- exit code: 0=success/cancel, 1=API/network/auth error, 2=non-interactive refuse
"""
from __future__ import annotations

import io
import json
import sys
from unittest.mock import MagicMock

import pytest


def _run(handler_name, client, args, monkeypatch, confirm_return=None):
    """Invoke a CLI command handler, capturing stdout/stderr, returning
    (stdout_text, stderr_text, exc_type)."""
    from zentao_api import cli

    out, err = io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)
    if confirm_return is not None:
        monkeypatch.setattr(cli, "_confirm", lambda *a, **kw: confirm_return)

    dispatch = getattr(cli, "COMMANDS", None)
    handler = dispatch[handler_name]
    exc = None
    try:
        handler(client, args)
    except SystemExit as e:  # _err_exit / --yes refuses call sys.exit
        exc = e
    return out.getvalue(), err.getvalue(), exc


def _args(**kw):
    ns = {
        "comment": "", "yes": False, "assigned_to": None,
        "story_id": None, "bug_id": None, "task_id": None,
        "product_id": None, "execution_id": None, "module_id": None,
        "name": None, "type": "story", "parent": "0", "title": None,
        "module": None, "plan_id": "0", "reviewer": "", "severity": "3",
        "pri": "3", "project_id": None, "assign_to": None, "parent_id": None,
        "tasks": None, "limit": 50, "status": "doing",
    }
    ns.update(kw)
    return __import__("argparse").Namespace(**ns)


# ---------- stdout is always valid JSON -------------------------------------


def test_products_stdout_is_json(monkeypatch):
    client = MagicMock()
    client.get_products.return_value = (True, [
        {"id": "1", "name": "Foo", "status": "active", "owner": "a"},
    ])
    out, err, _ = _run("products", client, _args(), monkeypatch)
    data = json.loads(out)  # must not raise
    assert isinstance(data, list)
    assert data[0]["id"] == "1"


def test_executions_stdout_is_json(monkeypatch):
    client = MagicMock()
    client.get_executions.return_value = (True, [
        {"id": "2", "name": "E1", "status": "doing", "begin": "", "end": ""},
    ])
    out, err, _ = _run("executions", client, _args(project_id="1"), monkeypatch)
    json.loads(out)
    assert "✅" not in out and "📋" not in out


def test_create_story_ok_envelope(monkeypatch):
    client = MagicMock()
    client.create_story.return_value = (True, {"id": "99"})
    out, err, _ = _run(
        "create-story", client,
        _args(product_id="1", execution_id="2", title="t", module="[m]"),
        monkeypatch, confirm_return=True,
    )
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["id"] == "99"


# ---------- errors go to stderr, non-zero exit -----------------------------


def test_products_failure_exits_1_and_json_error(monkeypatch):
    client = MagicMock()
    client.get_products.return_value = (False, "boom")
    out, err, exc = _run("products", client, _args(), monkeypatch)
    assert exc is not None and exc.code == 1
    err_payload = json.loads(err)
    assert err_payload["status"] == "error"


def test_query_failure_stdout_empty(monkeypatch):
    client = MagicMock()
    client.get_executions.return_value = (False, "network error")
    out, err, exc = _run("executions", client, _args(project_id="1"), monkeypatch)
    assert out.strip() == ""
    assert exc is not None and exc.code == 1


# ---------- cancelled operations return {"status":"cancelled"} -------------


def test_create_story_cancelled(monkeypatch):
    client = MagicMock()
    client.create_story.return_value = (True, {"id": "1"})
    out, err, exc = _run(
        "create-story", client,
        _args(product_id="1", execution_id="2", title="t", module="[m]"),
        monkeypatch, confirm_return=False,
    )
    data = json.loads(out)
    assert data["status"] == "cancelled"
    assert exc is None  # cancel is exit 0


def test_missing_credentials_exits_1(monkeypatch):
    from zentao_api import cli

    out, err = io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)
    monkeypatch.setattr(cli, "read_credentials", lambda *a, **kw: None)
    with pytest.raises(SystemExit) as ei:
        cli.main(["products"])  # parse passes; credential check fires
    assert ei.value.code == 1
    payload = json.loads(err.getvalue())
    assert payload["status"] == "error"
