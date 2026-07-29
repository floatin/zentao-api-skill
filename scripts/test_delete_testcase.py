#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试删除测试用例接口
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
    print("测试删除测试用例接口")
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

    # 测试1: 创建并删除测试用例
    print("\n" + "-" * 80)
    print("测试1: 创建并删除测试用例")
    print("-" * 80)

    timestamp = datetime.now().strftime("%H%M%S")

    # 创建测试用例
    print(f"\n1. 创建测试用例 '删除测试1_{timestamp}'...")
    success, result = client.create_testcase(
        product_id=product_id,
        title=f"删除测试1_{timestamp}",
        case_type="feature",
        pri="3",
        steps_list=["步骤1", "步骤2"],
        expects_list=["预期1", "预期2"],
    )

    if not success:
        print(f"❌ 创建失败: {result}")
        return 1

    print(f"✅ 创建成功")

    # 查询刚创建的用例
    success, cases = client.get_testcases(product_id)
    if success:
        if isinstance(cases, dict):
            case_list = list(cases.values())
        else:
            case_list = cases

        # 找到刚创建的用例
        case_id = None
        for case in case_list:
            if isinstance(case, dict) and f"删除测试1_{timestamp}" in case.get(
                "title", ""
            ):
                case_id = case.get("id")
                break

        if not case_id:
            print("❌ 未找到刚创建的测试用例")
            return 1

        print(f"2. 找到测试用例: ID={case_id}")

        # 删除测试用例 (confirm="yes")
        print(f"\n3. 删除测试用例 (confirm='yes')...")
        success, result = client.delete_testcase(case_id, confirm="yes")
        print(f"   结果: success={success}")
        if isinstance(result, dict) and "raw" in result:
            print(f"   返回HTML响应，长度: {len(result['raw'])}")
        else:
            print(f"   返回: {result}")

        # 验证删除
        print(f"\n4. 验证删除...")
        success, case = client.get_testcase(case_id)
        if not success or not case:
            print("   ✅ 测试用例已完全删除")
        elif case.get("deleted") == "1":
            print("   ✅ 测试用例已标记为删除（软删除）")
            print(f"      deleted字段: {case.get('deleted')}")
        else:
            print(f"   ❌ 测试用例仍存在: {case.get('title')}")
    else:
        print("❌ 查询测试用例失败")
        return 1

    # 测试2: 创建后尝试取消删除
    print("\n" + "-" * 80)
    print("测试2: 创建后尝试取消删除 (confirm='no')")
    print("-" * 80)

    timestamp2 = datetime.now().strftime("%H%M%S")

    # 创建测试用例
    print(f"\n1. 创建测试用例 '删除测试2_{timestamp2}'...")
    success, result = client.create_testcase(
        product_id=product_id,
        title=f"删除测试2_{timestamp2}",
        case_type="feature",
        pri="3",
        steps_list=["步骤A", "步骤B"],
        expects_list=["预期A", "预期B"],
    )

    if not success:
        print(f"❌ 创建失败: {result}")
        return 1

    print(f"✅ 创建成功")

    # 查询刚创建的用例
    success, cases = client.get_testcases(product_id)
    if success:
        if isinstance(cases, dict):
            case_list = list(cases.values())
        else:
            case_list = cases

        # 找到刚创建的用例
        case_id2 = None
        for case in case_list:
            if isinstance(case, dict) and f"删除测试2_{timestamp2}" in case.get(
                "title", ""
            ):
                case_id2 = case.get("id")
                break

        if not case_id2:
            print("❌ 未找到刚创建的测试用例")
            return 1

        print(f"2. 找到测试用例: ID={case_id2}")

        # 尝试使用 confirm="no" 删除
        print(f"\n3. 尝试删除测试用例 (confirm='no')...")
        success, result = client.delete_testcase(case_id2, confirm="no")
        print(f"   结果: success={success}")
        if isinstance(result, dict) and "raw" in result:
            print(f"   返回HTML响应，长度: {len(result['raw'])}")
        else:
            print(f"   返回: {result}")

        # 验证是否删除
        print(f"\n4. 验证是否删除...")
        success, case = client.get_testcase(case_id2)
        if not success or not case:
            print("   ⚠️  测试用例已删除（不应该发生）")
        elif case.get("deleted") == "1":
            print("   ⚠️  测试用例已标记为删除（不应该发生）")
        else:
            print("   ✅ 测试用例未被删除（符合预期）")
            print(f"      标题: {case.get('title')}")
            print(f"      deleted字段: {case.get('deleted')}")

            # 清理：删除这个测试用例
            print(f"\n5. 清理：删除测试用例...")
            client.delete_testcase(case_id2, confirm="yes")
            print("   ✅ 已删除")

    # 测试3: 查看当前测试用例列表
    print("\n" + "-" * 80)
    print("测试3: 查看当前测试用例列表")
    print("-" * 80)

    success, cases = client.get_testcases(product_id)
    if success:
        if isinstance(cases, dict):
            case_list = list(cases.values())
        else:
            case_list = cases

        print(f"当前测试用例数量: {len(case_list)}")
        print("\n最近的测试用例:")
        for case in case_list[:5]:
            if isinstance(case, dict):
                deleted = case.get("deleted", "0")
                status = "已删除" if deleted == "1" else "正常"
                print(f"  [{case.get('id')}] {case.get('title')} ({status})")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
