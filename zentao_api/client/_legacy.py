from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class LegacyMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 老 API 方法 ====================

    def get_product_list_old(self) -> Dict[str, str]:
        """获取产品列表（老 API）- 返回 {产品名：ID}"""
        success, result = self.old_request("GET", "/product-index-no.json")
        if success and "data" in result:
            data = json.loads(result["data"])
            products = data.get("products", [])
            return {p["name"]: str(p["id"]) for p in products}
        return {}

    def get_project_list_old(self, status: str = "all") -> Dict[str, str]:
        """获取项目列表（老 API）

        Returns:
            {项目ID: 项目名} 例如 {'1': 'config', '2': 'project2'}
        """
        success, result = self.old_request("GET", "/project-browse-all.json")
        if success and "data" in result:
            data = json.loads(result["data"])
            projects = data.get("projects", {})
            return projects
        return {}

    def get_bug_list_old(self, product_id: str, branch: str = "0") -> List[Dict]:
        """获取缺陷列表（老 API）

        Args:
            product_id: 产品ID
            branch: 分支ID，默认 "0"

        Returns:
            Bug列表
        """
        success, result = self.old_request(
            "GET", f"/bug-browse-{product_id}-{branch}-all.json"
        )
        if success and "data" in result:
            return json.loads(result["data"])
        return []

    def get_productplan_list_old(
        self, product_id: str, branch: str = "0"
    ) -> Dict[str, str]:
        """获取发布计划列表（老 API）

        Args:
            product_id: 产品ID
            branch: 分支ID，默认 "0"

        Returns:
            {计划名：ID}
        """
        success, result = self.old_request(
            "GET", f"/productplan-browse-{product_id}-{branch}-all.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            plans = data.get("productPlansNum", {})
            return {v["title"]: v["id"] for k, v in plans.items()}
        return {}

    def get_project_tasks_old(
        self,
        project_id: str,
        status: str = "all",
        module_id: str = "0",
        limit: int = 2000,
        page: int = 1,
    ) -> Dict:
        """获取项目任务列表（老 API）

        Args:
            project_id: 项目ID
            status: 任务状态，默认 "all" 获取所有状态
            module_id: 模块ID，默认 "0" 获取所有模块
            limit: 每页数量，默认 2000
            page: 页码，默认 1

        Returns:
            任务字典 {任务ID: 任务信息}

        Note:
            已取消的任务可能不显示在列表中，请使用 get_task_detail 查询单个任务状态
        """
        success, result = self.old_request(
            "GET",
            f"/project-task-{project_id}-{status}-id_desc-{module_id}-{limit}-{page}.json",
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            tasks = data.get("tasks", {})
            return tasks
        return {}

    def get_task_detail(self, task_id: str) -> Tuple[bool, Dict]:
        """获取单个任务详情（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, task_info) task_info 包含 id, name, status, parent, assignedTo 等字段

        Note:
            此方法可获取任务的真实状态（包括已取消状态），适用于验证操作结果
        """
        success, result = self.old_request("GET", f"/task-view-{task_id}.json")
        if success and "data" in result:
            data = json.loads(result["data"])
            task = data.get("task", {})
            return True, task
        return False, {}

