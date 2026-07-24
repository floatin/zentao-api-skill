from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class BugsMixin:
    """Mixin for ZenTaoClient."""
    # ==================== Bug 相关方法 ====================

    def get_project_bugs(
        self, project_id: str, status: str = "all"
    ) -> Tuple[bool, List[Dict]]:
        """获取项目的Bug列表（老 API）

        Args:
            project_id: 项目ID
            status: Bug状态，默认 "all" 获取所有状态

        Returns:
            (success, bugs) Bug列表

        Example:
            >>> success, bugs = client.get_project_bugs("1")
            >>> for bug in bugs:
            ...     print(f"[{bug['id']}] {bug['title']} ({bug['status']})")
        """
        return True, self._data(f"/project-bug-{project_id}.json", "bugs")

    def get_bug(self, bug_id: str) -> Tuple[bool, Dict]:
        """获取Bug详情（老 API）

        Args:
            bug_id: BugID

        Returns:
            (success, bug_info) Bug详情

        Example:
            >>> success, bug = client.get_bug("1")
            >>> print(f"标题: {bug['title']}, 状态: {bug['status']}")
        """
        return True, self._data_dict(f"/bug-view-{bug_id}.json", "bug")

    def create_bug(
        self,
        product_id: str,
        title: str,
        opened_build: str = "trunk",
        project_id: str = None,
        case_id: str = None,
        **kwargs,
    ) -> Tuple[bool, Dict]:
        """创建Bug（老 API）

        Args:
            product_id: 产品ID
            title: Bug标题
            opened_build: 影响版本，默认 "trunk"
            project_id: 项目ID（可选）
            case_id: 测试用例ID（可选，用于关联测试用例）
            **kwargs: 其他参数，如:
                - module: 模块ID
                - severity: 严重程度 (1-4)
                - pri: 优先级 (0-4)
                - type: Bug类型 (codeerror, config, install, security, performance, standard, automation, designdefect, others)
                - steps: 重现步骤
                - assignedTo: 指派给
                - deadline: 截止日期 (YYYY-MM-DD)

        Returns:
            (success, result) 创建结果

        Note:
            创建Bug需要产品存在且有权限。
            传入 case_id 可以关联测试用例。

        Example:
            >>> success, result = client.create_bug(
            ...     product_id="1",
            ...     title="测试Bug",
            ...     severity="3",
            ...     pri="3",
            ...     assignedTo="admin"
            ... )
            >>> # 从测试用例创建Bug
            >>> success, result = client.create_bug(
            ...     product_id="1",
            ...     title="从测试用例创建的Bug",
            ...     case_id="8",
            ...     steps="测试用例8发现的问题"
            ... )
        """
        data = {
            "product": product_id,
            "title": title,
            "openedBuild": opened_build,
        }
        if project_id:
            data["project"] = project_id
        if case_id:
            data["case"] = case_id
        data.update(kwargs)

        # 构建URL
        url = f"/bug-create-{product_id}-0"
        if project_id:
            url += f"-projectID={project_id}"
        url += ".json"

        success, result = self.old_request("POST", url, data)

        if success:
            return True, {"message": "创建Bug请求已发送", "result": result}
        else:
            return False, result

    def create_bug_from_testcase(
        self,
        case_id: str,
        product_id: str = None,
        title: str = None,
        **kwargs,
    ) -> Tuple[bool, Dict]:
        """从测试用例创建Bug（老 API）

        Args:
            case_id: 测试用例ID *必填
            product_id: 产品ID（可选，不传则从测试用例获取）
            title: Bug标题（可选，不传则使用测试用例标题）
            **kwargs: 其他参数，如:
                - severity: 严重程度 (1-4)
                - pri: 优先级 (0-4)
                - type: Bug类型
                - steps: 重现步骤（可选，不传则使用测试用例步骤）
                - assignedTo: 指派给
                - opened_build: 影响版本，默认 "trunk"

        Returns:
            (success, result) 创建结果

        Example:
            >>> success, result = client.create_bug_from_testcase(
            ...     case_id="8",
            ...     title="登录功能测试发现Bug",
            ...     severity="3"
            ... )
        """
        # 获取测试用例详情
        success, case = self.get_testcase(case_id)
        if not success:
            return False, {"message": f"测试用例 {case_id} 不存在"}

        # 使用测试用例信息填充默认值
        if not product_id:
            product_id = case.get("product", "0")

        if not title:
            title = f"[测试用例{case_id}] {case.get('title', '')}"

        # 准备Bug数据
        data = {
            "case": case_id,
            "product": product_id,
            "title": title,
            "openedBuild": kwargs.pop("opened_build", "trunk"),
        }

        # 如果测试用例有步骤，转换为Bug重现步骤
        if "steps" not in kwargs and case.get("steps"):
            steps_text = ""
            for step_id, step in case.get("steps", {}).items():
                if isinstance(step, dict):
                    desc = step.get("desc", "")
                    expect = step.get("expect", "")
                    if desc:
                        steps_text += f"{desc}"
                        if expect:
                            steps_text += f" (预期: {expect})"
                        steps_text += "\n"
            if steps_text:
                data["steps"] = steps_text.strip()

        data.update(kwargs)

        # 构建URL
        url = f"/bug-create-{product_id}-0.json"

        success, result = self.old_request("POST", url, data)

        if success:
            return True, {
                "message": "从测试用例创建Bug成功",
                "case_id": case_id,
                "result": result,
            }
        else:
            return False, result

    def resolve_bug(
        self,
        bug_id: str,
        resolution: str = "fixed",
        resolved_build: str = "trunk",
        comment: str = "",
    ) -> Tuple[bool, Dict]:
        """解决Bug（老 API）

        Args:
            bug_id: BugID
            resolution: 解决方案，可选值: fixed, postponed, willnotfix, duplicate, tostory
            resolved_build: 解决版本，默认 "trunk"
            comment: 解决备注

        Returns:
            (success, result)

        Note:
            解决后Bug状态变为 'resolved'。
            建议使用 .html 端点。

        Example:
            >>> success, result = client.resolve_bug("1", "fixed", "trunk", "已修复")
        """
        data = {
            "resolution": resolution,
            "resolvedBuild": resolved_build,
            "comment": comment,
        }

        url = f"{self.old_api_base}/bug-resolve-{bug_id}.html?onlybody=yes"
        response = self.session.post(
            url, data=data, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {"message": "解决Bug成功", "status_code": response.status_code}
        else:
            return False, {
                "message": f"解决失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def close_bug(self, bug_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """关闭Bug（老 API）

        Args:
            bug_id: BugID
            comment: 关闭备注

        Returns:
            (success, result)

        Note:
            关闭后Bug状态变为 'closed'。

        Example:
            >>> success, result = client.close_bug("1", "已验证关闭")
        """
        data = {}
        if comment:
            data["comment"] = comment

        success, result = self.old_request("POST", f"/bug-close-{bug_id}.json", data)
        return success, result

    def activate_bug(self, bug_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """激活Bug（老 API）

        Args:
            bug_id: BugID
            comment: 激活备注

        Returns:
            (success, result)

        Note:
            激活后Bug状态变为 'active'。

        Example:
            >>> success, result = client.activate_bug("1", "问题重现，重新打开")
        """
        data = {}
        if comment:
            data["comment"] = comment

        success, result = self.old_request("POST", f"/bug-activate-{bug_id}.json", data)
        return success, result

    def assign_bug(
        self, bug_id: str, assigned_to: str, comment: str = ""
    ) -> Tuple[bool, Dict]:
        """指派Bug（老 API）

        Args:
            bug_id: BugID
            assigned_to: 指派给谁（用户名）
            comment: 指派备注

        Returns:
            (success, result)

        Example:
            >>> success, result = client.assign_bug("1", "zhangsan", "请处理")
        """
        data = {"assignedTo": assigned_to}
        if comment:
            data["comment"] = comment

        url = f"{self.old_api_base}/bug-assignTo-{bug_id}.json"
        response = self.session.post(
            url, data=data, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {"message": "指派Bug成功", "status_code": response.status_code}
        else:
            return False, {
                "message": f"指派失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def confirm_bug(self, bug_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """确认Bug（老 API）

        Args:
            bug_id: BugID
            comment: 确认备注

        Returns:
            (success, result)

        Example:
            >>> success, result = client.confirm_bug("1", "确认是Bug")
        """
        data = {}
        if comment:
            data["comment"] = comment

        success, result = self.old_request(
            "POST", f"/bug-confirmBug-{bug_id}.json", data
        )
        return success, result

    def delete_bug(self, bug_id: str) -> Tuple[bool, Dict]:
        """删除Bug（老 API）

        Args:
            bug_id: BugID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.delete_bug("1")
        """
        return self.old_request("GET", f"/bug-delete-{bug_id}-yes.json")


    # ==================== Bug模块补充方法 ====================

    def edit_bug(self, bug_id: str, **kwargs) -> Tuple[bool, Dict]:
        """编辑Bug（老 API）

        Args:
            bug_id: BugID
            **kwargs: 要修改的字段 (title, severity, pri, type, status, assignedTo, etc.)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.edit_bug("1", title="新标题", severity="2")
        """
        return self.old_request("POST", f"/bug-edit-{bug_id}.json", kwargs)

    def link_bug_story(self, bug_id: str, story_id: str) -> Tuple[bool, Dict]:
        """Bug关联需求（老 API）

        Args:
            bug_id: BugID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_bug_story("1", "5")
        """
        return self.old_request("POST", f"/bug-linkStory-{bug_id}-{story_id}.json")

    def unlink_bug_story(self, bug_id: str, story_id: str) -> Tuple[bool, Dict]:
        """取消Bug关联需求（老 API）

        Args:
            bug_id: BugID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_bug_story("1", "5")
        """
        return self.old_request("GET", f"/bug-unlinkStory-{bug_id}-{story_id}.json")

    def link_bug_task(self, bug_id: str, task_id: str) -> Tuple[bool, Dict]:
        """Bug关联任务（老 API）

        Args:
            bug_id: BugID
            task_id: 任务ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_bug_task("1", "10")
        """
        return self.old_request("POST", f"/bug-linkTask-{bug_id}-{task_id}.json")

    def unlink_bug_task(self, bug_id: str, task_id: str) -> Tuple[bool, Dict]:
        """取消Bug关联任务（老 API）

        Args:
            bug_id: BugID
            task_id: 任务ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_bug_task("1", "10")
        """
        return self.old_request("GET", f"/bug-unlinkTask-{bug_id}-{task_id}.json")

    def get_bug_statistics(
        self, product_id: str, branch: str = "0"
    ) -> Tuple[bool, Dict]:
        """获取Bug统计信息（老 API）

        Args:
            product_id: 产品ID
            branch: 分支ID，默认 "0"

        Returns:
            (success, statistics) Bug统计信息

        Example:
            >>> success, stats = client.get_bug_statistics("1")
            >>> print(f"总Bug数: {stats['total']}, 未解决: {stats['active']}")
        """
        success, result = self.old_request(
            "GET", f"/bug-statistic-{product_id}-{branch}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data
        return False, {}

    def add_bug_comment(self, bug_id: str, comment: str) -> Tuple[bool, Dict]:
        """添加Bug评论（老 API）

        Args:
            bug_id: BugID
            comment: 评论内容

        Returns:
            (success, result)

        Example:
            >>> success, result = client.add_bug_comment("1", "这是一个测试评论")
        """
        return self.old_request(
            "POST", f"/bug-addComment-{bug_id}.json", {"comment": comment}
        )

