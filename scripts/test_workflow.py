#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工单客服系统 - 完整项目流程测试
演示从产品创建到测试完成的完整生命周期
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加 lib 目录到 Python 路径
script_dir = Path(__file__).parent.absolute()
lib_path = script_dir.parent / "lib"
sys.path.insert(0, str(lib_path))

# 导入 ZenTaoClient
import importlib.util

client_path = lib_path / "zentao_client.py"
spec = importlib.util.spec_from_file_location("zentao_client", client_path)
zentao_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zentao_client)
ZenTaoClient = zentao_client.ZenTaoClient
read_credentials = zentao_client.read_credentials


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(success: bool, message: str, data: dict = None):
    """打印结果"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    if data:
        print(f"   数据: {json.dumps(data, ensure_ascii=False, indent=2)}")


def main():
    """主函数 - 完整流程测试"""

    print_section("🚀 工单客服系统 - 禅道完整流程测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ==================== 初始化 ====================
    print_section("📡 连接禅道")

    credentials = read_credentials()
    if not credentials:
        print("❌ 未找到禅道凭证，请检查 TOOLS.md")
        return 1

    print(f"API地址: {credentials['endpoint']}")
    print(f"用户名: {credentials['username']}")

    client = ZenTaoClient(
        credentials["endpoint"], credentials["username"], credentials["password"]
    )

    # 获取 Session
    print("\n正在获取 Session...")
    sid = client.get_session()
    if not sid:
        print("❌ 认证失败")
        return 1
    print(f"✅ 认证成功，Session ID: {sid[:20]}...")

    # 存储创建的资源ID，用于后续流程
    resources = {
        "product_id": None,
        "story_ids": [],
        "plan_id": None,
        "project_id": None,
        "task_ids": [],
        "bug_ids": [],
        "testcase_ids": [],
    }

    try:
        # ==================== 产品阶段 ====================
        print_section("📦 第一阶段：产品管理")

        # 1. 创建产品
        print("\n1️⃣  创建产品...")
        success, result = client.create_product(
            name="工单客服系统",
            code="TICKETCS",
            type="normal",
            po="admin",  # 产品负责人
            status="normal",
            desc="智能工单客服系统，支持多渠道接入、智能分配、知识库、数据分析等功能",
        )
        if success:
            print_result(
                True, "创建产品成功", {"产品名称": "工单客服系统", "代码": "TICKETCS"}
            )
        else:
            print_result(False, f"创建产品失败: {result}")

        # 2. 查看产品列表，获取产品ID
        print("\n2️⃣  查询产品列表...")
        success, products = client.get_products()
        if success:
            print(f"✅ 查询到 {len(products)} 个产品")
            for pid, name in products.items():
                print(f"   [{pid}] {name}")
                if "工单客服系统" in str(name):
                    resources["product_id"] = pid
        else:
            # 降级到老API
            products_old = client.get_product_list_old()
            print(f"✅ 查询到 {len(products_old)} 个产品 (老API)")
            for name, pid in products_old.items():
                print(f"   [{pid}] {name}")
                if "工单客服系统" in str(name):
                    resources["product_id"] = pid

        if not resources["product_id"]:
            print("⚠️  未找到产品ID，使用第一个产品")
            resources["product_id"] = list(products.values())[0] if products else "1"

        print(f"\n📍 使用产品ID: {resources['product_id']}")

        # 3. 创建需求
        print("\n3️⃣  创建需求...")
        requirements = [
            {"title": "用户登录功能", "pri": "3", "estimate": "4"},
            {"title": "工单创建功能", "pri": "3", "estimate": "8"},
            {"title": "工单分配功能", "pri": "3", "estimate": "6"},
            {"title": "工单处理功能", "pri": "3", "estimate": "8"},
            {"title": "知识库管理", "pri": "2", "estimate": "12"},
            {"title": "数据统计报表", "pri": "2", "estimate": "10"},
        ]

        for req in requirements:
            print(f"\n   创建需求: {req['title']}")
            success, result = client.create_story(
                product_id=resources["product_id"],
                title=req["title"],
                pri=req["pri"],
                estimate=req["estimate"],
                spec=f"实现{req['title']}，预计工时{req['estimate']}小时",
            )
            if success:
                print(f"   ✅ 需求创建成功: {req['title']}")
            else:
                print(f"   ⚠️  需求创建失败或已存在: {result}")

        # 4. 创建发布计划
        print("\n4️⃣  创建发布计划...")
        today = datetime.now()
        success, result = client.create_plan(
            product_id=resources["product_id"],
            title="V1.0版本",
            begin=today.strftime("%Y-%m-01"),
            end=today.strftime("%Y-%m-%d"),
            desc="工单客服系统首个版本发布计划",
        )
        print_result(success, "创建发布计划", {"计划名称": "V1.0版本"})

        # 5. 查看计划列表
        print("\n5️⃣  查询发布计划...")
        success, plans = client.get_plans(resources["product_id"])
        if success and plans:
            print(f"✅ 查询到 {len(plans)} 个发布计划")
            # 兼容不同返回格式
            if isinstance(plans, dict):
                for plan_id, plan_data in plans.items():
                    if isinstance(plan_data, dict):
                        print(f"   [{plan_id}] {plan_data.get('title', plan_data)}")
                        if "V1.0" in str(plan_data.get("title", "")):
                            resources["plan_id"] = plan_id
                    else:
                        print(f"   [{plan_id}] {plan_data}")
            elif isinstance(plans, list):
                for plan in plans:
                    if isinstance(plan, dict):
                        print(f"   [{plan.get('id')}] {plan.get('title')}")
                        if "V1.0" in str(plan.get("title", "")):
                            resources["plan_id"] = plan.get("id")

        # ==================== 立项阶段 ====================
        print_section("🎯 第二阶段：项目立项")

        # 6. 查看项目列表
        print("\n6️⃣  查询项目列表...")
        projects = client.get_project_list_old("all")
        if projects:
            print(f"✅ 查询到 {len(projects)} 个项目")
            for pid, name in list(projects.items())[:5]:
                print(f"   [{pid}] {name}")
            # 使用第一个项目作为测试项目
            resources["project_id"] = list(projects.keys())[0] if projects else None
            print(f"\n📍 使用项目ID: {resources['project_id']}")
        else:
            print("⚠️  未查询到项目，跳过立项阶段")

        # 7. 查看项目任务
        if resources["project_id"]:
            print(f"\n7️⃣  查询项目 {resources['project_id']} 的任务列表...")
            tasks = client.get_project_tasks_old(resources["project_id"], "all")
            if tasks:
                print(f"✅ 查询到 {len(tasks)} 个任务")
                for tid, task in list(tasks.items())[:5]:
                    print(f"   [{tid}] {task.get('name')} ({task.get('status')})")

        # 8. 创建子任务（如果有父任务）
        if resources["project_id"] and tasks:
            parent_task_id = list(tasks.keys())[0]
            print(f"\n8️⃣  为任务 {parent_task_id} 创建子任务...")

            subtasks = [
                {
                    "name": "前端开发",
                    "estimate": "8",
                    "assignedTo": "admin",
                    "type": "devel",
                    "pri": "3",
                },
                {
                    "name": "后端开发",
                    "estimate": "12",
                    "assignedTo": "admin",
                    "type": "devel",
                    "pri": "3",
                },
                {
                    "name": "接口联调",
                    "estimate": "4",
                    "assignedTo": "admin",
                    "type": "devel",
                    "pri": "3",
                },
            ]

            success, result = client.create_subtasks(
                execution_id=resources["project_id"],
                parent_id=parent_task_id,
                tasks=subtasks,
            )
            print_result(
                success,
                "创建子任务",
                {"父任务ID": parent_task_id, "子任务数": len(subtasks)},
            )

        # ==================== 开发阶段 ====================
        print_section("💻 第三阶段：开发执行")

        # 9. 查看我的任务
        print("\n9️⃣  查看我的任务...")
        success, my_tasks = client.get_my_tasks("assignedTo")
        if success:
            print(f"✅ 指派给我的任务: {len(my_tasks)} 个")
            for task in my_tasks[:5]:
                print(
                    f"   [{task.get('id')}] {task.get('name')} ({task.get('status')})"
                )
                if resources["project_id"] and len(resources["task_ids"]) < 3:
                    resources["task_ids"].append(task.get("id"))

        # 10. 演示任务流转
        if resources["task_ids"]:
            task_id = resources["task_ids"][0]

            # 获取任务详情
            print(f"\n🔟 查看任务 {task_id} 详情...")
            success, task = client.get_task_detail(task_id)
            if success:
                print(f"   任务名称: {task.get('name')}")
                print(f"   当前状态: {task.get('status')}")
                print(f"   预计工时: {task.get('estimate')}")
                print(f"   已消耗: {task.get('consumed')}")
                print(f"   剩余: {task.get('left')}")
                print(f"   指派给: {task.get('assignedTo')}")

            # 根据状态执行操作
            current_status = task.get("status", "wait")

            if current_status == "wait":
                print(f"\n1️⃣1️⃣ 开始任务 {task_id}...")
                success, result = client.start_task(task_id, "开始开发")
                print_result(success, "开始任务", {"任务ID": task_id})

            elif current_status == "doing":
                print(f"\n1️⃣1️⃣ 记录工时...")
                today_str = datetime.now().strftime("%Y-%m-%d")
                success, result = client.record_estimate(
                    task_id,
                    [
                        {
                            "date": today_str,
                            "consumed": "2",
                            "left": "6",
                            "work": "完成了基础功能开发",
                        }
                    ],
                )
                print_result(
                    success, "记录工时", {"任务ID": task_id, "消耗": "2h", "剩余": "6h"}
                )

            elif current_status == "pause":
                print(f"\n1️⃣1️⃣ 继续任务 {task_id}...")
                success, result = client.restart_task(task_id, "继续开发")
                print_result(success, "继续任务", {"任务ID": task_id})

            # 查看任务列表
            print(f"\n1️⃣2️⃣ 查看我创建的任务...")
            success, opened_tasks = client.get_my_tasks("openedBy")
            if success:
                print(f"✅ 我创建的任务: {len(opened_tasks)} 个")
                for task in opened_tasks[:5]:
                    print(
                        f"   [{task.get('id')}] {task.get('name')} ({task.get('status')})"
                    )

        # ==================== 测试阶段 ====================
        print_section("🧪 第四阶段：测试管理")

        # 13. 创建测试用例
        print("\n1️⃣3️⃣ 创建测试用例...")
        testcases = [
            {
                "title": "登录功能测试",
                "type": "feature",
                "steps": "1.打开登录页\n2.输入正确账号密码\n3.点击登录",
                "expect": "登录成功",
            },
            {
                "title": "工单创建测试",
                "type": "feature",
                "steps": "1.进入工单页面\n2.填写工单信息\n3.提交工单",
                "expect": "工单创建成功",
            },
            {
                "title": "工单分配测试",
                "type": "feature",
                "steps": "1.选择待分配工单\n2.选择处理人\n3.确认分配",
                "expect": "分配成功",
            },
        ]

        for tc in testcases:
            print(f"\n   创建用例: {tc['title']}")
            success, result = client.create_testcase(
                product_id=resources["product_id"],
                title=tc["title"],
                case_type=tc["type"],
                steps=tc["steps"],
                expect=tc["expect"],
            )
            print_result(success, f"创建测试用例: {tc['title']}")

        # 14. 查看测试用例列表
        print(f"\n1️⃣4️⃣ 查询测试用例...")
        success, cases = client.get_testcases(resources["product_id"])
        if success:
            print(f"✅ 查询到 {len(cases)} 个测试用例")
            for case in cases[:5]:
                print(f"   [{case.get('id')}] {case.get('title')}")

        # 15. 创建Bug
        print(f"\n1️⃣5️⃣ 创建Bug...")
        success, result = client.create_bug(
            product_id=resources["product_id"],
            title="登录页面报错：500错误",
            severity="3",
            pri="3",
            type="codeerror",
            steps="1.打开登录页面\n2.输入用户名密码\n3.点击登录\n4.出现500错误",
            assignedTo="admin",
            project_id=resources["project_id"],
        )
        print_result(success, "创建Bug", {"标题": "登录页面报错：500错误"})

        # 16. 查看我的Bug
        print(f"\n1️⃣6️⃣ 查看我的Bug...")
        success, my_bugs = client.get_my_bugs("assignedTo")
        if success:
            print(f"✅ 指派给我的Bug: {len(my_bugs)} 个")
            for bug in my_bugs[:5]:
                print(f"   [{bug.get('id')}] {bug.get('title')} ({bug.get('status')})")
                if len(resources["bug_ids"]) < 3:
                    resources["bug_ids"].append(bug.get("id"))

        # 17. Bug流转演示
        if resources["bug_ids"]:
            bug_id = resources["bug_ids"][0]

            print(f"\n1️⃣7️⃣ 查看Bug {bug_id} 详情...")
            success, bug = client.get_bug(bug_id)
            if success:
                print(f"   标题: {bug.get('title')}")
                print(f"   状态: {bug.get('status')}")
                print(f"   严重程度: {bug.get('severity')}")
                print(f"   指派给: {bug.get('assignedTo')}")

            # 如果Bug是active状态，演示解决
            if bug.get("status") == "active":
                print(f"\n1️⃣8️⃣ 确认Bug {bug_id}...")
                success, result = client.confirm_bug(bug_id, "确认是有效Bug")
                print_result(success, "确认Bug", {"BugID": bug_id})

                print(f"\n1️⃣9️⃣ 解决Bug {bug_id}...")
                success, result = client.resolve_bug(
                    bug_id=bug_id,
                    resolution="fixed",
                    resolved_build="trunk",
                    comment="已修复登录校验问题",
                )
                print_result(success, "解决Bug", {"BugID": bug_id, "解决方案": "fixed"})

        # ==================== 统计信息 ====================
        print_section("📊 流程总结")

        print(f"\n产品ID: {resources['product_id']}")
        print(f"项目ID: {resources['project_id']}")
        print(f"计划ID: {resources['plan_id']}")
        print(f"任务ID: {resources['task_ids']}")
        print(f"Bug ID: {resources['bug_ids']}")

        print("\n✅ 流程测试完成！")
        print("\n📋 后续操作建议:")
        print("   1. 在禅道Web界面查看创建的产品、需求、任务、Bug")
        print("   2. 测试任务的其他状态流转（暂停、继续、完成、关闭）")
        print("   3. 测试Bug的完整生命周期（激活、关闭）")
        print("   4. 测试测试任务和测试报告功能")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
