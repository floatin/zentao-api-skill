#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""禅道项目管理命令行工具。

输出约定（对代码/API 调用友好，参照 baserow-cli）：
  - stdout: 永远是合法 JSON（数据对象/数组，或带 status 的 envelope）。
  - stderr: 人类可读日志、确认提示、错误 envelope。
  - exit code: 0=成功或用户取消, 1=API/网络/认证错误, 2=非交互式拒绝执行。
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Dict, Tuple

from zentao_api.client import ZenTaoClient, read_credentials
from zentao_api.client._credentials import default_env_path


# ---------- output helpers --------------------------------------------------


def _jdump(obj) -> None:
    """Print valid JSON to stdout."""
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _err_exit(data, code: int = 1) -> None:
    """Print JSON error envelope to stderr and exit non-zero.

    `data` may be a dict (API error body), a string (network/auth message),
    or any other value — normalized into an `error` field.
    """
    if isinstance(data, dict):
        payload = {"status": "error", "error": data}
    else:
        payload = {"status": "error", "error": str(data)}
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def _deny_to_error(result):
    """Normalize a user-deny result into an error string, else None."""
    import json as _json
    if not isinstance(result, dict):
        return None
    try:
        inner = _json.loads(result.get("data", "{}"))
    except (ValueError, TypeError):
        return None
    if "user-deny" in inner.get("locate", ""):
        return "无权限操作"
    return None


