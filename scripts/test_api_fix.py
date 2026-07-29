#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证接口参数修复
"""

import sys
from pathlib import Path

script_dir = Path(__file__).parent.absolute()
lib_path = script_dir.parent / "lib"
sys.path.insert(0, str(lib_path))

import importlib.util

client_path = lib_path / "zentao_client.py"
spec = importlib.util.spec_from_file_location("zentao_client", client_path)
zentao_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zentao_client)
ZenTaoClient = zentao_client.ZenTaoClient
read_credentials = zentao_client.read_credentials


def main():
    print("=" * 80)
    print("验证接口参数修复")
    print("=" * 80)

    credentials = read_credentials()
    if not credentials:
        print("❌ 未找到禅道凭证")
        return 1

    client = ZenTaoClient(
        credentials["endpoint"], credentials["username"], credentials["password"]
    )

    print("\n正在获取 Session...")
    sid = client.get_session()
    if not sid:
        print("❌ 认证失败")
        return 1
    print(f"✅ 认证成功")

    # 获取产品ID
    success, products = client.get_products()
    product_id = list(products.keys())[0] if success else "4"
    print(f"使用产品ID: {product_id}")

    # 测试1: get_bug_list_old
    print("\n" + "-" * 80)
    print("测试1: get_bug_list_old(branch='0')")
    print("-" * 80)
    try:
        bugs = client.get_bug_list_old(product_id, branch="0")
        print(
            f"✅ 获取Bug列表成功，共 {len(bugs) if isinstance(bugs, list) else 'N/A'} 条"
        )
    except Exception as e:
        print(f"❌ 失败: {e}")

    # 测试2: get_productplan_list_old
    print("\n" + "-" * 80)
    print("测试2: get_productplan_list_old(branch='0')")
    print("-" * 80)
    try:
        plans = client.get_productplan_list_old(product_id, branch="0")
        print(f"✅ 获取计划列表成功，共 {len(plans)} 个计划")
    except Exception as e:
        print(f"❌ 失败: {e}")

    # 测试3: get_project_tasks_old
    print("\n" + "-" * 80)
    print("测试3: get_project_tasks_old(module_id='0', limit=100, page=1)")
    print("-" * 80)
    try:
        projects = client.get_project_list_old("all")
        if projects:
            project_id = list(projects.keys())[0]
            tasks = client.get_project_tasks_old(
                project_id, status="all", module_id="0", limit=100, page=1
            )
            print(f"✅ 获取项目任务成功，项目 {project_id}，共 {len(tasks)} 个任务")
        else:
            print("⚠️  没有项目可测试")
    except Exception as e:
        print(f"❌ 失败: {e}")

    # 测试4: create_testcase
    print("\n" + "-" * 80)
    print("测试4: create_testcase(module='0', story='0', branch='0')")
    print("-" * 80)
    try:
        from datetime import datetime

        success, result = client.create_testcase(
            product_id=product_id,
            title=f"参数测试_{datetime.now().strftime('%H%M%S')}",
            case_type="feature",
            module="0",
            story="0",
            branch="0",
            pri="3",
            steps_list=["步骤1", "步骤2"],
            expects_list=["预期1", "预期2"],
        )
        if success:
            print(f"✅ 创建测试用例成功: {result}")
        else:
            print(f"⚠️  创建测试用例返回: {result}")
    except Exception as e:
        print(f"❌ 失败: {e}")

    # 测试5: create_story
    print("\n" + "-" * 80)
    print("测试5: create_story(module='0', plan='0', execution_id='0', branch='0')")
    print("-" * 80)
    try:
        from datetime import datetime

        success, result = client.create_story(
            product_id=product_id,
            title=f"需求测试_{datetime.now().strftime('%H%M%S')}",
            module="0",
            plan="0",
            execution_id="0",
            branch="0",
            pri="3",
        )
        if success:
            print(f"✅ 创建需求成功: {result}")
        else:
            print(f"⚠️  创建需求返回: {result}")
    except Exception as e:
        print(f"❌ 失败: {e}")

    # 测试6: get_testreports
    print("\n" + "-" * 80)
    print("测试6: get_testreports(project_id='0')")
    print("-" * 80)
    try:
        success, reports = client.get_testreports(product_id, project_id="0")
        if success:
            print(f"✅ 获取测试报告成功，共 {len(reports)} 个报告")
        else:
            print(f"⚠️  获取测试报告返回: {reports}")
    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n" + "=" * 80)
    print("验证完成")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
