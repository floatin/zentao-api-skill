"""Regression test for the create_story module=0 body issue.

The old default ``module: str = "0"`` meant the POST body always carried
``{"module": "0", ...}`` which ZenTao's old API rejects. The URL keeps ``0``
as a positional placeholder, but the body must omit module/plan when
they're not provided.

After P6 the rule is:
- ``module="0"`` (default) → omitted from POST body, still in URL
- ``module="123"`` (real ID) → both in URL and in POST body
- Same for ``plan``
"""
from __future__ import annotations

from unittest.mock import patch

import pytest


# ---------- URL is unchanged (still uses 0 placeholder) --------------------


def test_create_story_url_always_uses_0_for_module_positions(client):
    """P10: URL module positions are always ``0`` (positional placeholders).
    The real module value goes in the POST body only."""
    captured = {}

    def fake(method, path, data=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(product_id="35", title="x", module="[模块1]")

    assert captured["method"] == "POST"
    # URL always uses 0 for module positions regardless of module value.
    assert captured["path"] == "/story-create-35-0-0-0-0-0-0-0-story.json"
    # Real module is in the body.
    assert captured["data"]["module"] == "[模块1]"


# ---------- body must NOT carry module=0 / plan=0 -----------------------


def test_create_story_body_always_includes_module(client):
    """P10: module is always sent in the POST body — server requires it.
    Default ``"0"`` is fine in the body (it's the root module)."""
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(product_id="35", title="x")

    assert "module" in captured["data"], (
        f"module must always be in body, got: {captured['data']}"
    )


def test_create_story_body_omits_plan_zero(client):
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(product_id="35", title="x")

    assert "plan" not in captured["data"], (
        f"plan should be omitted when defaulted to '0', got body: {captured['data']}"
    )


# ---------- when real ID passed, both URL and body carry it ---------------


def test_create_story_includes_real_module_in_body(client):
    captured = {}

    def fake(method, path, data=None):
        captured["path"] = path
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(product_id="35", title="x", module="505")

    assert captured["data"]["module"] == "505"
    # P10: URL always uses 0 for module positions (real value in body only).
    assert "505" not in captured["path"]


def test_create_story_includes_real_plan_in_body(client):
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(product_id="35", title="x", plan="12")

    assert captured["data"]["plan"] == "12"


# ---------- required fields are still present ------------------------------


def test_create_story_body_has_required_fields(client):
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(
            product_id="35",
            title="登录流程",
            execution_id="200",
            plan="0",
            reviewer="alice",
        )

    assert captured["data"]["product"] == "35"
    assert captured["data"]["title"] == "登录流程"
    # module is always in body (server requires it); plan omitted when "0".
    assert captured["data"]["module"] == "0"
    assert "plan" not in captured["data"]
    # reviewer is dropped from the create body — it belongs on
    # review-story, not on the INSERT into zt_story (no such column).
    assert "reviewer" not in captured["data"]


# ---------- review_story must include reviewedBy + reviewedDate ---------


def test_review_story_body_includes_reviewer_and_date(client):
    captured = {}

    def fake(method, path, data=None):
        captured["path"] = path
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"result": "success"}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.review_story("10701", "pass", comment="通过")

    assert captured["path"] == "/story-review-10701.json"
    assert captured["data"]["result"] == "pass"
    assert captured["data"]["comment"] == "通过"
    # reviewedBy defaults to the logged-in user
    assert captured["data"]["reviewedBy"] == client.username
    # reviewedDate is current time in ZenTao's format
    assert "reviewedDate" in captured["data"]
    assert len(captured["data"]["reviewedDate"]) == 19  # YYYY-MM-DD HH:MM:SS


def test_review_story_accepts_explicit_reviewer(client):
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"result": "success"}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.review_story("10701", "pass", reviewed_by="alice")

    assert captured["data"]["reviewedBy"] == "alice"


# ---------- create_tasks must include developEnd[0] -------------------


def test_create_tasks_body_includes_develop_end(client):
    """Without `developEnd[0]` the server returns 422 '任务方不能为空'."""
    from zentao_api.client.writes import WritesMixin

    captured = {}

    def fake(method, path, data=None):
        captured["path"] = path
        captured["data"] = data or {}
        return True, {"result": "success", "message": "保存成功"}

    with patch.object(client, "old_request", side_effect=fake):
        # Direct call to the batch helper (create_task delegates to it).
        WritesMixin.create_tasks(
            client,
            project="281",
            story_id="10770",
            tasks=[{"name": "sub", "assignedTo": "huaimin"}],
        )

    assert captured["path"] == "/task-batchCreate-281-10770-0-0.json"
    assert captured["data"]["developEnd[0]"] == "0"
    assert captured["data"]["name[0]"] == "sub"
    assert captured["data"]["assignedTo[0]"] == "huaimin"


def test_create_tasks_honors_explicit_develop_end(client):
    from zentao_api.client.writes import WritesMixin

    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"result": "success", "message": "保存成功"}

    with patch.object(client, "old_request", side_effect=fake):
        WritesMixin.create_tasks(
            client,
            project="281",
            tasks=[{"name": "x", "developEnd": "125"}],
        )

    assert captured["data"]["developEnd[0]"] == "125"