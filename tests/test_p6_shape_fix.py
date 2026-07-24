"""Tests for P6: collection-shape normalisation + get_product_list_old dict handling.

Bugs found during the live smoke test on zentao.yishou.com:
- ``_data(path, key)`` returns whatever the server gave (dict or list). The
  contract is a list of dicts, so dict-of-dict and dict-of-scalar shapes must
  be normalised.
- ``get_product_list_old()`` crashes when the server returns products as a
  ``{id: name}`` dict instead of a list of ``{id, name}`` dicts.
"""
from __future__ import annotations

import json
from unittest.mock import patch


def _ok(inner):
    """Wrap inner data as old_request's envelope."""
    return (True, {"status": "success", "data": json.dumps(inner, ensure_ascii=False)})


# ---------- _data normalisation --------------------------------------------


def test_data_normalises_dict_of_dict_to_list_with_id(client):
    """When the server returns ``{id: {field: value}}``, ``_data`` should
    produce ``[{id, field: value}, ...]``."""
    payload = {"stories": {"10701": {"title": "Foo"}, "10702": {"title": "Bar"}}}
    with patch.object(client, "old_request", return_value=_ok(payload)):
        result = client._data("/story-list.json", "stories")
    assert result == [
        {"id": "10701", "title": "Foo"},
        {"id": "10702", "title": "Bar"},
    ]


def test_data_keeps_list_shape_unchanged(client):
    """When the server already returns a list, ``_data`` passes it through."""
    payload = {"items": [{"id": "1"}, {"id": "2"}]}
    with patch.object(client, "old_request", return_value=_ok(payload)):
        result = client._data("/x.json", "items")
    assert result == [{"id": "1"}, {"id": "2"}]


def test_data_normalises_dict_of_string_to_list_of_id_name(client):
    """When the server returns ``{id: "name"}`` (value is a scalar), ``_data``
    should still produce ``[{id, name}, ...]`` so the CLI's table printer
    can iterate over rows."""
    payload = {"products": {"35": "AI选得准", "34": "Foo"}}
    with patch.object(client, "old_request", return_value=_ok(payload)):
        result = client._data("/x.json", "products")
    assert result == [
        {"id": "35", "name": "AI选得准"},
        {"id": "34", "name": "Foo"},
    ]


def test_data_returns_empty_list_when_missing_key(client):
    payload = {"other": "x"}
    with patch.object(client, "old_request", return_value=_ok(payload)):
        assert client._data("/x.json", "missing") == []


# ---------- get_product_list_old -------------------------------------------


def test_get_product_list_old_handles_dict_of_string(client):
    """Server returns ``products`` as ``{id: "name"}`` — flip to ``{name: id}``."""
    payload = {"products": {"35": "AI选得准", "34": "Foo"}}
    with patch.object(client, "old_request", return_value=_ok(payload)):
        result = client.get_product_list_old()
    assert result == {"AI选得准": "35", "Foo": "34"}


def test_get_product_list_old_handles_list_of_dicts(client):
    """Backwards-compat: if some day the server returns a list, still works."""
    payload = {
        "products": [
            {"id": "35", "name": "AI选得准"},
            {"id": "34", "name": "Foo"},
        ]
    }
    with patch.object(client, "old_request", return_value=_ok(payload)):
        result = client.get_product_list_old()
    assert result == {"AI选得准": "35", "Foo": "34"}


# ---------- get_products / get_stories integration -------------------------


def test_get_products_returns_list_of_dicts(client):
    """Server returns ``{id: name}`` but the return contract is a list."""
    payload = {"products": {"35": "AI选得准"}}
    with patch.object(client, "old_request", return_value=_ok(payload)):
        ok, result = client.get_products()
    assert ok is True
    assert isinstance(result, list)
    assert result == [{"id": "35", "name": "AI选得准"}]


def test_get_stories_returns_list_of_dicts(client):
    """Server returns ``{id: {...}}`` but the return contract is a list."""
    payload = {"stories": {"10701": {"title": "Foo", "status": "active"}}}
    with patch.object(client, "old_request", return_value=_ok(payload)):
        ok, result = client.get_stories("45")
    assert ok is True
    assert isinstance(result, list)
    assert result == [{"id": "10701", "title": "Foo", "status": "active"}]


# ---------- CLI compatibility ---------------------------------------------


def test_cli_cmd_products_iterates_rows_when_server_returns_dict_shape(client):
    """Regression: cli.cmd_products must print a table when get_products
    returns list-of-dicts (the post-P5 normalise contract)."""
    from zentao_api import cli

    # Patch the bound method so cmd_products sees our list.
    client.get_products = lambda: (True, [{"id": "35", "name": "Foo"}])
    client.get_product_list_old = lambda: {}

    # Capture stdout.
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.cmd_products(client, MagicMockNamespace())
    out = buf.getvalue()
    assert "Foo" in out
    assert "35" in out


class MagicMockNamespace:
    """Stand-in for argparse.Namespace that returns None for any attribute."""
    def __getattr__(self, name):
        return None