from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class StoriesMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 需求相关方法 ====================

    def get_story(self, story_id: str) -> Tuple[bool, Dict]:
        """获取需求详情（老 API）

        Args:
            story_id: 需求ID

        Returns:
            (success, story_info) 需求详情

        Example:
            >>> success, story = client.get_story("1")
            >>> print(f"需求标题: {story['title']}")
        """
        return True, self._data_dict(f"/story-view-{story_id}.json", "story")

    def create_story(
        self,
        product_id: str,
        title: str,
        module: str = "0",
        plan: str = "0",
        execution_id: str = "0",
        branch: str = "0",
        **kwargs,
    ) -> Tuple[bool, Dict]:
        """创建需求（老 API）

        Args:
            product_id: 产品ID
            title: 需求标题
            module: 模块ID，默认 "0"
            plan: 计划ID，默认 "0"
            execution_id: 执行/项目ID，默认 "0"
            branch: 分支ID，默认 "0"
            **kwargs: 其他参数:
                - source: 需求来源
                - pri: 优先级 (0-4)
                - estimate: 预计工时
                - spec: 需求描述
                - verify: 验收标准
                - assignedTo: 指派给
                - reviewer: 评审人

        Returns:
            (success, result)

        Example:
            >>> success, result = client.create_story(
            ...     product_id="1",
            ...     title="新需求",
            ...     pri="3",
            ...     spec="需求描述"
            ... )
        """
        data = {
            "product": product_id,
            "title": title,
        }
        # ponytail: ZenTao's old API rejects module=0 / plan=0 in the POST
        # body (the "0" sentinel is OK in the URL path, where it's a positional
        # placeholder, but the body has a strict schema). Only emit these
        # fields when the caller supplied a real ID.
        if module and module != "0":
            data["module"] = module
        if plan and plan != "0":
            data["plan"] = plan
        data.update(kwargs)

        # URL: /story-create-{product}-{module}-{story}-{plan}-{execution}-{branch}-{module}-{type}.json
        return self.old_request(
            "POST",
            f"/story-create-{product_id}-{module}-0-{plan}-{execution_id}-{branch}-{module}-0-story.json",
            data,
        )

    def edit_story(self, story_id: str, **kwargs) -> Tuple[bool, Dict]:
        """编辑需求（老 API）

        Args:
            story_id: 需求ID
            **kwargs: 要修改的字段

        Returns:
            (success, result)

        Example:
            >>> success, result = client.edit_story("1", title="新标题", pri="2")
        """
        return self.old_request("POST", f"/story-edit-{story_id}.json", kwargs)

    def close_story(self, story_id: str) -> Tuple[bool, Dict]:
        """关闭需求（老 API）

        Args:
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.close_story("1")
        """
        return self.old_request("POST", f"/story-close-{story_id}.json")

    def activate_story(self, story_id: str) -> Tuple[bool, Dict]:
        """激活需求（老 API）

        Args:
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.activate_story("1")
        """
        return self.old_request("POST", f"/story-activate-{story_id}.json")

    def delete_story(self, story_id: str) -> Tuple[bool, Dict]:
        """删除需求（老 API）

        Args:
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.delete_story("1")
        """
        return self.old_request("GET", f"/story-delete-{story_id}-yes.json")


    # ==================== 需求模块补充方法 ====================

    def change_story(self, story_id: str, **kwargs) -> Tuple[bool, Dict]:
        """变更需求（老 API）

        Args:
            story_id: 需求ID
            **kwargs: 变更参数 (title, spec, verify, etc.)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.change_story("1", title="新标题", spec="新描述")
        """
        return self.old_request("POST", f"/story-change-{story_id}.json", kwargs)

    def review_story(
        self, story_id: str, result: str, comment: str = ""
    ) -> Tuple[bool, Dict]:
        """评审需求（老 API）

        Args:
            story_id: 需求ID
            result: 评审结果 (pass, revert, clarify, reject)
            comment: 评审意见

        Returns:
            (success, result)

        Example:
            >>> success, result = client.review_story("1", "pass", "评审通过")
        """
        data = {"result": result}
        if comment:
            data["comment"] = comment
        return self.old_request("POST", f"/story-review-{story_id}.json", data)

    def get_story_tasks(
        self, story_id: str, project_id: str = "0"
    ) -> Tuple[bool, List[Dict]]:
        """获取需求关联的任务（老 API）

        Args:
            story_id: 需求ID
            project_id: 项目ID，默认 "0" 获取所有项目

        Returns:
            (success, tasks) 任务列表

        Example:
            >>> success, tasks = client.get_story_tasks("1")
            >>> for task in tasks:
            ...     print(f"[{task['id']}] {task['name']}")
        """
        success, result = self.old_request(
            "GET", f"/story-tasks-{story_id}-{project_id}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("tasks", [])
        return False, []

    def get_story_bugs(self, story_id: str) -> Tuple[bool, List[Dict]]:
        """获取需求关联的Bug（老 API）

        Args:
            story_id: 需求ID

        Returns:
            (success, bugs) Bug列表

        Example:
            >>> success, bugs = client.get_story_bugs("1")
            >>> for bug in bugs:
            ...     print(f"[{bug['id']}] {bug['title']}")
        """
        return True, self._data(f"/story-bugs-{story_id}.json", "bugs")

    def get_story_cases(self, story_id: str) -> Tuple[bool, List[Dict]]:
        """获取需求关联的测试用例（老 API）

        Args:
            story_id: 需求ID

        Returns:
            (success, cases) 测试用例列表

        Example:
            >>> success, cases = client.get_story_cases("1")
            >>> for case in cases:
            ...     print(f"[{case['id']}] {case['title']}")
        """
        return True, self._data(f"/story-cases-{story_id}.json", "cases")

    def link_story_project(self, story_id: str, project_id: str) -> Tuple[bool, Dict]:
        """需求关联项目（老 API）

        Args:
            story_id: 需求ID
            project_id: 项目ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_story_project("1", "2")
        """
        return self.old_request(
            "POST", f"/story-linkProject-{story_id}-{project_id}.json"
        )

    def unlink_story_project(self, story_id: str, project_id: str) -> Tuple[bool, Dict]:
        """取消需求关联项目（老 API）

        Args:
            story_id: 需求ID
            project_id: 项目ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_story_project("1", "2")
        """
        return self.old_request(
            "GET", f"/story-unlinkProject-{story_id}-{project_id}.json"
        )