def _confirm(args, name, details) -> bool:
    """Confirm a destructive action.

    - --yes flag: auto-confirm.
    - interactive tty: prompt on stderr, read from stdin.
    - non-interactive without --yes: refuse (exit 2, JSON error on stderr).

    Returns True if confirmed; if user actively cancelled returns False.
    Never returns False from non-interactive mode — that path exits 2.
    """
    if getattr(args, "yes", False):
        return True
    if not sys.stdin.isatty():
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": (
                        f"refused to {name}: non-interactive session requires --yes"
                    ),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        sys.exit(2)
    print(f"\n⚠️  确认执行操作：{name}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    for k, v in details.items():
        print(f"  {k}: {v}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    sys.stderr.write("确认执行？(y/n): ")
    sys.stderr.flush()
    return input().strip().lower() in ("y", "yes", "是")


def _fetch_list(client_method: Callable, fallback=None):
    """Return (data, error). `data` is a list or None; `error` is set on failure.

    A failed primary call (success=False) is reported immediately rather than
    silently swallowed by the fallback, so API errors stay visible.
    """
    success, data = client_method()
    if not success:
        return None, data if isinstance(data, str) else "查询失败"
    if not isinstance(data, list):
        return None, "查询失败"
    if not data and fallback is not None:
        print("⚠️  主查询为空，尝试回退...", file=sys.stderr)
        fb = fallback()
        data = fb if isinstance(fb, list) else []
    return data, None


# ---------- command handlers ------------------------------------------------


def cmd_products(client, args):
    def rows():
        return (client.get_product_list_old() or {}).items()
    data, error = _fetch_list(
        client.get_products,
        fallback=lambda: [{"id": pid, "name": n} for n, pid in rows()],
    )
    if error is not None:
        _err_exit(error)
    _jdump(data)


def cmd_projects(client, args):
    data, error = _fetch_list(
        lambda: client.get_projects(args.status),
        fallback=lambda: [{"id": pid, "name": n}
                          for pid, n in (client.get_project_list_old() or {}).items()],
    )
    if error is not None:
        _err_exit(error)
    _jdump(data)


def cmd_executions(client, args):
    success, executions = client.get_executions(args.project_id)
    if not (success and isinstance(executions, list)):
        _err_exit(executions if not success else "查询失败")
    _jdump(executions)


def cmd_stories(client, args):
    success, stories = client.get_stories(args.project_id)
    if not (success and isinstance(stories, list)):
        _err_exit(stories if not success else "查询失败")
    if args.limit and len(stories) > args.limit:
        stories = stories[: args.limit]
    _jdump(stories)


def cmd_tasks(client, args):
    success, tasks = client.get_tasks(args.execution_id)
    if not (success and isinstance(tasks, list)):
        _err_exit(tasks if not success else "查询失败")
    if args.limit and len(tasks) > args.limit:
        tasks = tasks[: args.limit]
    _jdump(tasks)


def cmd_bugs(client, args):
    success, bugs = client.get_bugs(args.product_id)
    if not (success and isinstance(bugs, list)):
        print("⚠️  REST 失败，回退到老 API", file=sys.stderr)
        bugs = client.get_bug_list_old(args.product_id) or []
        if not bugs:
            _err_exit("查询失败")
    if args.limit and len(bugs) > args.limit:
        bugs = bugs[: args.limit]
    _jdump([b for b in bugs if isinstance(b, dict)])


def cmd_productplans(client, args):
    success, plans = client.get_productplans(args.product_id)
    if not (success and isinstance(plans, list)):
        _err_exit(plans if not success else "查询失败")
    _jdump(plans)


# ---------- module (tree) commands -----------------------------------------


def cmd_modules(client, args):
    success, sons = client.list_modules(args.product_id, args.type)
    if not success:
        _err_exit(sons)
    _jdump(sons)


def cmd_create_module(client, args):
    if not _confirm(args, "新建模块", {
        "产品 ID": args.product_id,
        "模块名称": args.name,
        "类型": args.type,
        "父级 ID": args.parent,
    }):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.create_module(
        args.product_id, args.name, view_type=args.type, parent=args.parent,
    )
    deny = _deny_to_error(result) if ok else None
    if deny:
        _err_exit(deny)
    _jdump({"status": "ok"} if ok else {"status": "error", "error": result})


def cmd_edit_module(client, args):
    if not _confirm(args, "编辑模块", {
        "模块 ID": args.module_id,
        "新名称": args.name,
        "类型": args.type,
    }):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.edit_module(args.module_id, args.name, view_type=args.type)
    deny = _deny_to_error(result) if ok else None
    if deny:
        _err_exit(deny)
    _jdump({"status": "ok"} if ok else {"status": "error", "error": result})


def cmd_delete_module(client, args):
    if not _confirm(args, "删除模块", {
        "模块 ID": args.module_id,
        "类型": args.type,
    }):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.delete_module(args.module_id, view_type=args.type)
    deny = _deny_to_error(result) if ok else None
    if deny:
        _err_exit(deny)
    _jdump({"status": "ok"} if ok else {"status": "error", "error": result})


def cmd_create_story(client, args):
    if not _confirm(args, "新建需求", {
        "产品 ID": args.product_id,
        "执行 ID": args.execution_id,
        "模块": args.module,
        "需求标题": args.title,
        "计划 ID": args.plan_id,
        "评审人": args.reviewer or "默认",
    }):
        _jdump({"status": "cancelled"})
        return
    success, result = client.create_story(
        product_id=args.product_id,
        title=args.title,
        module=args.module,
        execution_id=args.execution_id,
        plan=args.plan_id,
        reviewer=args.reviewer,
    )
    _jdump({"status": "ok", "id": result.get("id")} if success
          else {"status": "error", "error": result})


def cmd_create_bug(client, args):
    info = {
        "产品 ID": args.product_id,
        "模块": args.module,
        "Bug 标题": args.title,
        "严重程度": args.severity,
        "指派给": args.assigned_to or "默认",
    }
    if args.project_id:
        info["项目 ID"] = args.project_id
    if not _confirm(args, "新建 Bug", info):
        _jdump({"status": "cancelled"})
        return
    success, result = client.create_bug(
        product_id=args.product_id,
        title=args.title,
        module=args.module,
        severity=args.severity,
        pri=args.pri,
        project_id=args.project_id or None,
        assignedTo=args.assigned_to or None,
    )
    _jdump({"status": "ok", "id": result.get("id")} if success
          else {"status": "error", "error": result})


def cmd_create_task(client, args):
    info = {"执行 ID": args.execution_id, "需求 ID": args.story_id,
            "任务名称": args.name, "指派给": args.assign_to}
    if args.parent_id:
        info["父任务 ID"] = args.parent_id
    if not _confirm(args, "新建任务", info):
        _jdump({"status": "cancelled"})
        return
    success, result = client.create_task(
        project=args.execution_id,
        name=args.name,
        story=args.story_id,
        assignedTo=args.assign_to,
        module="0",
        parent=args.parent_id,
    )
    _jdump({"status": "ok", "id": result.get("id")} if success
          else {"status": "error", "error": result})


def cmd_batch_create_tasks(client, args):
    tasks = []
    for item in args.tasks.split(","):
        parts = item.strip().split(":")
        if not parts or not parts[0]:
            continue
        t = {"name": parts[0].strip()}
        if len(parts) >= 2:
            t["estimate"] = parts[1].strip()
        tasks.append(t)
    if not tasks:
        _err_exit("未提供有效的任务信息")
    if not _confirm(args, "批量创建子任务", {
        "执行 ID": args.execution_id, "父任务 ID": args.parent_id,
        "任务数量": len(tasks),
        "任务列表": ", ".join(f"{t['name']}({t.get('estimate', '?')}h)" for t in tasks),
    }):
        _jdump({"status": "cancelled"})
        return
    success, result = client.batch_create_tasks(
        args.execution_id, args.parent_id, tasks,
    )
    _jdump({"status": "ok", "message": result.get("message", "创建成功")} if success
          else {"status": "error", "error": result})


def cmd_create_productplan(client, args):
    if not _confirm(args, "新建发布计划", {
        "产品 ID": args.product_id, "计划名称": args.title,
    }):
        _jdump({"status": "cancelled"})
        return
    success, result = client.create_productplan(args.product_id, args.title)
    _jdump({"status": "ok", "id": result.get("id")} if success
          else {"status": "error", "error": result})


def cmd_review_story(client, args):
    if not _confirm(args, "评审需求", {"需求 ID": args.story_id, "结果": "通过"}):
        _jdump({"status": "cancelled"})
        return
    # ponytail: review_story needs result (pass/revert/clarify/reject).
    # CLI defaults to "pass"; add --result flag later if needed.
    success, result = client.review_story(args.story_id, "pass")
    _jdump({"status": "ok", "story_id": args.story_id} if success
          else {"status": "error", "error": result})


# ---------- task status transitions ------------------------------------------


def _cmd_task_status(client, args, action_zh, method_name, status_label):
    """Shared handler for the seven task-status CLI commands.

    Each is a thin shim: confirm, call ``client.<method_name>(task_id, ...)``,
    print a JSON result.
    """
    info = {"任务 ID": args.task_id}
    if getattr(args, "comment", ""):
        info["备注"] = args.comment
    if not _confirm(args, action_zh, info):
        _jdump({"status": "cancelled"})
        return
    method = getattr(client, method_name)
    ok, result = method(args.task_id, comment=args.comment or "")
    _jdump({"status": "ok", "task_id": args.task_id, "state": status_label} if ok
          else {"status": "error", "error": result})


def cmd_assign_task(client, args):
    """assign_task is the only task-status command with an extra required
    argument (the new assignee), so it doesn't share the helper above."""
    info = {"任务 ID": args.task_id, "指派给": args.assigned_to}
    if args.comment:
        info["备注"] = args.comment
    if not _confirm(args, "指派任务", info):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.assign_task(
        args.task_id, assigned_to=args.assigned_to, comment=args.comment or ""
    )
    _jdump({"status": "ok", "task_id": args.task_id, "assigned_to": args.assigned_to} if ok
          else {"status": "error", "error": result})


def cmd_start_task(client, args):
    _cmd_task_status(client, args, "开始任务", "start_task", "doing")


def cmd_pause_task(client, args):
    _cmd_task_status(client, args, "暂停任务", "pause_task", "pause")


def cmd_restart_task(client, args):
    _cmd_task_status(client, args, "继续任务", "restart_task", "doing")


def cmd_finish_task(client, args):
    _cmd_task_status(client, args, "完成任务", "finish_task", "done")


def cmd_close_task(client, args):
    _cmd_task_status(client, args, "关闭任务", "close_task", "closed")


def cmd_cancel_task(client, args):
    _cmd_task_status(client, args, "取消任务", "cancel_task", "cancel")


def cmd_activate_task(client, args):
    _cmd_task_status(client, args, "激活任务", "activate_task", "doing")


def cmd_assign_task(client, args):  # noqa: F811  (deliberate redefinition kept)
    """assign_task is the only task-status command with an extra required
    argument (the new assignee), so it doesn't share the helper above."""
    info = {"任务 ID": args.task_id, "指派给": args.assigned_to}
    if args.comment:
        info["备注"] = args.comment
    if not _confirm(args, "指派任务", info):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.assign_task(
        args.task_id, assigned_to=args.assigned_to, comment=args.comment or ""
    )
    _jdump({"status": "ok", "task_id": args.task_id, "assigned_to": args.assigned_to} if ok
          else {"status": "error", "error": result})


# ---------- bug status transitions -------------------------------------------


def cmd_assign_bug(client, args):
    if not _confirm(args, "指派 Bug", {"Bug ID": args.bug_id, "指派给": args.assigned_to}):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.assign_bug(
        args.bug_id, args.assigned_to, comment=args.comment or ""
    )
    _jdump({"status": "ok", "bug_id": args.bug_id, "assigned_to": args.assigned_to} if ok
          else {"status": "error", "error": result})


def cmd_confirm_bug(client, args):
    if not _confirm(args, "确认 Bug", {"Bug ID": args.bug_id}):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.confirm_bug(args.bug_id, comment=args.comment or "")
    _jdump({"status": "ok", "bug_id": args.bug_id} if ok
          else {"status": "error", "error": result})


def cmd_resolve_bug(client, args):
    if not _confirm(args, "解决 Bug", {
        "Bug ID": args.bug_id,
        "解决方案": args.resolution,
        "解决版本": args.build,
    }):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.resolve_bug(
        args.bug_id,
        resolution=args.resolution,
        resolved_build=args.build,
        comment=args.comment or "",
    )
    _jdump({"status": "ok", "bug_id": args.bug_id, "resolution": args.resolution} if ok
          else {"status": "error", "error": result})


def cmd_close_bug(client, args):
    if not _confirm(args, "关闭 Bug", {"Bug ID": args.bug_id}):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.close_bug(args.bug_id, comment=args.comment or "")
    _jdump({"status": "ok", "bug_id": args.bug_id} if ok
          else {"status": "error", "error": result})


def cmd_activate_bug(client, args):
    if not _confirm(args, "激活 Bug", {"Bug ID": args.bug_id}):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.activate_bug(args.bug_id, comment=args.comment or "")
    _jdump({"status": "ok", "bug_id": args.bug_id} if ok
          else {"status": "error", "error": result})


# ---------- story status transitions ---------------------------------------


def cmd_assign_story(client, args):
    """assign-story routes through change_story to set the assignedTo field."""
    if not _confirm(args, "指派需求", {"需求 ID": args.story_id, "指派给": args.assigned_to}):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.change_story(
        args.story_id, assignedTo=args.assigned_to
    )
    _jdump({"status": "ok", "story_id": args.story_id, "assigned_to": args.assigned_to} if ok
          else {"status": "error", "error": result})


def cmd_close_story(client, args):
    if not _confirm(args, "关闭需求", {"需求 ID": args.story_id}):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.close_story(args.story_id)
    _jdump({"status": "ok", "story_id": args.story_id} if ok
          else {"status": "error", "error": result})


def cmd_activate_story(client, args):
    if not _confirm(args, "激活需求", {"需求 ID": args.story_id}):
        _jdump({"status": "cancelled"})
        return
    ok, result = client.activate_story(args.story_id)
    _jdump({"status": "ok", "story_id": args.story_id} if ok
          else {"status": "error", "error": result})


# ---------- argparse + dispatch ---------------------------------------------


COMMANDS: Dict[str, Callable[[ZenTaoClient, argparse.Namespace], None]] = {
    "products": cmd_products,
    "projects": cmd_projects,
    "executions": cmd_executions,
    "stories": cmd_stories,
    "tasks": cmd_tasks,
    "bugs": cmd_bugs,
    "productplans": cmd_productplans,
    "modules": cmd_modules,
    "create-module": cmd_create_module,
    "edit-module": cmd_edit_module,
    "delete-module": cmd_delete_module,
    "create-story": cmd_create_story,
    "create-bug": cmd_create_bug,
    "create-task": cmd_create_task,
    "batch-create-tasks": cmd_batch_create_tasks,
    "create-productplan": cmd_create_productplan,
    "review-story": cmd_review_story,
    "start-task": cmd_start_task,
    "pause-task": cmd_pause_task,
    "restart-task": cmd_restart_task,
    "finish-task": cmd_finish_task,
    "close-task": cmd_close_task,
    "cancel-task": cmd_cancel_task,
    "activate-task": cmd_activate_task,
    "assign-task": cmd_assign_task,
    "assign-bug": cmd_assign_bug,
    "confirm-bug": cmd_confirm_bug,
    "resolve-bug": cmd_resolve_bug,
    "close-bug": cmd_close_bug,
    "activate-bug": cmd_activate_bug,
    "assign-story": cmd_assign_story,
    "close-story": cmd_close_story,
    "activate-story": cmd_activate_story,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zentao", description="禅道项目管理工具")
    p.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help=f".env 凭证文件路径，默认 {default_env_path()}",
    )
    p.add_argument(
        "-y", "--yes",
        action="store_true",
        help="对所有破坏性操作自动确认 (适合 CI/脚本)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("products", help="查询产品列表")

    sp = sub.add_parser("projects", help="查询项目列表")
    sp.add_argument("--status", default="doing", help="项目状态，默认 doing")

    sp = sub.add_parser("executions", help="查询执行列表")
    sp.add_argument("--project-id", required=True, help="项目 ID")

    sp = sub.add_parser("stories", help="查询需求列表")
    sp.add_argument("--project-id", required=True, help="项目 ID")
    sp.add_argument("--limit", type=int, default=50, help="最多显示条数")

    sp = sub.add_parser("tasks", help="查询任务列表")
    sp.add_argument("--execution-id", required=True, help="执行 ID")
    sp.add_argument("--limit", type=int, default=50, help="最多显示条数")

    sp = sub.add_parser("bugs", help="查询缺陷列表")
    sp.add_argument("--product-id", required=True, help="产品 ID")
    sp.add_argument("--limit", type=int, default=50, help="最多显示条数")

    sp = sub.add_parser("productplans", help="查询发布计划")
    sp.add_argument("--product-id", required=True, help="产品 ID")

    sp = sub.add_parser("modules", help="查询模块列表")
    sp.add_argument("--product-id", required=True, help="产品 ID")
    sp.add_argument("--type", default="story",
                    choices=["story", "bug", "task"],
                    help="模块视图类型，默认 story")

    sp = sub.add_parser("create-module", help="新建模块")
    sp.add_argument("--product-id", required=True, help="产品 ID")
    sp.add_argument("--name", required=True, help="模块名称")
    sp.add_argument("--type", default="story",
                    choices=["story", "bug", "task"],
                    help="模块类型，默认 story")
    sp.add_argument("--parent", default="0", help="父模块 ID，默认 0（根级）")

    sp = sub.add_parser("edit-module", help="编辑模块")
    sp.add_argument("--module-id", required=True, help="模块 ID")
    sp.add_argument("--name", required=True, help="新名称")
    sp.add_argument("--type", default="story",
                    choices=["story", "bug", "task"],
                    help="模块类型，默认 story")

    sp = sub.add_parser("delete-module", help="删除模块")
    sp.add_argument("--module-id", required=True, help="模块 ID")
    sp.add_argument("--type", default="story",
                    choices=["story", "bug", "task"],
                    help="模块类型，默认 story")

    sp = sub.add_parser("create-story", help="新建需求")
    sp.add_argument("--product-id", required=True)
    sp.add_argument("--execution-id", required=True)
    sp.add_argument("--title", required=True)
    sp.add_argument("--module", required=True, help="模块，如 [模块1] / [模块2]")
    sp.add_argument("--plan-id", default="0")
    sp.add_argument("--reviewer", default="")

    sp = sub.add_parser("create-bug", help="新建 Bug")
    sp.add_argument("--product-id", required=True)
    sp.add_argument("--title", required=True)
    sp.add_argument("--module", required=True, help="模块，如 [模块1] / [模块2]")
    sp.add_argument("--severity", default="3", help="严重程度 1-4")
    sp.add_argument("--pri", default="3", help="优先级 0-4")
    sp.add_argument("--project-id", default=None)
    sp.add_argument("--assigned-to", default=None)

    sp = sub.add_parser("create-task", help="新建任务")
    sp.add_argument("--execution-id", required=True)
    sp.add_argument("--story-id", required=True)
    sp.add_argument("--name", required=True)
    sp.add_argument("--assign-to", required=True)
    sp.add_argument("--parent-id", default=None)

    sp = sub.add_parser("batch-create-tasks", help="批量创建子任务")
    sp.add_argument("--execution-id", required=True)
    sp.add_argument("--parent-id", required=True)
    sp.add_argument("--tasks", required=True,
                    help="任务列表，格式: 名称:工时,名称:工时")

    sp = sub.add_parser("create-productplan", help="新建发布计划")
    sp.add_argument("--product-id", required=True)
    sp.add_argument("--title", required=True)

    sp = sub.add_parser("review-story", help="评审需求")
    sp.add_argument("--story-id", required=True)

    # ----- task status transitions (7 subcommands) -----

    for cmd_name, help_zh in [
        ("start-task", "开始任务 (wait→doing)"),
        ("pause-task", "暂停任务 (doing→pause)"),
        ("restart-task", "继续任务 (pause→doing)"),
        ("finish-task", "完成任务 (doing→done)"),
        ("close-task", "关闭任务 (done→closed)"),
        ("cancel-task", "取消任务 (任意状态→cancel)"),
        ("activate-task", "激活任务 (done/closed→doing)"),
    ]:
        sp = sub.add_parser(cmd_name, help=help_zh)
        sp.add_argument("--task-id", required=True, help="任务 ID")
        sp.add_argument("--comment", default="", help="状态变更备注（可选）")

    sp = sub.add_parser("assign-task", help="指派任务")
    sp.add_argument("--task-id", required=True, help="任务 ID")
    sp.add_argument("--assigned-to", required=True, help="指派给的用户名")
    sp.add_argument("--comment", default="", help="备注（可选）")

    # ----- bug status transitions (5 subcommands) -----

    sp = sub.add_parser("assign-bug", help="指派 Bug")
    sp.add_argument("--bug-id", required=True, help="Bug ID")
    sp.add_argument("--assigned-to", required=True, help="指派给的用户名")
    sp.add_argument("--comment", default="", help="备注（可选）")

    sp = sub.add_parser("confirm-bug", help="确认 Bug")
    sp.add_argument("--bug-id", required=True)
    sp.add_argument("--comment", default="")

    sp = sub.add_parser("resolve-bug", help="解决 Bug")
    sp.add_argument("--bug-id", required=True)
    sp.add_argument("--resolution", default="fixed",
                    choices=["fixed", "postponed", "willnotfix", "duplicate", "tostory"],
                    help="解决方案类型")
    sp.add_argument("--build", default="trunk", help="解决版本 (默认 trunk)")
    sp.add_argument("--comment", default="")

    sp = sub.add_parser("close-bug", help="关闭 Bug")
    sp.add_argument("--bug-id", required=True)
    sp.add_argument("--comment", default="")

    sp = sub.add_parser("activate-bug", help="激活 Bug")
    sp.add_argument("--bug-id", required=True)
    sp.add_argument("--comment", default="")

    # ----- story status transitions (3 subcommands) -----

    sp = sub.add_parser("assign-story", help="指派需求给某人")
    sp.add_argument("--story-id", required=True, help="需求 ID")
    sp.add_argument("--assigned-to", required=True, help="指派给的用户名")

    sp = sub.add_parser("close-story", help="关闭需求")
    sp.add_argument("--story-id", required=True)

    sp = sub.add_parser("activate-story", help="激活需求")
    sp.add_argument("--story-id", required=True)

    return p


def main(argv=None) -> int:
    # Parse first so --help never reaches the credential check.
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    env_path = args.env_file if args.env_file is not None else default_env_path()
    credentials = read_credentials(env_path)
    if not credentials:
        _err_exit(
            {
                "missing": ["endpoint", "username", "password"],
                "config_path": str(env_path),
                "hint": "创建该文件, 格式: endpoint=... / username=... / password=...",
            },
            code=1,
        )

    client = ZenTaoClient(
        credentials["endpoint"],
        credentials["username"],
        credentials["password"],
    )

    handler = COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    handler(client, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
