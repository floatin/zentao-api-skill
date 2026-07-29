#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试创建测试用例接口
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
    print("=" * 60)
    print("测试创建测试用例接口")
    print("=" * 60)

    credentials = read_credentials()
    if not credentials:
        print("❌ 未找到禅道凭证")
        return 1

    print(f"API地址: {credentials['endpoint']}")
    print(f"用户名: {credentials['username']}")

    client = ZenTaoClient(
        credentials["endpoint"], credentials["username"], credentials["password"]
    )

    print("\n正在获取 Session...")
    sid = client.get_session()
    if not sid:
        print("❌ 认证失败")
        return 1
    print(f"✅ 认证成功")

    # 获取产品列表
    print("\n" + "-" * 60)
    print("1. 获取产品列表")
    print("-" * 60)
    success, products = client.get_products()
    if not success:
        products = client.get_product_list_old()
        products = {v: k for k, v in products.items()}

    if not products:
        print("❌ 未找到产品，先创建产品")
        success, result = client.create_product(
            name="测试产品", code="TEST", po="admin", status="normal"
        )
        if success:
            print("✅ 创建产品成功")
            success, products = client.get_products()
            if not success:
                products = client.get_product_list_old()
                products = {v: k for k, v in products.items()}

    print(f"产品列表: {products}")

    # products 格式为 {'id': 'name'}，需要使用 id
    product_id = list(products.keys())[0] if products else "1"
    print(f"使用产品ID: {product_id}")

    # 创建测试用例
    print("\n" + "-" * 60)
    print("2. 创建测试用例")
    print("-" * 60)

    testcases = [
        {
            "title": f"登录功能测试_{datetime.now().strftime('%H%M%S')}",
            "case_type": "feature",
            "pri": "3",
            "steps_list": [
                "打开登录页面",
                "输入用户名: admin",
                "输入密码: 123456",
                "点击登录按钮",
            ],
            "expects_list": [
                "显示登录表单",
                "用户名输入成功",
                "密码输入成功",
                "登录成功，跳转到首页",
            ],
        },
        {
            "title": f"用户注册测试_{datetime.now().strftime('%H%M%S')}",
            "case_type": "feature",
            "pri": "2",
            "steps": "1.打开注册页面\n2.填写用户信息\n3.点击注册按钮",
            "expect": "注册成功，自动登录",
        },
        {
            "title": f"接口性能测试_{datetime.now().strftime('%H%M%S')}",
            "case_type": "performance",
            "pri": "1",
            "steps": "1.准备测试数据\n2.执行压力测试\n3.记录响应时间",
            "expect": "平均响应时间<200ms",
        },
    ]

    created_cases = []
    for tc in testcases:
        print(f"\n创建用例: {tc['title']}")

        # 构建参数
        params = {
            "product_id": product_id,
            "title": tc["title"],
            "case_type": tc["case_type"],
            "pri": tc["pri"],
        }

        # 添加步骤（支持两种格式）
        if "steps_list" in tc:
            params["steps_list"] = tc["steps_list"]
            params["expects_list"] = tc.get("expects_list")
        elif "steps" in tc:
            params["steps"] = tc["steps"]
            params["expect"] = tc.get("expect")

        success, result = client.create_testcase(**params)
        print(f"   返回结果: success={success}, result={result}")
        if success:
            print(f"   ✅ 创建成功")
            created_cases.append(tc["title"])
        else:
            # 禅道老API可能返回空响应，实际可能已创建成功
            if isinstance(result, dict) and "raw" in result:
                raw_content = result.get("raw", "")
                print(f"   ⚠️  返回HTML响应长度: {len(raw_content)}")
                # 检查是否有错误信息
                if "error" in raw_content.lower() or "失败" in raw_content:
                    print(f"   ❌ 可能创建失败")
                else:
                    print(f"   ✅ 可能创建成功（需查询验证）")
                    created_cases.append(tc["title"])
            else:
                print(f"   ❌ 创建失败: {result}")

    # 查询测试用例
    print("\n" + "-" * 60)
    print("3. 查询测试用例列表")
    print("-" * 60)
    success, cases = client.get_testcases(product_id)
    if success:
        # cases 可能是 dict 或 list
        if isinstance(cases, dict):
            case_list = list(cases.values())
        else:
            case_list = cases
        print(f"✅ 共有 {len(case_list)} 个测试用例")
        for case in case_list[:10]:
            if isinstance(case, dict):
                print(
                    f"   [{case.get('id')}] {case.get('title')} - {case.get('type', '')}"
                )
            else:
                print(f"   {case}")
    else:
        print(f"❌ 查询失败: {cases}")

    # 获取测试用例详情
    if cases:
        print("\n" + "-" * 60)
        print("4. 获取测试用例详情")
        print("-" * 60)
        # 获取第一个用例的ID
        if isinstance(cases, dict):
            case_id = list(cases.keys())[0]
        else:
            case_id = cases[0].get("id")
        success, case_detail = client.get_testcase(str(case_id))
        if success:
            print(f"✅ 用例ID: {case_detail.get('id')}")
            print(f"   标题: {case_detail.get('title')}")
            print(f"   类型: {case_detail.get('type')}")
            print(f"   优先级: {case_detail.get('pri')}")
            print(f"   状态: {case_detail.get('status')}")
        else:
            print(f"❌ 获取详情失败")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print(f"创建用例数: {len(created_cases)}")
    for title in created_cases:
        print(f"   - {title}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
