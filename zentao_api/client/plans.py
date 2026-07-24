from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class PlansMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 计划相关方法 ====================

    def get_plans(self, product_id: str) -> Tuple[bool, List[Dict]]:
        """获取产品计划列表（老 API）

        Args:
            product_id: 产品ID

        Returns:
            (success, plans) 计划列表

        Example:
            >>> success, plans = client.get_plans("1")
            >>> for plan in plans:
            ...     print(f"[{plan['id']}] {plan['title']}")
        """
        success, result = self.old_request(
            "GET", f"/productplan-browse-{product_id}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            return True, data.get("plans", [])
        return False, []

    def create_plan(
        self,
        product_id: str,
        title: str,
        begin: str = "",
        end: str = "",
        desc: str = "",
    ) -> Tuple[bool, Dict]:
        """创建产品计划（老 API）

        Args:
            product_id: 产品ID
            title: 计划标题
            begin: 开始日期 (YYYY-MM-DD)
            end: 结束日期 (YYYY-MM-DD)
            desc: 计划描述

        Returns:
            (success, result)

        Example:
            >>> success, result = client.create_plan(
            ...     product_id="1",
            ...     title="1.0版本",
            ...     begin="2026-03-01",
            ...     end="2026-03-31"
            ... )
        """
        data = {
            "product": product_id,
            "title": title,
            "begin": begin,
            "end": end,
            "desc": desc,
        }
        return self.old_request("POST", f"/productplan-create-{product_id}.json", data)

    def delete_plan(self, plan_id: str) -> Tuple[bool, Dict]:
        """删除产品计划（老 API）

        Args:
            plan_id: 计划ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.delete_plan("1")
        """
        return self.old_request("GET", f"/productplan-delete-{plan_id}-yes.json")


    # ==================== 计划模块补充方法 ====================

    def get_plan(self, plan_id: str) -> Tuple[bool, Dict]:
        """获取计划详情（老 API）

        Args:
            plan_id: 计划ID

        Returns:
            (success, plan_info) 计划详情

        Example:
            >>> success, plan = client.get_plan("1")
            >>> print(f"计划名: {plan['title']}")
        """
        return True, self._data_dict(f"/productplan-view-{plan_id}.json", "plan")

    def edit_plan(self, plan_id: str, **kwargs) -> Tuple[bool, Dict]:
        """编辑计划（老 API）

        Args:
            plan_id: 计划ID
            **kwargs: 要修改的字段 (title, begin, end, desc, etc.)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.edit_plan("1", title="新计划名", begin="2026-04-01")
        """
        return self.old_request("POST", f"/productplan-edit-{plan_id}.json", kwargs)

    def link_plan_story(self, plan_id: str, story_ids: List[str]) -> Tuple[bool, Dict]:
        """计划关联需求（老 API）

        Args:
            plan_id: 计划ID
            story_ids: 需求ID列表

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_plan_story("1", ["5", "6", "7"])
        """
        data = {}
        for i, story_id in enumerate(story_ids):
            data[f"stories[{i}]"] = story_id

        return self.old_request("POST", f"/productplan-linkStory-{plan_id}.json", data)

    def unlink_plan_story(self, plan_id: str, story_id: str) -> Tuple[bool, Dict]:
        """取消计划关联需求（老 API）

        Args:
            plan_id: 计划ID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.unlink_plan_story("1", "5")
        """
        return self.old_request(
            "GET", f"/productplan-unlinkStory-{plan_id}-{story_id}.json"
        )
