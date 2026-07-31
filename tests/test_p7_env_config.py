"""Tests for P7: replace TOOLS.md-based credential reading with a .env file.

The CLI now:
- accepts ``--env-file PATH`` (defaults to ``~/.config/zentao-cli/.env``)
- never checks credentials during ``--help``
- returns a clear error message when the env file is missing or incomplete
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------- read_credentials: .env parsing ---------------------------------


def test_read_credentials_parses_simple_env(tmp_path):
    """The .env format is ``KEY=VALUE`` per line, with # comments."""
    from zentao_api.client import read_credentials

    env = tmp_path / "zentao.env"
    env.write_text(
        "# Generated config\n"
        "endpoint=http://example.com\n"
        "username=alice\n"
        "password=secret123\n"
    )
    creds = read_credentials(env)
    assert creds == {
        "endpoint": "http://example.com",
        "username": "alice",
        "password": "secret123",
    }


def test_read_credentials_handles_quoted_values(tmp_path):
    """Quoted values are common in .env files; quotes must be stripped."""
    from zentao_api.client import read_credentials

    env = tmp_path / "zentao.env"
    env.write_text(
        'endpoint="http://example.com/zentao"\n'
        "username='alice'\n"
        "password=secret\n"
    )
    creds = read_credentials(env)
    assert creds["endpoint"] == "http://example.com/zentao"
    assert creds["username"] == "alice"


def test_read_credentials_returns_none_when_file_missing(tmp_path):
    from zentao_api.client import read_credentials
    assert read_credentials(tmp_path / "missing.env") is None


def test_read_credentials_returns_none_when_keys_incomplete(tmp_path):
    """An env file that lacks any required key is treated as missing."""
    from zentao_api.client import read_credentials

    env = tmp_path / "zentao.env"
    env.write_text("endpoint=http://x\n")  # missing username + password
    assert read_credentials(env) is None


def test_read_credentials_ignores_comments_and_blank_lines(tmp_path):
    from zentao_api.client import read_credentials

    env = tmp_path / "zentao.env"
    env.write_text(
        "\n"
        "# this is a comment\n"
        "  \n"
        "endpoint=http://x\n"
        "# inline comment\n"
        "username=u\n"
        "password=p\n"
    )
    creds = read_credentials(env)
    assert creds["username"] == "u"


def test_read_credentials_default_path_uses_home_config(tmp_path, monkeypatch):
    """When no path is given, default to ``~/.config/zentao-cli/.env``."""
    from zentao_api.client import read_credentials

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    config_dir = tmp_path / ".config" / "zentao-cli"
    config_dir.mkdir(parents=True)
    (config_dir / ".env").write_text(
        "endpoint=http://default\nusername=def\npassword=p\n"
    )
    creds = read_credentials()
    assert creds["endpoint"] == "http://default"


# ---------- CLI: --help must not trigger credential check -------------------


def test_help_exits_zero_without_credentials(monkeypatch, capsys):
    """``zentao --help`` must not require or even check credentials.

    argparse's --help calls ``sys.exit(0)``, so we catch SystemExit.
    """
    from zentao_api import cli

    # Make read_credentials blow up — if main() calls it on --help,
    # the test fails because the AssertionError propagates instead of SystemExit.
    def boom():
        raise AssertionError("read_credentials should not be called for --help")

    monkeypatch.setattr(cli, "read_credentials", boom)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0


def test_help_for_subcommand_exits_zero_without_credentials(monkeypatch, capsys):
    """``zentao products --help`` must also skip credential check."""
    from zentao_api import cli

    def boom():
        raise AssertionError("read_credentials should not be called for --help")

    monkeypatch.setattr(cli, "read_credentials", boom)
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["products", "--help"])
    assert excinfo.value.code == 0


# ---------- CLI: --env-file wiring -----------------------------------------


def test_cli_accepts_env_file_flag():
    """The parser must accept ``--env-file PATH``."""
    from zentao_api import cli

    parser = cli.build_parser()
    args = parser.parse_args(["--env-file", "/tmp/x.env", "products"])
    assert args.env_file == Path("/tmp/x.env")


def test_cli_uses_default_env_path_when_flag_omitted(monkeypatch):
    """When ``--env-file`` is omitted, ``args.env_file`` is None so the
    default (~/.config/zentao-cli/.env) kicks in inside main()."""
    from zentao_api import cli

    parser = cli.build_parser()
    args = parser.parse_args(["products"])
    assert args.env_file is None


def test_cli_help_lists_env_file_option():
    """--env-file must appear in --help so users can discover it."""
    from zentao_api import cli

    parser = cli.build_parser()
    help_text = parser.format_help()
    assert "--env-file" in help_text


def test_cli_uses_credentials_from_env_file(tmp_path, monkeypatch):
    """The .env file is read; ZenTaoClient is constructed from its values;
    a mock method then runs without crashing."""
    from zentao_api import cli

    env = tmp_path / "zentao.env"
    env.write_text(
        "endpoint=http://envhost/zentao\n"
        "username=envuser\n"
        "password=envpass\n"
    )
    mock_client = MagicMock()
    mock_client.get_products.return_value = (True, [])

    # Track constructor args without monkeypatching (use a sentinel factory).
    captured: Dict[str, tuple] = {}

    def factory(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return mock_client

    monkeypatch.setattr(cli, "ZenTaoClient", factory)

    rc = cli.main(["--env-file", str(env), "products"])
    assert rc == 0
    assert captured["args"] == ("http://envhost/zentao", "envuser", "envpass")


def test_cli_errors_clearly_when_env_file_missing(tmp_path, capsys, monkeypatch):
    """No env file and no flag ⇒ clear error pointing to the default path."""
    from zentao_api import cli
    from zentao_api.client import _credentials

    # Make Path.home() resolve into a fake empty directory.
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(_credentials.Path, "home", lambda: tmp_path)

    with pytest.raises(SystemExit) as ei:
        cli.main(["products"])
    assert ei.value.code == 1

    captured = capsys.readouterr()
    # error is a JSON envelope on stderr (code-friendly output)
    import json
    payload = json.loads(captured.err)
    assert payload["status"] == "error"
    assert "endpoint" in str(payload["error"])


# ---------- TOOLS.md is no longer referenced --------------------------------


def test_tools_md_no_longer_referenced():
    """The cli / credentials module must not import or read TOOLS.md at
    runtime. Docstring mentions of "old TOOLS.md reader" are fine."""
    from zentao_api import cli

    src = open(cli.__file__, encoding="utf-8").read()
    # Strip the module docstring so historical references in docs don't count.
    non_doc = src.split('"""', 2)[-1] if '"""' in src else src
    assert "TOOLS.md" not in non_doc, "TOOLS.md was removed as a credential source"

    from zentao_api.client import _credentials
    creds_src = open(_credentials.__file__, encoding="utf-8").read()
    creds_non_doc = creds_src.split('"""', 2)[-1] if '"""' in creds_src else creds_src
    assert "TOOLS.md" not in creds_non_doc