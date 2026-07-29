"""Tests for P2: helpers + status consolidation + create_subtasks simplification.

P2 introduces three changes that cut ~100+ lines of boilerplate:
1. ``_data_get(path, key)`` helper that wraps ``old_request`` + ``json.loads`` +
   ``data.get(key)`` in one call.
2. ``_change_task_status(task_id, status, comment)`` helper that
   consolidates the cancel_task and start_task patterns (get task detail,
   build edit dict, POST to task-edit).
3. ``create_subtasks`` rewrite using ``requests`` ``files=`` instead of
   hand-built multipart bytes.
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest


def _ok_payload(inner):
    return (True, {"status": "success", "data": json.dumps(inner)})


# ---------- _data_get helper --------------------------------------------------


def test_data_get_returns_nested_value(client):
    """The helper should unwrap old_request's {status, data} envelope and
    return data.get(key)."""
    with patch.object(
        client,
        "old_request",
        return_value=_ok_payload({"stories": [{"id": "1"}], "extra": "x"}),
    ) as mocked:
        result = client._data("/story-list.json", "stories")

    assert result == [{"id": "1"}]
    mocked.assert_called_once_with("GET", "/story-list.json")


def test_data_get_returns_empty_default_when_payload_bad(client):
    """If old_request fails or the envelope is malformed, return [] / {}."""
    with patch.object(client, "old_request", return_value=(False, "boom")):
        assert client._data("/x.json", "items") == []


def test_data_get_returns_dict_default_when_key_missing(client):
    """If the JSON payload is there but the key isn't, return the default."""
    with patch.object(
        client,
        "old_request",
        return_value=_ok_payload({"other": "x"}),
    ):
        assert client._data("/x.json", "missing") == []


# ---------- _change_task_status helper ---------------------------------------


def _fake_task(status="wait"):
    return {
        "id": "42",
        "name": "测试任务",
        "parent": "0",
        "project": "1",
        "module": "0",
        "story": "0",
        "type": "devel",
        "pri": "3",
        "estimate": "8",
        "left": "8",
        "consumed": "0",
        "assignedTo": "alice",
        "status": status,
    }


def test_change_task_status_posts_to_task_edit(client):
    """The helper must POST to task-edit-{id}.json with a minimal body
    containing only ``status`` (and ``comment`` if provided). Server fills
    other fields with defaults — that's the only path that accepts
    arbitrary status changes (e.g. cancel from any state)."""
    captured = {}

    def fake(method, path, data=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data
        return True, {"status": "success", "data": "{}"}

    with patch.object(client, "old_request", side_effect=fake):
        ok, _ = client._change_task_status("42", "doing", comment="开工了")

    assert ok is True
    assert captured["path"] == "/task-edit-42.json"
    # Minimal body — only status (and optional comment); no get_task_detail,
    # no echo of all the task fields. The server accepts defaults.
    assert captured["data"] == {"status": "doing", "comment": "开工了"}


def test_change_task_status_no_comment(client):
    """``comment`` default is empty string — it's still added to the body
    so the server's form-data parser doesn't see a missing key."""
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data
        return True, {"status": "success", "data": "{}"}

    with patch.object(client, "old_request", side_effect=fake):
        client._change_task_status("42", "cancel")

    assert captured["data"] == {"status": "cancel"}


def test_cancel_task_uses_change_task_status(client):
    """Regression: cancel_task should now route through _change_task_status."""
    import inspect
    from zentao_api.client.writes import WritesMixin

    src = inspect.getsource(WritesMixin.cancel_task)
    assert "_change_task_status" in src, (
        "cancel_task must delegate to _change_task_status"
    )


def test_start_task_uses_change_task_status(client):
    """Regression: start_task should now route through _change_task_status."""
    import inspect
    from zentao_api.client.writes import WritesMixin

    src = inspect.getsource(WritesMixin.start_task)
    assert "_change_task_status" in src, (
        "start_task must delegate to _change_task_status"
    )


# ---------- create_subtasks simplification -----------------------------------


def test_create_subtasks_sends_multipart_with_ditto_after_first(client):
    """After P2 the multipart body is built by ``requests`` from a ``files=``
    dict. The ditto convention (ditto for parent/story/type/assignedTo/pri on
    tasks after the first) must still be preserved."""
    captured = {}

    class FakeResponse:
        status_code = 200

    def fake_post(url, files=None, data=None, params=None, headers=None, timeout=None):
        captured["url"] = url
        captured["files"] = files
        captured["data"] = data
        captured["params"] = params
        return FakeResponse()

    client.session.post = fake_post  # type: ignore[assignment]

    tasks = [
        {"name": "task-A", "estimate": 4, "assignedTo": "alice", "type": "devel", "pri": 3},
        {"name": "task-B", "estimate": 2, "assignedTo": "bob", "type": "test", "pri": 2},
    ]
    ok, result = client.create_subtasks(
        execution_id="200",
        parent_id="42",
        tasks=tasks,
    )

    assert ok is True
    files = captured["files"]
    assert isinstance(files, dict), f"expected files dict, got {type(files)}"

    # First task: explicit values for everything.
    assert files["name[0]"][1] == "task-A"
    assert files["assignedTo[0]"][1] == "alice"
    assert files["estimate[0]"][1] == "4"
    assert files["type[0]"][1] == "devel"
    assert files["pri[0]"][1] == "3"
    assert files["parent[0]"][1] == "42"

    # Second task: ditto for parent/story/type/assignedTo/pri, but
    # explicit name and estimate.
    assert files["name[1]"][1] == "task-B"
    assert files["estimate[1]"][1] == "2"
    assert files["parent[1]"][1] == "ditto"
    assert files["story[1]"][1] == "ditto"
    assert files["type[1]"][1] == "ditto"
    assert files["assignedTo[1]"][1] == "ditto"
    assert files["pri[1]"][1] == "ditto"


def test_create_subtasks_url_includes_parent_and_execution(client):
    """URL must still embed execution_id and parent_id."""
    captured = {}

    class FakeResponse:
        status_code = 200

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        return FakeResponse()

    client.session.post = fake_post  # type: ignore[assignment]

    client.create_subtasks(
        execution_id="999",
        parent_id="77",
        tasks=[{"name": "t1", "estimate": 1}],
    )

    assert "999" in captured["url"]
    assert "77" in captured["url"]
    assert captured["params"] == {"zentaosid": "fake-sid"}