#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试从测试用例创建Bug
"""

import sys
from pathlib import Path
from datetime import datetime

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
    print("测试从测试用例创建Bug")
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

    # 获取测试用例
    print("\n" + "-" * 80)
    print("1. 获取测试用例列表")
    print("-" * 80)
    success, cases = client.get_testcases(product_id)
    if success:
        if isinstance(cases, dict):
            case_list = list(cases.values())
        else:
            case_list = cases
        print(f"✅ 共有 {len(case_list)} 个测试用例")

        if not case_list:
            print("❌ 没有测试用例，先创建一个")
            return 1

        # 选择第一个测试用例
        case = case_list[0] if isinstance(case_list[0], dict) else {"id": case_list[0]}
        case_id = case.get("id")
        print(f"\n选择测试用例: ID={case_id}, 标题={case.get('title')}")
    else:
        print(f"❌ 获取测试用例失败")
        return 1

    # 查看测试用例详情
    print("\n" + "-" * 80)
    print("2. 查看测试用例详情")
    print("-" * 80)
    success, case_detail = client.get_testcase(case_id)
    if success:
        print(f"ID: {case_detail.get('id')}")
        print(f"标题: {case_detail.get('title')}")
        print(f"类型: {case_detail.get('type')}")
        print(f"优先级: {case_detail.get('pri')}")

        # 显示步骤
        steps = case_detail.get("steps", {})
        if steps:
            print(f"\n步骤 ({len(steps)} 步):")
            for step_id, step in steps.items():
                if isinstance(step, dict):
                    desc = step.get("desc", "")
                    expect = step.get("expect", "")
                    print(f"  - {desc}")
                    if expect:
                        print(f"    预期: {expect}")

    # 方法1: 使用 create_bug_from_testcase
    print("\n" + "-" * 80)
    print("3. 方法1: 使用 create_bug_from_testcase")
    print("-" * 80)
    success, result = client.create_bug_from_testcase(
        case_id=case_id, severity="3", pri="3", type="codeerror", assignedTo="admin"
    )
    print(f"结果: success={success}")
    print(f"返回: {result}")

    if success:
        # 查看测试用例的 toBugs
        success, case_detail = client.get_testcase(case_id)
        if success:
            print(f"\n测试用例关联的Bug: {case_detail.get('toBugs')}")

    # 方法2: 使用 create_bug + case_id 参数
    print("\n" + "-" * 80)
    print("4. 方法2: 使用 create_bug + case_id 参数")
    print("-" * 80)
    timestamp = datetime.now().strftime("%H%M%S")
    success, result = client.create_bug(
        product_id=product_id,
        title=f"方法2创建的Bug_{timestamp}",
        case_id=case_id,
        severity="3",
        pri="3",
        type="config",
        steps=f"从测试用例 {case_id} 发现的问题",
        assignedTo="admin",
    )
    print(f"结果: success={success}")
    print(f"返回: {result}")

    if success:
        # 查看测试用例的 toBugs
        success, case_detail = client.get_testcase(case_id)
        if success:
            print(f"\n测试用例关联的Bug: {case_detail.get('toBugs')}")

    # 查看我的Bug
    print("\n" + "-" * 80)
    print("5. 查看我的Bug列表")
    print("-" * 80)
    success, my_bugs = client.get_my_bugs("assignedTo")
    if success:
        print(f"✅ 指派给我的Bug: {len(my_bugs)} 个")
        for bug in my_bugs[:5]:
            print(f"   [{bug.get('id')}] {bug.get('title')} ({bug.get('status')})")
            if bug.get("case"):
                print(f"       关联用例: {bug.get('case')}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
