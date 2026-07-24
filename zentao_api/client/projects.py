from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class ProjectsMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 项目管理方法 ====================

    def create_project(
        self,
        name: str,
        begin: str,
        end: str,
        code: str = "",
        days: str = "",
        products: List[str] = None,
        plans: List[str] = None,
        desc: str = "",
        **kwargs,
    ) -> Tuple[bool, Dict]:
        """创建项目（老 API）

        Args:
            name: 项目名称
            begin: 开始日期 (YYYY-MM-DD)
            end: 结束日期 (YYYY-MM-DD)
            code: 项目代号
            days: 可用工时天数
            products: 关联产品ID列表
            plans: 关联计划ID列表（需与products一一对应）
            desc: 项目描述
            **kwargs: 其他参数 (acl, whitelist, team, etc.)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.create_project(
            ...     name="V1.0开发项目",
            ...     begin="2026-04-01",
            ...     end="2026-04-30",
            ...     code="V1",
            ...     days="22",
            ...     products=["1"],
            ...     plans=["1"]
            ... )
        """
        data = {
            "name": name,
            "begin": begin,
            "end": end,
        }
        if code:
            data["code"] = code
        if days:
            data["days"] = days
        if desc:
            data["desc"] = desc

        # 关联产品和计划
        if products:
            for i, product_id in enumerate(products):
                data[f"products[{i}]"] = product_id
                if plans and i < len(plans):
                    data[f"plans[{i}]"] = plans[i]

        data.update(kwargs)

        return self.old_request("POST", "/project-create.json", data)

    def get_project(self, project_id: str) -> Tuple[bool, Dict]:
        """获取项目详情（老 API）

        Args:
            project_id: 项目ID

        Returns:
            (success, project)

        Example:
            >>> success, project = client.get_project("1")
            >>> print(project['name'])
        """
        success, result = self.old_request("GET", f"/project-view-{project_id}.json")
        if success and "data" in result:
            data = result["data"]
            if isinstance(data, str):
                data = json.loads(data)
            return True, data.get("project", data)
        return success, result

    def start_project(self, project_id: str) -> Tuple[bool, Dict]:
        """启动项目（老 API）

        Args:
            project_id: 项目ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.start_project("1")
        """
        return self.old_request("GET", f"/project-start-{project_id}.json")

    def close_project(self, project_id: str) -> Tuple[bool, Dict]:
        """关闭项目（老 API）

        Args:
            project_id: 项目ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.close_project("1")
        """
        return self.old_request("GET", f"/project-close-{project_id}.json")


    # ==================== 项目模块补充方法 ====================

    def edit_project(self, project_id: str, **kwargs) -> Tuple[bool, Dict]:
        """编辑项目（老 API）

        Args:
            project_id: 项目ID
            **kwargs: 要修改的字段 (name, code, begin, end, days, status, etc.)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.edit_project("1", name="新项目名", status="doing")
        """
        return self.old_request("POST", f"/project-edit-{project_id}.json", kwargs)

    def get_project_stories(
        self, project_id: str, order_by: str = "id_desc"
    ) -> Tuple[bool, List[Dict]]:
        """获取项目需求列表（老 API）

        Args:
            project_id: 项目ID
            order_by: 排序方式，默认 "id_desc"

        Returns:
            (success, stories) 需求列表

        Example:
            >>> success, stories = client.get_project_stories("1")
            >>> for story in stories:
            ...     print(f"[{story['id']}] {story['title']}")
        """
        success, result = self.old_request(
            "GET", f"/project-story-{project_id}-{order_by}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("stories", [])
        return False, []

    def manage_project_members(
        self, project_id: str, members: List[Dict]
    ) -> Tuple[bool, Dict]:
        """管理项目成员（老 API）

        Args:
            project_id: 项目ID
            members: 成员列表，每个成员包含:
                - account: 用户账号
                - role: 角色 (如 developer, tester, pm)
                - hours: 可用工时

        Returns:
            (success, result)

        Example:
            >>> members = [
            ...     {"account": "user1", "role": "developer", "hours": "8"},
            ...     {"account": "user2", "role": "tester", "hours": "8"}
            ... ]
            >>> success, result = client.manage_project_members("1", members)
        """
        data = {}
        for i, member in enumerate(members):
            data[f"accounts[{i}]"] = member.get("account", "")
            data[f"roles[{i}]"] = member.get("role", "developer")
            data[f"hours[{i}]"] = member.get("hours", "8")

        return self.old_request(
            "POST", f"/project-manageMembers-{project_id}.json", data
        )

    def link_project_story(self, project_id: str, story_id: str) -> Tuple[bool, Dict]:
        """项目关联需求（老 API）

        Args:
            project_id: 项目ID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_project_story("1", "5")
        """
        return self.old_request(
            "POST", f"/project-linkStory-{project_id}.json", {"story": story_id}
        )

    def unlink_project_story(self, project_id: str, story_id: str) -> Tuple[bool, Dict]:
        """取消项目关联需求（老 API）

        Args:
            project_id: 项目ID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_project_story("1", "5")
        """
        return self.old_request(
            "GET", f"/project-unlinkStory-{project_id}-{story_id}.json"
        )

    def get_project_team(self, project_id: str) -> Tuple[bool, List[Dict]]:
        """获取项目团队成员（老 API）

        Args:
            project_id: 项目ID

        Returns:
            (success, team) 团队成员列表

        Example:
            >>> success, team = client.get_project_team("1")
            >>> for member in team:
            ...     print(f"{member['account']}: {member['role']}")
        """
        success, result = self.old_request("GET", f"/project-team-{project_id}.json")
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("team", [])
        return False, []

    def get_project_dynamic(
        self, project_id: str, dynamic_type: str = "all"
    ) -> Tuple[bool, List[Dict]]:
        """获取项目动态（老 API）

        Args:
            project_id: 项目ID
            dynamic_type: 动态类型 (all, today, yesterday, thisweek, lastweek, thismonth, lastmonth)

        Returns:
            (success, dynamics) 动态列表

        Example:
            >>> success, dynamics = client.get_project_dynamic("1", "today")
            >>> for dynamic in dynamics:
            ...     print(f"{dynamic['date']}: {dynamic['action']}")
        """
        success, result = self.old_request(
            "GET", f"/project-dynamic-{project_id}-{dynamic_type}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("dynamics", [])
        return False, []

