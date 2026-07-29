#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试测试用例创建接口
"""

import sys
import json
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
    print("调试测试用例创建接口")
    print("=" * 60)

    credentials = read_credentials()
    if not credentials:
        print("❌ 未找到禅道凭证")
        return 1

    print(f"API地址: {credentials['endpoint']}")

    client = ZenTaoClient(
        credentials["endpoint"], credentials["username"], credentials["password"]
    )

    print("\n正在获取 Session...")
    sid = client.get_session()
    if not sid:
        print("❌ 认证失败")
        return 1
    print(f"✅ 认证成功, sid: {sid[:20]}...")

    # 获取产品ID
    success, products = client.get_products()
    print(f"产品列表: {products}")
    product_id = list(products.keys())[0] if success else "4"
    print(f"使用产品ID: {product_id}")

    # 测试0: 获取创建页面
    print("\n" + "-" * 60)
    print("测试0: 获取测试用例创建页面")
    print("-" * 60)

    url = f"{client.old_api_base}/testcase-create-{product_id}.json"
    print(f"URL: {url}")

    response = client.session.get(url, params={"zentaosid": client.sid}, timeout=30)

    print(f"HTTP状态码: {response.status_code}")
    print(f"响应内容前1000字符:\n{response.text[:1000]}")

    # 解析JSON看看有什么字段
    try:
        result = response.json()
        if "data" in result:
            data_obj = json.loads(result["data"])
            print(f"\n解析后的data对象键: {data_obj.keys()}")
    except:
        print("\n无法解析JSON")

    # 测试1: 使用 .json 端点，简单参数
    print("\n" + "-" * 60)
    print("测试1: 使用 .json 端点创建测试用例（简单参数）")
    print("-" * 60)

    data = {
        "product": product_id,
        "title": f"简单测试_{datetime.now().strftime('%H%M%S')}",
        "type": "feature",
        "pri": "3",
    }

    success, result = client.old_request(
        "POST", f"/testcase-create-{product_id}-0-0-0-0.json", data
    )
    print(f"结果: success={success}")
    print(f"返回: {result}")

    # 测试2: 使用 .html 端点，带步骤
    print("\n" + "-" * 60)
    print("测试2: 使用 .html 端点创建测试用例（带步骤）")
    print("-" * 60)

    data = {
        "product": product_id,
        "title": f"JSON测试_{datetime.now().strftime('%H%M%S')}",
        "type": "feature",
        "pri": "3",
        "steps": "步骤1\n步骤2\n步骤3",
        "expect": "预期结果",
    }

    success, result = client.old_request(
        "POST", f"/testcase-create-{product_id}-0-0-0-0.json", data
    )
    print(f"结果: success={success}")
    print(f"返回: {result}")

    # 测试2: 使用 .html 端点
    print("\n" + "-" * 60)
    print("测试2: 使用 .html 端点创建测试用例")
    print("-" * 60)

    url = (
        f"{client.old_api_base}/testcase-create-{product_id}-0-0-0-0.html?onlybody=yes"
    )
    print(f"URL: {url}")

    response = client.session.post(
        url, data=data, params={"zentaosid": client.sid}, timeout=30
    )

    print(f"HTTP状态码: {response.status_code}")
    print(f"响应内容长度: {len(response.text)}")
    print(f"响应内容前500字符:\n{response.text[:500]}")

    # 检查是否有错误
    if "error" in response.text.lower() or "失败" in response.text:
        print("\n❌ 检测到错误信息")
    elif "成功" in response.text or "success" in response.text.lower():
        print("\n✅ 检测到成功信息")
    else:
        print("\n⚠️  响应内容需要手动检查")

    # 查询测试用例验证
    print("\n" + "-" * 60)
    print("验证: 查询测试用例列表")
    print("-" * 60)
    success, cases = client.get_testcases(product_id)
    if success:
        if isinstance(cases, dict):
            case_list = list(cases.values())
        else:
            case_list = cases
        print(f"共 {len(case_list)} 个测试用例")
        for case in case_list[-5:]:
            if isinstance(case, dict):
                print(f"   [{case.get('id')}] {case.get('title')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
