from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class BuildsMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 版本模块补充方法 ====================

    def create_build(
        self,
        project_id: str,
        name: str,
        product_id: str = "0",
        build: str = "",
        desc: str = "",
    ) -> Tuple[bool, Dict]:
        """创建版本（老 API）

        Args:
            project_id: 项目ID
            name: 版本名称
            product_id: 产品ID，默认 "0"
            build: 版本号
            desc: 版本描述

        Returns:
            (success, result)

        Example:
            >>> success, result = client.create_build(
            ...     project_id="1",
            ...     name="Sprint1 Build",
            ...     product_id="1",
            ...     build="1.0.0"
            ... )
        """
        data = {
            "project": project_id,
            "name": name,
        }
        if product_id:
            data["product"] = product_id
        if build:
            data["build"] = build
        if desc:
            data["desc"] = desc

        return self.old_request(
            "POST", f"/build-create-{project_id}-{product_id}.json", data
        )

    def edit_build(self, build_id: str, **kwargs) -> Tuple[bool, Dict]:
        """编辑版本（老 API）

        Args:
            build_id: 版本ID
            **kwargs: 要修改的字段 (name, build, desc, etc.)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.edit_build("1", name="New Build Name")
        """
        return self.old_request("POST", f"/build-edit-{build_id}.json", kwargs)

    def get_build(self, build_id: str) -> Tuple[bool, Dict]:
        """获取版本详情（老 API）

        Args:
            build_id: 版本ID

        Returns:
            (success, build_info) 版本详情

        Example:
            >>> success, build = client.get_build("1")
            >>> print(f"版本名: {build['name']}")
        """
        success, result = self.old_request("GET", f"/build-view-{build_id}.json")
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("build", {})
        return False, {}

    def delete_build(self, build_id: str) -> Tuple[bool, Dict]:
        """删除版本（老 API）

        Args:
            build_id: 版本ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.delete_build("1")
        """
        return self.old_request("GET", f"/build-delete-{build_id}-yes.json")

    def link_build_story(
        self, build_id: str, story_ids: List[str]
    ) -> Tuple[bool, Dict]:
        """版本关联需求（老 API）

        Args:
            build_id: 版本ID
            story_ids: 需求ID列表

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_build_story("1", ["5", "6"])
        """
        data = {}
        for i, story_id in enumerate(story_ids):
            data[f"stories[{i}]"] = story_id

        return self.old_request("POST", f"/build-linkStory-{build_id}.json", data)

    def unlink_build_story(self, build_id: str, story_id: str) -> Tuple[bool, Dict]:
        """取消版本关联需求（老 API）

        Args:
            build_id: 版本ID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_build_story("1", "5")
        """
        return self.old_request("GET", f"/build-unlinkStory-{story_id}-yes.json")

    def link_build_bug(self, build_id: str, bug_ids: List[str]) -> Tuple[bool, Dict]:
        """版本关联Bug（老 API）

        Args:
            build_id: 版本ID
            bug_ids: BugID列表

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_build_bug("1", ["10", "11"])
        """
        data = {}
        for i, bug_id in enumerate(bug_ids):
            data[f"bugs[{i}]"] = bug_id

        return self.old_request("POST", f"/build-linkBug-{build_id}.json", data)

    def unlink_build_bug(self, build_id: str, bug_id: str) -> Tuple[bool, Dict]:
        """取消版本关联Bug（老 API）

        Args:
            build_id: 版本ID
            bug_id: BugID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_build_bug("1", "10")
        """
        return self.old_request("GET", f"/build-unlinkBug-{build_id}-{bug_id}.json")

