#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""禅道项目管理命令行工具。"""

import argparse
import sys
from pathlib import Path
from typing import Callable, Dict, Tuple

from zentao_api.client import ZenTaoClient, read_credentials
from zentao_api.client._credentials import default_env_path


# ---------- display helpers --------------------------------------------------


def _print_table(headers, rows):
    """Render a simple aligned table. Columns sized to header + widest cell."""
    if not rows:
        print("无数据")
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    sep = "-+-".join("-" * w for w in widths)
    print(" | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print(sep)
    for row in rows:
        print(" | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))


def _confirm(name, details) -> bool:
    print(f"\n⚠️  确认执行操作：{name}")
    print("-" * 50)
    for k, v in details.items():
        print(f"  {k}: {v}")
    print("-" * 50)
    return input("确认执行？(y/n): ").strip().lower() in ("y", "yes", "是")


def _show_list(client_method: Callable, headers, row_fn, limit=None,
               title=None, fallback=None) -> None:
    """Print a list fetched via ``client_method``. Optionally falls back to
    ``fallback`` when the primary call returns falsy."""
    if title:
        print(f"📋 {title}\n")
    success, data = client_method()
    if not (success and isinstance(data, list) and data):
        if fallback is not None:
            print("⚠️  主查询失败，尝试回退...\n")
            success, data = True, fallback() or (False, [])
            data = data if isinstance(data, list) else []
        if not data:
            print("❌ 查询失败")
            return
    print(f"✅ 共 {len(data)} 条")
    if limit and len(data) > limit:
        print(f"（显示前 {limit} 条）")
        data = data[:limit]
    print()
    _print_table(headers, [row_fn(item) for item in data])


# ---------- command handlers ------------------------------------------------


def cmd_products(client, args):
    def rows():
        return (client.get_product_list_old() or {}).items()
    _show_list(
        client.get_products,
        ["ID", "产品名称", "状态", "负责人"],
        lambda p: [p.get("id", ""), p.get("name", ""),
                   p.get("status", ""), p.get("owner", "")],
        title="查询禅道产品列表",
        fallback=lambda: [{"id": pid, "name": n} for n, pid in rows()],
    )


def cmd_projects(client, args):
    _show_list(
        lambda: client.get_projects(args.status),
        ["ID", "项目名称", "状态", "开始", "结束"],
        lambda p: [p.get("id", ""), p.get("name", ""),
                   p.get("status", ""), p.get("begin", ""), p.get("end", "")],
        title=f"查询项目列表（status={args.status}）",
        fallback=lambda: [{"id": pid, "name": n}
                          for pid, n in (client.get_project_list_old() or {}).items()],
    )

def cmd_executions(client, args):
    success, executions = client.get_executions(args.project_id)
    if not (success and isinstance(executions, list)):
        print(f"❌ 查询失败：{executions}")
        return
    print(f"✅ 共 {len(executions)} 个执行\n")
    _print_table(
        ["ID", "执行名称", "状态", "开始", "结束"],
        [[e.get("id", ""), e.get("name", ""), e.get("status", ""),
          e.get("begin", ""), e.get("end", "")] for e in executions],
    )


def cmd_stories(client, args):
    success, stories = client.get_stories(args.project_id)
    if not (success and isinstance(stories, list)):
        print(f"❌ 查询失败：{stories}")
        return
    limit = args.limit
    print(f"✅ 共 {len(stories)} 个需求" + (f"（前 {limit}）" if len(stories) > limit else ""))
    if limit and len(stories) > limit:
        stories = stories[:limit]
    print()
    _print_table(
        ["ID", "需求标题", "状态", "优先级", "指派给"],
        [[s.get("id", ""), str(s.get("title", ""))[:40], s.get("status", ""),
          s.get("priority", ""), s.get("assignedTo", "")] for s in stories],
    )


def cmd_tasks(client, args):
    success, tasks = client.get_tasks(args.execution_id)
    if not (success and isinstance(tasks, list)):
        print(f"❌ 查询失败：{tasks}")
        return
    limit = args.limit
    print(f"✅ 共 {len(tasks)} 个任务" + (f"（前 {limit}）" if len(tasks) > limit else ""))
    if limit and len(tasks) > limit:
        tasks = tasks[:limit]
    print()
    _print_table(
        ["ID", "任务名称", "状态", "优先级", "指派给"],
        [[t.get("id", ""), str(t.get("name", ""))[:40], t.get("status", ""),
          t.get("priority", ""), t.get("assignedTo", "")] for t in tasks],
    )


def cmd_bugs(client, args):
    success, bugs = client.get_bugs(args.product_id)
    if not (success and isinstance(bugs, list)):
        print("⚠️  REST 失败，回退到老 API\n")
        bugs = client.get_bug_list_old(args.product_id) or []
        if not bugs:
            print("❌ 查询失败")
            return
    limit = args.limit
    print(f"✅ 共 {len(bugs)} 个缺陷" + (f"（前 {limit}）" if len(bugs) > limit else ""))
    if limit and len(bugs) > limit:
        bugs = bugs[:limit]
    print()
    _print_table(
        ["ID", "缺陷标题", "严重程度", "状态", "指派给"],
        [[b.get("id", ""), str(b.get("title", ""))[:40],
          b.get("severity", ""), b.get("status", ""), b.get("assignedTo", "")]
         for b in bugs if isinstance(b, dict)],
    )


def cmd_productplans(client, args):
    success, plans = client.get_productplans(args.product_id)
    if not (success and isinstance(plans, list)):
        print(f"❌ 查询失败：{plans}")
        return
    print(f"✅ 共 {len(plans)} 个发布计划\n")
    if not plans:
        print("无数据")
        return
    _print_table(
        ["ID", "计划名称"],
        [[p.get("id", ""), p.get("name", "")] for p in plans],
    )


def cmd_create_story(client, args):
    if not _confirm("新建需求", {
        "产品 ID": args.product_id,
        "执行 ID": args.execution_id,
        "需求标题": args.title,
        "计划 ID": args.plan_id,
        "评审人": args.reviewer or "默认",
    }):
        print("❌ 操作已取消")
        return
    success, result = client.create_story(
        product_id=args.product_id,
        title=args.title,
        execution_id=args.execution_id,
        plan=args.plan_id,
        reviewer=args.reviewer,
    )
    print(f"✅ 新建成功，需求 ID: {result.get('id', '未知')}" if success
          else f"❌ 新建失败：{result}")


def cmd_create_task(client, args):
    info = {"执行 ID": args.execution_id, "需求 ID": args.story_id,
            "任务名称": args.name, "指派给": args.assign_to}
    if args.parent_id:
        info["父任务 ID"] = args.parent_id
    if not _confirm("新建任务", info):
        print("❌ 操作已取消")
        return
    success, result = client.create_task(
        project=args.execution_id,
        name=args.name,
        story=args.story_id,
        assignedTo=args.assign_to,
        module="0",
        parent=args.parent_id,
    )
    print(f"✅ 新建成功，任务 ID: {result.get('id', '未知')}" if success
          else f"❌ 新建失败：{result}")


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
        print("❌ 未提供有效的任务信息")
        return
    if not _confirm("批量创建子任务", {
        "执行 ID": args.execution_id, "父任务 ID": args.parent_id,
        "任务数量": len(tasks),
        "任务列表": ", ".join(f"{t['name']}({t.get('estimate', '?')}h)" for t in tasks),
    }):
        print("❌ 操作已取消")
        return
    success, result = client.batch_create_tasks(
        args.execution_id, args.parent_id, tasks,
    )
    print(f"✅ {result.get('message', '创建成功')}" if success
          else f"❌ 创建失败：{result}")


def cmd_create_productplan(client, args):
    if not _confirm("新建发布计划", {
        "产品 ID": args.product_id, "计划名称": args.title,
    }):
        print("❌ 操作已取消")
        return
    success, result = client.create_productplan(args.product_id, args.title)
    print(f"✅ 新建成功，计划 ID: {result.get('id', '未知')}" if success
          else f"❌ 新建失败：{result}")


def cmd_review_story(client, args):
    if not _confirm("评审需求", {"需求 ID": args.story_id, "结果": "通过"}):
        print("❌ 操作已取消")
        return
    # ponytail: review_story needs result (pass/revert/clarify/reject).
    # CLI defaults to "pass"; add --result flag later if needed.
    success, result = client.review_story(args.story_id, "pass")
    print(f"✅ 需求 {args.story_id} 评审通过" if success
          else f"❌ 评审失败：{result}")


# ---------- task status transitions ------------------------------------------


def _cmd_task_status(client, args, action_zh, method_name, status_label):
    """Shared handler for the seven task-status CLI commands.

    Each is a thin shim: confirm, call ``client.<method_name>(task_id, ...)``,
    print the boolean result. The seven callers differ only in which client
    method they hit and what UI label they display. ``assign_task`` is the
    only caller that also accepts an ``assigned_to`` argument; it has its
    own handler (``cmd_assign_task``) below to keep the dispatch explicit
    rather than guessing from attribute presence.
    """
    info = {"任务 ID": args.task_id}
    if getattr(args, "comment", ""):
        info["备注"] = args.comment
    if not _confirm(action_zh, info):
        print("❌ 操作已取消")
        return
    method = getattr(client, method_name)
    ok, result = method(args.task_id, comment=args.comment or "")
    label = f"✅ 任务 {args.task_id} {status_label}" if ok else f"❌ {status_label}失败：{result}"
    print(label)


def cmd_assign_task(client, args):
    """assign_task is the only task-status command with an extra required
    argument (the new assignee), so it doesn't share the helper above."""
    info = {"任务 ID": args.task_id, "指派给": args.assigned_to}
    if args.comment:
        info["备注"] = args.comment
    if not _confirm("指派任务", info):
        print("❌ 操作已取消")
        return
    ok, result = client.assign_task(
        args.task_id, assigned_to=args.assigned_to, comment=args.comment or ""
    )
    label = f"✅ 任务 {args.task_id} 已指派给 {args.assigned_to}" if ok else f"❌ 指派失败：{result}"
    print(label)


def cmd_start_task(client, args):
    _cmd_task_status(client, args, "开始任务", "start_task", "已转为 doing")


def cmd_pause_task(client, args):
    _cmd_task_status(client, args, "暂停任务", "pause_task", "已暂停")


def cmd_restart_task(client, args):
    _cmd_task_status(client, args, "继续任务", "restart_task", "已恢复 doing")


def cmd_finish_task(client, args):
    _cmd_task_status(client, args, "完成任务", "finish_task", "已完成")


def cmd_close_task(client, args):
    _cmd_task_status(client, args, "关闭任务", "close_task", "已关闭")


def cmd_cancel_task(client, args):
    _cmd_task_status(client, args, "取消任务", "cancel_task", "已取消")


def cmd_activate_task(client, args):
    _cmd_task_status(client, args, "激活任务", "activate_task", "已激活")


# ---------- argparse + dispatch ---------------------------------------------


COMMANDS: Dict[str, Callable[[ZenTaoClient, argparse.Namespace], None]] = {
    "products": cmd_products,
    "projects": cmd_projects,
    "executions": cmd_executions,
    "stories": cmd_stories,
    "tasks": cmd_tasks,
    "bugs": cmd_bugs,
    "productplans": cmd_productplans,
    "create-story": cmd_create_story,
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
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zentao", description="禅道项目管理工具")
    p.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help=f".env 凭证文件路径，默认 {default_env_path()}",
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

    sp = sub.add_parser("create-story", help="新建需求")
    sp.add_argument("--product-id", required=True)
    sp.add_argument("--execution-id", required=True)
    sp.add_argument("--title", required=True)
    sp.add_argument("--plan-id", default="0")
    sp.add_argument("--reviewer", default="")

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

    return p


def main(argv=None) -> int:
    # Parse first so --help never reaches the credential check.
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    env_path = args.env_file if args.env_file is not None else default_env_path()
    credentials = read_credentials(env_path)
    if not credentials:
        print(f"❌ 未找到凭证文件：{env_path}", file=sys.stderr)
        print()
        print("请创建该文件，格式：", file=sys.stderr)
        print("  endpoint=http://your-zentao-host", file=sys.stderr)
        print("  username=your-username", file=sys.stderr)
        print("  password=your-password", file=sys.stderr)
        return 1

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
