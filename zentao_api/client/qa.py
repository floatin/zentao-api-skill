from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class QAMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 测试相关方法 ====================

    def get_testcases(
        self, product_id: str, browse_type: str = "all"
    ) -> Tuple[bool, List[Dict]]:
        """获取测试用例列表（老 API）

        Args:
            product_id: 产品ID
            browse_type: 浏览类型 (all, bymodule, assignedtome)

        Returns:
            (success, cases) 测试用例列表

        Example:
            >>> success, cases = client.get_testcases("1")
            >>> for case in cases:
            ...     print(f"[{case['id']}] {case['title']}")
        """
        success, result = self.old_request(
            "GET", f"/testcase-browse-{product_id}-{browse_type}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("cases", [])
        return False, []

    def get_testcase(self, case_id: str) -> Tuple[bool, Dict]:
        """获取测试用例详情（老 API）

        Args:
            case_id: 用例ID

        Returns:
            (success, case_info) 用例详情

        Example:
            >>> success, case = client.get_testcase("1")
            >>> print(f"标题: {case['title']}")
        """
        success, result = self.old_request("GET", f"/testcase-view-{case_id}.json")
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("case", {})
        return False, {}

    def create_testcase(
        self,
        product_id: str,
        title: str,
        case_type: str = "feature",
        module: str = "0",
        story: str = "0",
        branch: str = "0",
        **kwargs,
    ) -> Tuple[bool, Dict]:
        """创建测试用例（老 API）

        Args:
            product_id: 产品ID
            title: 用例标题
            case_type: 用例类型 (feature, performance, config, install, security, interface, unit, other)
            module: 模块ID，默认 "0"
            story: 需求ID，默认 "0"
            branch: 分支ID，默认 "0"
            **kwargs: 其他参数:
                - stage: 适用阶段 (unittest, feature, intergrate, system, smoke, bvt)
                - pri: 优先级 (0-4)
                - precondition: 前置条件
                - steps: 用例步骤（字符串，按换行分割）
                - expect: 预期结果（字符串，按换行分割）
                - steps_list: 步骤列表（列表格式，与steps二选一）
                - expects_list: 预期结果列表（列表格式，与expect二选一）

        Returns:
            (success, result)

        Example:
            >>> # 字符串格式（自动按换行分割）
            >>> success, result = client.create_testcase(
            ...     product_id="1",
            ...     title="测试登录功能",
            ...     case_type="feature",
            ...     steps="1. 打开登录页面\\n2. 输入用户名密码\\n3. 点击登录",
            ...     expect="登录成功"
            ... )
            >>> # 列表格式（精确控制）
            >>> success, result = client.create_testcase(
            ...     product_id="1",
            ...     title="测试登录功能",
            ...     module="1",
            ...     story="5",
            ...     steps_list=["打开登录页面", "输入用户名密码", "点击登录"],
            ...     expects_list=["显示登录表单", "输入成功", "登录成功"]
            ... )
        """
        data = {
            "product": product_id,
            "title": title,
            "type": case_type,
        }

        # 处理步骤和预期结果
        steps_text = kwargs.pop("steps", None)
        expect_text = kwargs.pop("expect", None)
        steps_list = kwargs.pop("steps_list", None)
        expects_list = kwargs.pop("expects_list", None)

        # 转换步骤格式
        if steps_list:
            # 直接使用列表
            for i, step in enumerate(steps_list, start=1):
                data[f"steps[{i}]"] = step
        elif steps_text:
            # 按换行分割
            steps = [s.strip() for s in steps_text.split("\n") if s.strip()]
            for i, step in enumerate(steps, start=1):
                data[f"steps[{i}]"] = step

        # 转换预期结果格式
        if expects_list:
            # 直接使用列表
            for i, exp in enumerate(expects_list, start=1):
                data[f"expects[{i}]"] = exp
        elif expect_text:
            # 按换行分割
            expects = [e.strip() for e in expect_text.split("\n") if e.strip()]
            for i, exp in enumerate(expects, start=1):
                data[f"expects[{i}]"] = exp

        # 其他参数
        data.update(kwargs)

        # 构建URL: /testcase-create-{product}-{module}-{story}-{branch}-{0}
        return self.old_request(
            "POST",
            f"/testcase-create-{product_id}-{module}-{story}-{branch}-0.json",
            data,
        )

    def delete_testcase(self, case_id: str, confirm: str = "yes") -> Tuple[bool, Dict]:
        """删除测试用例（老 API）

        Args:
            case_id: 用例ID
            confirm: 确认删除，可选值: "yes"（删除）| "no"（不删除），默认 "yes"

        Returns:
            (success, result)

        Note:
            - 禅道使用软删除机制，删除后用例的 deleted 字段标记为 '1'
            - 删除后用例不再显示在列表中，但数据仍保留在数据库
            - 返回 HTML 响应表示删除成功

        Example:
            >>> success, result = client.delete_testcase("10")
            >>> # 验证删除
            >>> success, case = client.get_testcase("10")
            >>> if case.get('deleted') == '1':
            ...     print("已删除")
        """
        return self.old_request("GET", f"/testcase-delete-{case_id}-{confirm}.json")

    def get_testsuites(self, product_id: str) -> Tuple[bool, List[Dict]]:
        """获取测试套件列表（老 API）

        Args:
            product_id: 产品ID

        Returns:
            (success, suites) 测试套件列表

        Example:
            >>> success, suites = client.get_testsuites("1")
            >>> for suite in suites:
            ...     print(f"[{suite['id']}] {suite['name']}")
        """
        success, result = self.old_request(
            "GET", f"/testsuite-browse-{product_id}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("suites", [])
        return False, []

    def get_testsuite(self, suite_id: str) -> Tuple[bool, Dict]:
        """获取测试套件详情（老 API）

        Args:
            suite_id: 套件ID

        Returns:
            (success, suite_info) 套件详情

        Example:
            >>> success, suite = client.get_testsuite("1")
            >>> print(f"套件名: {suite['name']}")
        """
        success, result = self.old_request("GET", f"/testsuite-view-{suite_id}.json")
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("suite", {})
        return False, {}

    def create_testsuite(
        self, product_id: str, name: str, desc: str = ""
    ) -> Tuple[bool, Dict]:
        """创建测试套件（老 API）

        Args:
            product_id: 产品ID
            name: 套件名称
            desc: 套件描述

        Returns:
            (success, result)

        Example:
            >>> success, result = client.create_testsuite("1", "冒烟测试套件", "冒烟测试用例集合")
        """
        data = {"product": product_id, "name": name, "desc": desc}
        return self.old_request("POST", f"/testsuite-create-{product_id}.json", data)

    def delete_testsuite(self, suite_id: str) -> Tuple[bool, Dict]:
        """删除测试套件（老 API）

        Args:
            suite_id: 套件ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.delete_testsuite("1")
        """
        return self.old_request("GET", f"/testsuite-delete-{suite_id}-yes.json")

    def get_testtasks(
        self, product_id: str, task_type: str = "all"
    ) -> Tuple[bool, List[Dict]]:
        """获取测试任务列表（老 API）

        Args:
            product_id: 产品ID
            task_type: 任务类型 (all, wait, doing, done, blocked)

        Returns:
            (success, tasks) 测试任务列表

        Example:
            >>> success, tasks = client.get_testtasks("1")
            >>> for task in tasks:
            ...     print(f"[{task['id']}] {task['name']}")
        """
        success, result = self.old_request(
            "GET", f"/testtask-browse-{product_id}-{task_type}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("tasks", [])
        return False, []

    def get_testtask(self, task_id: str) -> Tuple[bool, Dict]:
        """获取测试任务详情（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, task_info) 任务详情

        Example:
            >>> success, task = client.get_testtask("1")
            >>> print(f"任务名: {task['name']}")
        """
        success, result = self.old_request("GET", f"/testtask-view-{task_id}.json")
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("task", {})
        return False, {}

    def create_testtask(
        self, product_id: str, name: str, begin: str = "", end: str = "", desc: str = ""
    ) -> Tuple[bool, Dict]:
        """创建测试任务（老 API）

        Args:
            product_id: 产品ID
            name: 任务名称
            begin: 开始日期 (YYYY-MM-DD)
            end: 结束日期 (YYYY-MM-DD)
            desc: 任务描述

        Returns:
            (success, result) 注意：可能返回HTML

        Example:
            >>> success, result = client.create_testtask(
            ...     product_id="1",
            ...     name="Sprint1测试",
            ...     begin="2026-03-01",
            ...     end="2026-03-15"
            ... )
        """
        data = {
            "product": product_id,
            "name": name,
            "begin": begin,
            "end": end,
            "desc": desc,
        }
        return self.old_request("POST", f"/testtask-create-{product_id}.json", data)

    def delete_testtask(self, task_id: str) -> Tuple[bool, Dict]:
        """删除测试任务（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.delete_testtask("1")
        """
        return self.old_request("GET", f"/testtask-delete-{task_id}-yes.json")

    def start_testtask(self, task_id: str) -> Tuple[bool, Dict]:
        """开始测试任务（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.start_testtask("1")
        """
        return self.old_request("POST", f"/testtask-start-{task_id}.json")

    def close_testtask(self, task_id: str) -> Tuple[bool, Dict]:
        """关闭测试任务（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.close_testtask("1")
        """
        return self.old_request("POST", f"/testtask-close-{task_id}.json")

    def block_testtask(self, task_id: str) -> Tuple[bool, Dict]:
        """阻塞测试任务（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.block_testtask("1")
        """
        return self.old_request("POST", f"/testtask-block-{task_id}.json")

    def activate_testtask(self, task_id: str) -> Tuple[bool, Dict]:
        """激活测试任务（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.activate_testtask("1")
        """
        return self.old_request("POST", f"/testtask-activate-{task_id}.json")

    def get_testreports(
        self, product_id: str, project_id: str = "0"
    ) -> Tuple[bool, List[Dict]]:
        """获取测试报告列表（老 API）

        Args:
            product_id: 产品ID
            project_id: 项目ID，默认 "0"

        Returns:
            (success, reports) 测试报告列表

        Example:
            >>> success, reports = client.get_testreports("1")
            >>> for report in reports:
            ...     print(f"[{report['id']}] {report['title']}")
        """
        success, result = self.old_request(
            "GET", f"/testreport-browse-{product_id}-product-{project_id}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("reports", [])
        return False, []

    def delete_testreport(self, report_id: str) -> Tuple[bool, Dict]:
        """删除测试报告（老 API）

        Args:
            report_id: 报告ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.delete_testreport("1")
        """
        return self.old_request("GET", f"/testreport-delete-{report_id}-yes.json")


    # ==================== 测试用例模块补充方法 ====================

    def edit_testcase(self, case_id: str, **kwargs) -> Tuple[bool, Dict]:
        """编辑测试用例（老 API）

        Args:
            case_id: 用例ID
            **kwargs: 要修改的字段 (title, type, pri, module, story, steps, expects, etc.)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.edit_testcase("1", title="新标题", pri="2")
        """
        return self.old_request("POST", f"/testcase-edit-{case_id}.json", kwargs)

    def batch_create_testcases(
        self, product_id: str, cases: List[Dict]
    ) -> Tuple[bool, Dict]:
        """批量创建测试用例（老 API）

        Args:
            product_id: 产品ID
            cases: 用例列表，每个用例包含:
                - title: 用例标题
                - type: 用例类型
                - module: 模块ID
                - story: 需求ID
                - steps: 步骤列表
                - expects: 预期结果列表

        Returns:
            (success, result)

        Example:
            >>> cases = [
            ...     {"title": "测试用例1", "type": "feature"},
            ...     {"title": "测试用例2", "type": "performance"}
            ... ]
            >>> success, result = client.batch_create_testcases("1", cases)
        """
        data = {}
        for i, case in enumerate(cases):
            data[f"title[{i}]"] = case.get("title", "")
            data[f"type[{i}]"] = case.get("type", "feature")
            if case.get("module"):
                data[f"module[{i}]"] = case.get("module")
            if case.get("story"):
                data[f"story[{i}]"] = case.get("story")

        return self.old_request(
            "POST", f"/testcase-batchCreate-{product_id}.json", data
        )

    def import_testcases(self, product_id: str, file_path: str) -> Tuple[bool, Dict]:
        """导入测试用例（老 API）

        Args:
            product_id: 产品ID
            file_path: 导入文件路径

        Returns:
            (success, result)

        Note:
            这个方法需要上传文件，暂时返回错误信息

        Example:
            >>> success, result = client.import_testcases("1", "/path/to/import.csv")
        """
        # TODO: 需要实现文件上传
        return False, {"message": "文件导入功能暂未实现"}

    def export_testcases(self, product_id: str) -> Tuple[bool, Dict]:
        """导出测试用例（老 API）

        Args:
            product_id: 产品ID

        Returns:
            (success, result) 注意：返回文件内容

        Example:
            >>> success, result = client.export_testcases("1")
        """
        return self.old_request("POST", f"/testcase-export-{product_id}.json")

    def link_testcase_story(self, case_id: str, story_id: str) -> Tuple[bool, Dict]:
        """测试用例关联需求（老 API）

        Args:
            case_id: 用例ID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_testcase_story("1", "5")
        """
        return self.old_request(
            "POST", f"/testcase-linkStory-{case_id}-{story_id}.json"
        )

    def unlink_testcase_story(self, case_id: str, story_id: str) -> Tuple[bool, Dict]:
        """取消测试用例关联需求（老 API）

        Args:
            case_id: 用例ID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_testcase_story("1", "5")
        """
        return self.old_request(
            "GET", f"/testcase-unlinkStory-{case_id}-{story_id}.json"
        )

