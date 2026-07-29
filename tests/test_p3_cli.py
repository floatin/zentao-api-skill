"""Tests for P3: cli.py rewrite using argparse + command dispatch.

cli.py was 557 lines of Chinese-keyword regex parsing + 12 near-identical
cmd_* functions. After P3 it should:
- use argparse for both subcommand and parameter parsing
- dispatch commands via a dict (no if/elif chain in main)
- skip the hand-rolled format_table
"""
from __future__ import annotations

import argparse
import inspect
import sys
from unittest.mock import patch, MagicMock

import pytest


# ---------- argparse-based entry point --------------------------------------


def test_cli_builds_argparser():
    """cli.py must expose a function that builds an argparse.ArgumentParser."""
    from zentao_api import cli

    assert hasattr(cli, "build_parser"), "cli.py must expose build_parser()"
    parser = cli.build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_parser_lists_products_subcommand():
    from zentao_api import cli

    parser = cli.build_parser()
    # argparse with subparsers should accept 'products'
    args = parser.parse_args(["products"])
    assert args.command == "products"


def test_parser_accepts_project_filter_for_projects():
    from zentao_api import cli

    parser = cli.build_parser()
    args = parser.parse_args(["projects", "--status", "doing"])
    assert args.command == "projects"
    assert args.status == "doing"


def test_parser_accepts_project_id_for_stories():
    from zentao_api import cli

    parser = cli.build_parser()
    args = parser.parse_args(["stories", "--project-id", "176"])
    assert args.command == "stories"
    assert args.project_id == "176"


def test_parser_accepts_execution_id_for_tasks():
    from zentao_api import cli

    parser = cli.build_parser()
    args = parser.parse_args(["tasks", "--execution-id", "200"])
    assert args.command == "tasks"
    assert args.execution_id == "200"


def test_parser_accepts_product_id_for_bugs():
    from zentao_api import cli

    parser = cli.build_parser()
    args = parser.parse_args(["bugs", "--product-id", "21"])
    assert args.command == "bugs"
    assert args.product_id == "21"


def test_parser_accepts_create_story_args():
    from zentao_api import cli

    parser = cli.build_parser()
    args = parser.parse_args([
        "create-story",
        "--product-id", "21",
        "--execution-id", "200",
        "--title", "登录流程",
        "--module", "[模块1]",
    ])
    # argparse keeps the subcommand name verbatim (including the hyphen).
    assert args.command == "create-story"
    assert args.title == "登录流程"


# ---------- dispatch dict ---------------------------------------------------


def test_cli_uses_command_dispatch_dict():
    """main() must dispatch via a COMMANDS dict, not an if/elif chain."""
    from zentao_api import cli

    main_src = inspect.getsource(cli.main)
    # The dispatch dict has the pattern: COMMANDS = {...}
    assert "COMMANDS" in main_src or "DISPATCH" in main_src or "_DISPATCH" in main_src, (
        "cli.main must use a command dispatch dict (COMMANDS / DISPATCH / etc.)"
    )


def test_dispatch_dict_handles_every_subcommand():
    """Every subcommand the parser knows about must have an entry in the
    dispatch dict, otherwise it'll silently no-op."""
    from zentao_api import cli

    parser = cli.build_parser()
    # Each subparser's choices
    sub_names = set()
    for action in parser._actions:
        sp = getattr(action, "choices", None)
        if isinstance(sp, dict):
            sub_names.update(sp.keys())

    dispatch = getattr(cli, "COMMANDS", None) or getattr(cli, "DISPATCH", None) or getattr(cli, "_DISPATCH", None)
    assert dispatch is not None, "cli must expose a dispatch dict"
    missing = sub_names - set(dispatch.keys())
    assert not missing, f"subcommands without dispatch handlers: {missing}"


# ---------- cmd_* functions trimmed -----------------------------------------


def test_cmd_lines_count_reduced():
    """The 12 cmd_* functions should collectively be much smaller than
    the original ~250 lines of near-identical boilerplate."""
    from zentao_api import cli

    cmd_funcs = [
        (name, obj) for name, obj in inspect.getmembers(cli, inspect.isfunction)
        if name.startswith("cmd_")
    ]
    total_lines = sum(
        len(inspect.getsource(obj).splitlines()) for _, obj in cmd_funcs
    )
    # The original 12 cmd_* functions totalled ~250 lines.
    # After P3 they were ~165, then P8 added 8 task-status commands (now 20),
    # then P9 added 8 bug/story-status commands (now 28). Bump ceiling.
    assert total_lines < 310, (
        f"cmd_* functions still total {total_lines} lines (should be < 280)"
    )


def test_cmd_runs_against_mocked_client():
    """A single cmd should be invokable with a mock client and not crash."""
    from zentao_api import cli

    mock_client = MagicMock()
    mock_client.get_products.return_value = (True, [{"id": "1", "name": "Foo"}])
    mock_client.get_product_list_old.return_value = {}

    dispatch = getattr(cli, "COMMANDS", None) or getattr(cli, "DISPATCH", None) or getattr(cli, "_DISPATCH", None)
    handler = dispatch["products"]
    # cmd handlers take (client, args); pass a MagicMock for args.
    handler(mock_client, MagicMock())


def test_cli_help_lists_subcommands():
    """`--help` should list every subcommand."""
    from zentao_api import cli

    parser = cli.build_parser()
    help_text = parser.format_help()
    for cmd in ("products", "projects", "executions", "stories",
                "tasks", "bugs", "create-story"):
        assert cmd in help_text, f"--help missing subcommand: {cmd}"