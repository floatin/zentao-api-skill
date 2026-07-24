from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any


class ReleasesMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 发布相关方法 ====================

    def get_releases(self, product_id: str) -> Tuple[bool, List[Dict]]:
        """获取产品发布列表（老 API）

        Args:
            product_id: 产品ID

        Returns:
            (success, releases) 发布列表

        Example:
            >>> success, releases = client.get_releases("1")
            >>> for release in releases:
            ...     print(f"[{release['id']}] {release['name']}")
        """
        return True, self._data(f"/release-browse-{product_id}.json", "releases")


    # ==================== 发布模块补充方法 ====================

    def create_release(
        self,
        product_id: str,
        name: str,
        branch: str = "0",
        build: str = "",
        date: str = "",
        desc: str = "",
    ) -> Tuple[bool, Dict]:
        """创建发布（老 API）

        Args:
            product_id: 产品ID
            name: 发布名称
            branch: 分支ID，默认 "0"
            build: 版本ID
            date: 发布日期 (YYYY-MM-DD)
            desc: 发布描述

        Returns:
            (success, result)

        Example:
            >>> success, result = client.create_release(
            ...     product_id="1",
            ...     name="V1.0",
            ...     build="1",
            ...     date="2026-04-01"
            ... )
        """
        data = {
            "product": product_id,
            "name": name,
            "branch": branch,
        }
        if build:
            data["build"] = build
        if date:
            data["date"] = date
        if desc:
            data["desc"] = desc

        return self.old_request(
            "POST", f"/release-create-{product_id}-{branch}.json", data
        )

    def edit_release(self, release_id: str, **kwargs) -> Tuple[bool, Dict]:
        """编辑发布（老 API）

        Args:
            release_id: 发布ID
            **kwargs: 要修改的字段 (name, date, build, desc, status, etc.)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.edit_release("1", name="V1.0.1", status="released")
        """
        return self.old_request("POST", f"/release-edit-{release_id}.json", kwargs)

    def get_release(self, release_id: str) -> Tuple[bool, Dict]:
        """获取发布详情（老 API）

        Args:
            release_id: 发布ID

        Returns:
            (success, release_info) 发布详情

        Example:
            >>> success, release = client.get_release("1")
            >>> print(f"发布名: {release['name']}")
        """
        return True, self._data_dict(f"/release-view-{release_id}.json", "release")

    def delete_release(self, release_id: str) -> Tuple[bool, Dict]:
        """删除发布（老 API）

        Args:
            release_id: 发布ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.delete_release("1")
        """
        return self.old_request("GET", f"/release-delete-{release_id}-yes.json")

    def link_release_story(
        self, release_id: str, story_ids: List[str]
    ) -> Tuple[bool, Dict]:
        """发布关联需求（老 API）

        Args:
            release_id: 发布ID
            story_ids: 需求ID列表

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_release_story("1", ["5", "6", "7"])
        """
        data = {}
        for i, story_id in enumerate(story_ids):
            data[f"stories[{i}]"] = story_id

        return self.old_request("POST", f"/release-linkStory-{release_id}.json", data)

    def unlink_release_story(self, release_id: str, story_id: str) -> Tuple[bool, Dict]:
        """取消发布关联需求（老 API）

        Args:
            release_id: 发布ID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_release_story("1", "5")
        """
        return self.old_request(
            "GET", f"/release-unlinkStory-{release_id}-{story_id}.json"
        )

    def link_release_bug(
        self, release_id: str, bug_ids: List[str], bug_type: str = "bug"
    ) -> Tuple[bool, Dict]:
        """发布关联Bug（老 API）

        Args:
            release_id: 发布ID
            bug_ids: BugID列表
            bug_type: Bug类型 (bug, leftBug)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_release_bug("1", ["10", "11"])
        """
        data = {}
        for i, bug_id in enumerate(bug_ids):
            data[f"bugs[{i}]"] = bug_id

        return self.old_request(
            "POST", f"/release-linkBug-{release_id}-all-all-bug.json", data
        )

    def unlink_release_bug(
        self, release_id: str, bug_id: str, bug_type: str = "bug"
    ) -> Tuple[bool, Dict]:
        """取消发布关联Bug（老 API）

        Args:
            release_id: 发布ID
            bug_id: BugID
            bug_type: Bug类型 (bug, leftBug)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_release_bug("1", "10")
        """
        return self.old_request(
            "GET", f"/release-unlinkBug-{release_id}-{bug_id}-{bug_type}.json"
        )

