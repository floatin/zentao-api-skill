"""Read ZenTao credentials from a .env file.

Replaces the old TOOLS.md-based reader. The .env format is::

    # comment
    endpoint=http://example.com/zentao
    username=alice
    password=secret

Quotes around values are stripped. Empty lines and ``#`` lines are ignored.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict


def default_env_path() -> Path:
    """Return ``~/.config/zentao-cli/.env``, evaluated lazily so monkeypatch
    on ``Path.home()`` works in tests.
    """
    return Path.home() / ".config" / "zentao-cli" / ".env"


def read_credentials(env_path: Optional[Path] = None) -> Optional[Dict[str, str]]:
    """Return ``{endpoint, username, password}`` from ``env_path``.

    Args:
        env_path: Path to the .env file. Defaults to
            ``~/.config/zentao-cli/.env`` when ``None``.

    Returns:
        A dict with the three keys, or ``None`` if any is missing or the
        file doesn't exist.
    """
    path = Path(env_path) if env_path is not None else default_env_path()
    if not path.exists():
        return None

    creds: Dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        creds[key.strip()] = value.strip().strip('"').strip("'")

    if all(k in creds for k in ("endpoint", "username", "password")):
        return {
            "endpoint": creds["endpoint"],
            "username": creds["username"],
            "password": creds["password"],
        }
    return None