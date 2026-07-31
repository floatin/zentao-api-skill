"""Tests for P9: bug + story status transition CLI subcommands.

P8 added 8 task-status subcommands. P9 adds:
- 5 bug-status: assign-bug, confirm-bug, resolve-bug, close-bug, activate-bug
- 3 story-status: assign-story, close-story, activate-story

The test verifies parser, dispatch, and handler delegation.
"""
from __future__ import annotations

import io
import contextlib
from unittest.mock import patch, MagicMock

import pytest

from zentao_api import cli


# ---------- bug parser subcommands --------------------------------------


@pytest.mark.parametrize(
    "cmd_name, extra",
    [
        ("assign-bug", ["--assigned-to", "alice"]),
        ("confirm-bug", []),
        ("resolve-bug", []),
        ("close-bug", []),
        ("activate-bug", []),
    ],
)
def test_bug_subcommand_registered(cmd_name, extra):
    parser = cli.build_parser()
    args = parser.parse_args([cmd_name, "--bug-id", "100", *extra])
    assert args.command == cmd_name
    assert args.bug_id == "100"


# ---------- story parser subcommands ------------------------------------


@pytest.mark.parametrize(
    "cmd_name, extra",
    [
        ("assign-story", ["--assigned-to", "alice"]),
        ("close-story", []),
        ("activate-story", []),
    ],
)
def test_story_subcommand_registered(cmd_name, extra):
    parser = cli.build_parser()
    args = parser.parse_args([cmd_name, "--story-id", "100", *extra])
    assert args.command == cmd_name
    assert args.story_id == "100"


# ---------- bug dispatch + handler invocation -----------------------------


@pytest.mark.parametrize(
    "cmd_name, method_name, success_label_substr",
    [
        ("assign-bug",   "assign_bug",   "已指派给"),
        ("confirm-bug",  "confirm_bug",  "已确认"),
        ("close-bug",    "close_bug",    "已关闭"),
        ("activate-bug", "activate_bug", "已激活"),
    ],
)
def test_bug_handler_dispatches_and_prints_success(
    cmd_name, method_name, success_label_substr
):
    mock_client = MagicMock()
    getattr(mock_client, method_name).return_value = (True, {"id": "100"})

    args = MagicMock(bug_id="100", comment="", assigned_to="alice", yes=False)

    with patch("zentao_api.cli._confirm", return_value=True):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS[cmd_name](mock_client, args)

    getattr(mock_client, method_name).assert_called_once()
    import json
    payload = json.loads(buf.getvalue())
    assert payload["status"] == "ok"
    assert payload["bug_id"] == "100"


def test_resolve_bug_passes_resolution_and_build():
    mock_client = MagicMock()
    mock_client.resolve_bug.return_value = (True, {"id": "100"})
    args = MagicMock(bug_id="100", resolution="postponed", build="2.0", comment="排期")

    with patch("zentao_api.cli._confirm", return_value=True):
        cli.COMMANDS["resolve-bug"](mock_client, args)

    mock_client.resolve_bug.assert_called_once_with(
        "100", resolution="postponed", resolved_build="2.0", comment="排期"
    )


def test_assign_bug_passes_assigned_to():
    mock_client = MagicMock()
    mock_client.assign_bug.return_value = (True, {"id": "100"})
    args = MagicMock(bug_id="100", assigned_to="alice", comment="")

    with patch("zentao_api.cli._confirm", return_value=True):
        cli.COMMANDS["assign-bug"](mock_client, args)

    mock_client.assign_bug.assert_called_once_with(
        "100", "alice", comment=""
    )


# ---------- story dispatch + handler invocation -------------------------


@pytest.mark.parametrize(
    "cmd_name, method_name, success_label_substr",
    [
        ("close-story",    "close_story",    "已关闭"),
        ("activate-story", "activate_story", "已激活"),
    ],
)
def test_story_simple_handler_dispatches(cmd_name, method_name, success_label_substr):
    mock_client = MagicMock()
    getattr(mock_client, method_name).return_value = (True, {"id": "100"})

    args = MagicMock(story_id="100", yes=False)

    with patch("zentao_api.cli._confirm", return_value=True):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS[cmd_name](mock_client, args)

    getattr(mock_client, method_name).assert_called_once_with("100")
    import json
    payload = json.loads(buf.getvalue())
    assert payload["status"] == "ok"
    assert payload["story_id"] == "100"


def test_assign_story_routes_through_change_story():
    """assign-story doesn't have a dedicated client method; it uses
    change_story with assignedTo kwarg."""
    mock_client = MagicMock()
    mock_client.change_story.return_value = (True, {"id": "100"})
    args = MagicMock(story_id="100", assigned_to="alice")

    with patch("zentao_api.cli._confirm", return_value=True):
        cli.COMMANDS["assign-story"](mock_client, args)

    mock_client.change_story.assert_called_once_with("100", assignedTo="alice")


# ---------- prompt cancellation ------------------------------------------


def test_bug_handler_aborts_on_decline():
    mock_client = MagicMock()
    args = MagicMock(bug_id="100", comment="", yes=False)

    with patch("zentao_api.cli._confirm", return_value=False):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS["close-bug"](mock_client, args)

    mock_client.close_bug.assert_not_called()
    import json
    assert json.loads(buf.getvalue())["status"] == "cancelled"


def test_story_handler_aborts_on_decline():
    mock_client = MagicMock()
    args = MagicMock(story_id="100", yes=False)

    with patch("zentao_api.cli._confirm", return_value=False):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS["activate-story"](mock_client, args)

    mock_client.activate_story.assert_not_called()
    import json
    assert json.loads(buf.getvalue())["status"] == "cancelled"


# ---------- session guard on resolve_bug (P9 fix) ---------------------


def test_resolve_bug_loads_session_first(client):
    """P9 fix: resolve_bug bypasses old_request and posts directly; it must
    ensure ``self.sid`` is loaded first or ``self.session.post`` crashes."""
    from zentao_api.client.bugs import BugsMixin
    import inspect

    src = inspect.getsource(BugsMixin.resolve_bug)
    guard_pos = src.find("if not self.sid:")
    post_pos = src.find("self.session.post(")
    assert guard_pos != -1, "resolve_bug missing session guard"
    assert post_pos != -1
    assert guard_pos < post_pos


def test_assign_bug_loads_session_first(client):
    from zentao_api.client.bugs import BugsMixin
    import inspect

    src = inspect.getsource(BugsMixin.assign_bug)
    guard_pos = src.find("if not self.sid:")
    post_pos = src.find("self.session.post(")
    assert guard_pos != -1
    assert guard_pos < post_pos


def test_bug_handler_prints_failure():
    mock_client = MagicMock()
    mock_client.close_bug.return_value = (False, {"message": "权限不足"})
    args = MagicMock(bug_id="100", comment="", yes=False)

    with patch("zentao_api.cli._confirm", return_value=True):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS["close-bug"](mock_client, args)

    import json
    payload = json.loads(buf.getvalue())
    assert payload["status"] == "error"
    assert "权限不足" in str(payload["error"])


def test_story_handler_prints_failure():
    mock_client = MagicMock()
    mock_client.activate_story.return_value = (False, {"message": "需求已关闭"})
    args = MagicMock(story_id="100", yes=False)

    with patch("zentao_api.cli._confirm", return_value=True):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS["activate-story"](mock_client, args)

    import json
    payload = json.loads(buf.getvalue())
    assert payload["status"] == "error"
    assert "需求已关闭" in str(payload["error"])