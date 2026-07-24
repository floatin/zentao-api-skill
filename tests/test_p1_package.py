"""Tests for P1: the zentao_api.client split into a package.

These tests pin the public surface so future refactors don't accidentally
break the facade contract that cli.py relies on.
"""
from __future__ import annotations

import inspect

import zentao_api.client as client_pkg
from zentao_api.client import ZenTaoClient, read_credentials
from zentao_api.client._credentials import read_credentials as creds_fn


# ---------- package shape ----------------------------------------------------


def test_client_is_a_package():
    """The old single-file module must now be a package."""
    import os

    pkg_path = os.path.dirname(client_pkg.__file__)
    assert os.path.isdir(pkg_path), "client must be a package directory now"
    assert os.path.isfile(os.path.join(pkg_path, "__init__.py"))


def test_zenTaoClient_exported_from_package_root():
    """Backwards-compat: cli.py imports `from zentao_api.client import ZenTaoClient`."""
    assert hasattr(client_pkg, "ZenTaoClient")
    assert hasattr(client_pkg, "read_credentials")


def test_read_credentials_reexported_in_own_module():
    """read_credentials should also be importable from its own module."""
    assert creds_fn is read_credentials


# ---------- facade composition ----------------------------------------------


def test_zenTaoClient_is_mixin_composed():
    """ZenTaoClient must inherit from BaseClient + all resource mixins."""
    mro = inspect.getmro(ZenTaoClient)
    expected_mixins = {
        "BaseClient",
        "ProductsMixin",
        "ProjectsMixin",
        "StoriesMixin",
        "TasksMixin",
        "BugsMixin",
        "QAMixin",
        "ReleasesMixin",
        "BuildsMixin",
        "PlansMixin",
    }
    actual_mixins = {c.__name__ for c in mro}
    missing = expected_mixins - actual_mixins
    assert not missing, f"missing mixins: {missing}"


# ---------- method preservation ---------------------------------------------


# Spot-check methods from each mixin survive the split. Picking a few that
# cover the major resources without enumerating all 100+.
PRESERVED_METHODS = [
    ("ProductsMixin", "get_products"),
    ("ProductsMixin", "create_product"),
    ("ProjectsMixin", "get_project"),
    ("ProjectsMixin", "create_project"),
    ("StoriesMixin", "create_story"),
    ("StoriesMixin", "review_story"),
    ("TasksMixin", "create_task"),
    ("TasksMixin", "cancel_task"),
    ("BugsMixin", "create_bug"),
    ("BugsMixin", "resolve_bug"),
    ("QAMixin", "create_testcase"),
    ("QAMixin", "create_testsuite"),
    ("ReleasesMixin", "create_release"),
    ("BuildsMixin", "create_build"),
    ("PlansMixin", "create_plan"),
    ("BaseClient", "get_session"),
    ("BaseClient", "old_request"),
]


def test_preserved_methods_exist_on_client():
    for mixin_name, method_name in PRESERVED_METHODS:
        assert hasattr(ZenTaoClient, method_name), (
            f"{method_name} ({mixin_name}) missing from ZenTaoClient"
        )


def test_init_signature_preserved():
    """The original __init__ signature must survive the split."""
    sig = inspect.signature(ZenTaoClient.__init__)
    params = [p for p in sig.parameters.keys() if p != "self"]
    assert params[:3] == ["endpoint", "username", "password"], params
    assert "session_dir" in params
    assert "auto_save" in params
    assert "auto_load" in params


# ---------- CLI import smoke -------------------------------------------------


def test_cli_can_still_import_client():
    """cli.py's `from zentao_api.client import ZenTaoClient, read_credentials`."""
    from zentao_api import cli  # noqa: F401

    assert cli.ZenTaoClient is ZenTaoClient
    assert cli.read_credentials is read_credentials