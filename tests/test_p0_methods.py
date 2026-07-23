"""Tests for the P0 missing-method additions to ZenTaoClient.

The CLI calls a number of methods that did not exist on ZenTaoClient.
These tests pin the expected signatures and return shapes using a mocked
old_request, so no network access is required.
"""
from __future__ import annotations

import inspect
import json
from unittest.mock import patch

import pytest


def _make_payload(inner):
    """Wrap an inner dict/list as the server-side payload returned by old_request."""
    return {"status": "success", "data": json.dumps(inner)}


# ---------- get_projects -----------------------------------------------------


def test_get_projects_calls_expected_endpoint_and_returns_list(client):
    captured = {}

    def fake(method, path, data=None):
        captured["method"] = method
        captured["path"] = path
        return True, _make_payload({"projects": [{"id": "1", "name": "Alpha"}]})

    with patch.object(client, "old_request", side_effect=fake):
        ok, projects = client.get_projects(status="doing")

    assert ok is True
    assert captured["method"] == "GET"
    assert "doing" in captured["path"]
    assert isinstance(projects, list)
    assert projects[0]["id"] == "1"


# ---------- get_executions ---------------------------------------------------


def test_get_executions_returns_list(client):
    with patch.object(
        client,
        "old_request",
        return_value=(True, _make_payload({"executions": [{"id": "7", "name": "Sprint 1"}]})),
    ):
        ok, executions = client.get_executions("176")

    assert ok is True
    assert isinstance(executions, list)
    assert executions[0]["name"] == "Sprint 1"


# ---------- get_stories ------------------------------------------------------


def test_get_stories_returns_list(client):
    with patch.object(
        client,
        "old_request",
        return_value=(True, _make_payload({"stories": [{"id": "9", "title": "Login flow"}]})),
    ):
        ok, stories = client.get_stories("176")

    assert ok is True
    assert isinstance(stories, list)
    assert stories[0]["title"] == "Login flow"


# ---------- get_tasks --------------------------------------------------------


def test_get_tasks_returns_list(client):
    with patch.object(
        client,
        "old_request",
        return_value=(True, _make_payload({"tasks": [{"id": "4", "name": "Wire up DB"}]})),
    ):
        ok, tasks = client.get_tasks("200")

    assert ok is True
    assert isinstance(tasks, list)
    assert tasks[0]["name"] == "Wire up DB"


# ---------- get_bugs ---------------------------------------------------------


def test_get_bugs_returns_list(client):
    with patch.object(
        client,
        "old_request",
        return_value=(True, _make_payload({"bugs": [{"id": "11", "title": "Crash on save"}]})),
    ):
        ok, bugs = client.get_bugs("21")

    assert ok is True
    assert isinstance(bugs, list)
    assert bugs[0]["title"] == "Crash on save"


# ---------- get_productplans -------------------------------------------------


def test_get_productplans_returns_list_of_dicts(client):
    """The legacy _old helper returns a {name: id} dict; the new method
    normalises that into [{id, title}, ...]."""
    with patch.object(
        client,
        "get_productplan_list_old",
        return_value={"1.0 release": "12", "2.0 release": "13"},
    ):
        ok, plans = client.get_productplans("21")

    assert ok is True
    assert isinstance(plans, list)
    assert {"id", "title"} <= set(plans[0].keys())
    titles = {p["title"] for p in plans}
    assert titles == {"1.0 release", "2.0 release"}


# ---------- batch_create_tasks ----------------------------------------------


def test_batch_create_tasks_delegates_to_create_tasks(client):
    with patch.object(
        client,
        "create_tasks",
        return_value=(True, {"message": "ok"}),
    ) as mocked:
        ok, result = client.batch_create_tasks(
            execution_id="200",
            parent_id="4",
            tasks=[{"name": "t1"}, {"name": "t2"}],
        )

    assert ok is True
    assert result == {"message": "ok"}
    assert mocked.called


# ---------- create_productplan ----------------------------------------------


def test_create_productplan_delegates_to_create_plan(client):
    with patch.object(
        client,
        "create_plan",
        return_value=(True, {"id": "55", "message": "ok"}),
    ) as mocked:
        ok, result = client.create_productplan("21", "Q3 plan")

    assert ok is True
    assert result["id"] == "55"
    args, kwargs = mocked.call_args
    # Either positional or keyword; both are fine as long as create_plan received
    # the product_id and title.
    assert "21" in (args + tuple(kwargs.values()))
    assert "Q3 plan" in (args + tuple(kwargs.values()))


# ---------- all new methods exist -------------------------------------------


@pytest.mark.parametrize(
    "method_name",
    [
        "get_projects",
        "get_executions",
        "get_stories",
        "get_tasks",
        "get_bugs",
        "get_productplans",
        "batch_create_tasks",
        "create_productplan",
    ],
)
def test_method_exists_on_client(client, method_name):
    assert hasattr(client, method_name), f"missing method: {method_name}"
    assert callable(getattr(client, method_name))