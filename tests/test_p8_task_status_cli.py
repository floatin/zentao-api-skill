"""Tests for P8: 8 task-status transition CLI subcommands.

P6/P7 added mock-level tests for the client methods; P8 verifies the CLI
exposes start/pause/restart/finish/close/cancel/activate/assign as
subcommands with the right args and that they dispatch to the right
client method when confirmed.
"""
from __future__ import annotations

import io
import contextlib
from unittest.mock import patch, MagicMock

import pytest

from zentao_api import cli


# ---------- parser subcommands ----------------------------------------------


@pytest.mark.parametrize(
    "cmd_name, extra",
    [
        ("start-task", []),
        ("pause-task", []),
        ("restart-task", []),
        ("finish-task", []),
        ("close-task", []),
        ("cancel-task", []),
        ("activate-task", []),
        ("assign-task", ["--assigned-to", "alice"]),
    ],
)
def test_subcommand_registered_in_parser(cmd_name, extra):
    parser = cli.build_parser()
    args = parser.parse_args([cmd_name, "--task-id", "29653", *extra])
    assert args.command == cmd_name
    assert args.task_id == "29653"


# ---------- COMMANDS dispatch ----------------------------------------------


@pytest.mark.parametrize(
    "cmd_name, method_name",
    [
        ("start-task", "start_task"),
        ("pause-task", "pause_task"),
        ("restart-task", "restart_task"),
        ("finish-task", "finish_task"),
        ("close-task", "close_task"),
        ("cancel-task", "cancel_task"),
        ("activate-task", "activate_task"),
    ],
)
def test_status_command_in_dispatch_dict(cmd_name, method_name):
    assert cmd_name in cli.COMMANDS, f"{cmd_name} not in COMMANDS dispatch dict"


def test_assign_command_in_dispatch_dict():
    assert "assign-task" in cli.COMMANDS


# ---------- handler invokes the correct client method ----------------------


@pytest.mark.parametrize(
    "cmd_name, method_name, status_label_substr",
    [
        ("start-task", "start_task", "doing"),
        ("pause-task", "pause_task", "暂停"),
        ("restart-task", "restart_task", "恢复 doing"),
        ("finish-task", "finish_task", "已完成"),
        ("close-task", "close_task", "已关闭"),
        ("cancel-task", "cancel_task", "已取消"),
        ("activate-task", "activate_task", "已激活"),
    ],
)
def test_status_handler_dispatches_and_prints_success(
    cmd_name, method_name, status_label_substr
):
    """Auto-confirm the prompt, mock the client method, expect success label."""
    mock_client = MagicMock()
    getattr(mock_client, method_name).return_value = (True, {"id": "29653"})

    args = MagicMock(task_id="29653", comment="")

    with patch("zentao_api.cli._confirm", return_value=True):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS[cmd_name](mock_client, args)

    getattr(mock_client, method_name).assert_called_once_with(
        "29653", comment=""
    )
    assert status_label_substr in buf.getvalue()


def test_assign_task_handler_passes_assigned_to():
    mock_client = MagicMock()
    mock_client.assign_task.return_value = (True, {"id": "29653"})
    args = MagicMock(task_id="29653", assigned_to="alice", comment="接手")

    with patch("zentao_api.cli._confirm", return_value=True):
        cli.COMMANDS["assign-task"](mock_client, args)

    mock_client.assign_task.assert_called_once_with(
        "29653", assigned_to="alice", comment="接手"
    )


# ---------- prompt cancellation ---------------------------------------------


def test_handler_aborts_when_user_declines():
    """If user types 'n' at the confirm prompt, the client method is not called."""
    mock_client = MagicMock()
    args = MagicMock(task_id="999", comment="")

    with patch("zentao_api.cli._confirm", return_value=False):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS["start-task"](mock_client, args)

    mock_client.start_task.assert_not_called()
    assert "已取消" in buf.getvalue()


# ---------- failure path prints the server message -----------------------


def test_handler_prints_failure_message():
    mock_client = MagicMock()
    mock_client.start_task.return_value = (False, {"message": "任务不存在"})

    args = MagicMock(task_id="999", comment="")

    with patch("zentao_api.cli._confirm", return_value=True):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.COMMANDS["start-task"](mock_client, args)

    assert "失败" in buf.getvalue()
    assert "任务不存在" in buf.getvalue()


# ---------- session-direct client methods auto-load session -------------


@pytest.mark.parametrize(
    "method_name",
    [
        "finish_task",
        "pause_task",
        "restart_task",
        "activate_task",
        "assign_task",
    ],
)
def test_session_direct_method_loads_session_first(method_name):
    """These 5 methods bypass ``old_request`` and POST directly. Before the
    P8 fix they hit ``self.session.post(...)`` while ``self.session`` was
    None (because no earlier call had loaded it). Verify each guards."""
    from zentao_api.client.writes import WritesMixin
    import inspect

    src = inspect.getsource(getattr(WritesMixin, method_name))
    # The guard must appear *before* the `self.session.post` call.
    guard_pos = src.find("if not self.sid:")
    post_pos = src.find("self.session.post(")
    assert guard_pos != -1, f"{method_name} missing session guard"
    assert post_pos != -1, f"{method_name} doesn't use self.session.post at all"
    assert guard_pos < post_pos, f"{method_name}: guard must precede .session.post"


# ---------- status field in body ------------------------------------------


@pytest.mark.parametrize(
    "method_name, expected_status",
    [
        ("finish_task", "done"),
        ("pause_task", "pause"),
        ("restart_task", "doing"),
        ("activate_task", "doing"),
        ("assign_task", "doing"),
    ],
)
def test_status_method_includes_status_field(method_name, expected_status):
    """P9 fix: ZenTao's status-transition endpoints require the new status
    value to be sent as form data, otherwise the response is a fake success
    that doesn't actually change the task.
    """
    from zentao_api.client.writes import WritesMixin
    import inspect

    src = inspect.getsource(getattr(WritesMixin, method_name))
    assert f'data["status"] = "{expected_status}"' in src, (
        f"{method_name} must hard-code status=\"{expected_status}\" "
        f"in the request body"
    )