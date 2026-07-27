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


def test_create_story_url_uses_0_when_module_default(client):
    captured = {}

    def fake(method, path, data=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(product_id="35", title="x")

    assert captured["method"] == "POST"
    # 9-segment URL: product-module-story-plan-execution-branch-module-type
    assert captured["path"] == "/story-create-35-0-0-0-0-0-0-0-story.json"


# ---------- body must NOT carry module=0 / plan=0 -----------------------


def test_create_story_body_omits_module_zero(client):
    """The reported bug: server rejects ``module=0`` in the body."""
    captured = {}

    def fake(method, path, data=None):
        captured["data"] = data or {}
        return True, {"status": "success", "data": '{"id": 1}'}

    with patch.object(client, "old_request", side_effect=fake):
        client.create_story(product_id="35", title="x")

    assert "module" not in captured["data"], (
        f"module should be omitted when defaulted to '0', got body: {captured['data']}"
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
    # URL also embeds the real module id in both positions.
    # Pattern: /story-create-{p}-{m}-0-{plan}-{exec}-{branch}-{m}-0-story.json
    # With m=505: /story-create-35-505-0-0-0-0-505-0-story.json
    assert "505" in captured["path"]
    # module appears twice in URL (positions 2 and 7) when set.
    assert captured["path"].count("505") == 2


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
    # execution_id/plan/branch are named params (used in URL), not body
    # module/plan omitted from body because defaulted to "0"
    assert "module" not in captured["data"]
    assert "plan" not in captured["data"]
    # reviewer goes through **kwargs
    assert captured["data"]["reviewer"] == "alice"