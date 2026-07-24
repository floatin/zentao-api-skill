"""Tests for P5: _data / _data_dict / _data_unwrap refactor across all mixins.

Each test pins the behaviour of one refactored method: a mocked old_request
returns a payload, and the method must hand back the relevant slice.
These are regression guards so future edits don't accidentally fall back to
the verbose json.loads boilerplate.
"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest


def _ok(inner):
    """Wrap an inner dict/list as old_request's envelope."""
    return (True, {"status": "success", "data": json.dumps(inner, ensure_ascii=False)})


# ---------- list returns use _data ------------------------------------------


@pytest.mark.parametrize(
    "method_name, path, key, inner_key",
    [
        ("get_executions", "/project-execution-{id}.json", "executions", "176"),
        ("get_stories", "/project-story-{id}.json", "stories", "176"),
        ("get_tasks", "/execution-task-{id}.json", "tasks", "200"),
        ("get_bugs", "/product-bug-{id}.json", "bugs", "21"),
        ("get_products", "/product-all.json", "products", None),
        ("get_project_bugs", "/project-bug-{id}.json", "bugs", "176"),
        ("get_story_bugs", "/story-bugs-{id}.json", "bugs", "123"),
        ("get_story_cases", "/story-cases-{id}.json", "cases", "123"),
        ("get_task_subtasks", "/task-viewSubtasks-{id}.json", "children", "100"),
        ("get_task_history", "/task-history-{id}.json", "history", "9"),
        ("get_releases", "/release-browse-{id}.json", "releases", "21"),
        ("get_project_team", "/project-team-{id}.json", "team", "176"),
        ("get_my_projects", "/my-project.json", "projects", None),
    ],
)
def test_method_uses__data_list_helper(client, method_name, path, key, inner_key):
    """The refactored method must return ``(True, _data(path, key))`` so the
    underlying _data helper handles the json.loads unwrap.

    Payload shape is a list to match the post-P6 normalise contract — the
    server returns list-of-dict for most collection endpoints.
    """
    sentinel = [{"id": "x", "name": "y"}]

    def fake_old(method, actual_path, data=None):
        if inner_key:
            assert inner_key in actual_path, f"{method_name} called with wrong path: {actual_path}"
        return True, _ok({key: sentinel})[1]

    with patch.object(client, "old_request", side_effect=fake_old):
        method = getattr(client, method_name)
        if inner_key:
            ok, result = method(inner_key)
        else:
            ok, result = method()

    assert ok is True
    assert result == sentinel


@pytest.mark.parametrize(
    "method_name, path, key, inner_id",
    [
        ("get_product", "/product-view-{id}.json", "product", "1"),
        ("get_story", "/story-view-{id}.json", "story", "123"),
        ("get_bug", "/bug-view-{id}.json", "bug", "11"),
        ("get_project", "/project-view-{id}.json", "project", "176"),
        ("get_testcase", "/testcase-view-{id}.json", "case", "1"),
        ("get_testsuite", "/testsuite-view-{id}.json", "suite", "1"),
        ("get_testtask", "/testtask-view-{id}.json", "task", "1"),
        ("get_release", "/release-view-{id}.json", "release", "5"),
        ("get_build", "/build-view-{id}.json", "build", "5"),
        ("get_plan", "/productplan-view-{id}.json", "plan", "5"),
    ],
)
def test_method_uses__data_dict_helper(client, method_name, path, key, inner_id):
    """Single-dict endpoints must use _data_dict, which returns {} on failure."""
    sentinel = {"__sentinel__": True}

    def fake_old(method, actual_path, data=None):
        assert inner_id in actual_path
        return True, _ok({key: sentinel})[1]

    with patch.object(client, "old_request", side_effect=fake_old):
        method = getattr(client, method_name)
        ok, result = method(inner_id)

    assert ok is True
    assert result == sentinel


# ---------- the _data helpers themselves ------------------------------------


def test_data_unwrap_returns_inner_dict(client):
    """_data_unwrap is for transformation methods (the *_list_old family)."""
    with patch.object(
        client,
        "old_request",
        return_value=_ok({"products": [{"id": "1", "name": "Foo"}]}),
    ):
        result = client._data_unwrap("/anything.json")
    assert result == {"products": [{"id": "1", "name": "Foo"}]}


def test_data_unwrap_returns_empty_on_failure(client):
    with patch.object(client, "old_request", return_value=(False, "boom")):
        assert client._data_unwrap("/x.json") == {}


# ---------- regression: smoke-test legacy _old methods still work -----------


def test_get_product_list_old_uses_unwrap(client):
    """The 4 legacy methods still transform results via _data_unwrap."""
    with patch.object(
        client,
        "old_request",
        return_value=_ok({"products": [{"id": "1", "name": "X"}]}),
    ):
        result = client.get_product_list_old()
    assert result == {"X": "1"}


def test_get_bug_list_old_returns_direct_list(client):
    """get_bug_list_old returns the bare list, not wrapped in (success, data)."""
    payload = [{"id": "1", "title": "Bug"}]
    with patch.object(
        client,
        "old_request",
        return_value=(True, {"status": "success", "data": json.dumps(payload)}),
    ):
        result = client.get_bug_list_old("21")
    assert result == payload