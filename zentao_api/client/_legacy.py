from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class LegacyMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 老 API 方法 ====================

    def get_product_list_old(self) -> Dict[str, str]:
        """获取产品列表（老 API）- 返回 {产品名：ID}"""
        data = self._data_unwrap("/product-index-no.json")
        products = data.get("products", {})
        # ponytail: server returns either {id: name} (dict) or [{id, name}] (list).
        # Handle both — the second form is rare but documented in older Zentao.
        if isinstance(products, dict):
            return {v: str(k) for k, v in products.items() if isinstance(v, str)}
        return {p["name"]: str(p["id"]) for p in products}

    def get_project_list_old(self, status: str = "all") -> Dict[str, str]:
        """获取项目列表（老 API）

        Returns:
            {项目ID: 项目名} 例如 {'1': 'config', '2': 'project2'}
        """
        return self._data_unwrap("/project-browse-all.json").get("projects", {})

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
        plans = self._data_unwrap(
            f"/productplan-browse-{product_id}-{branch}-all.json"
        ).get("productPlansNum", {})
        return {v["title"]: v["id"] for k, v in plans.items()}

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
        return self._data_unwrap(
            f"/project-task-{project_id}-{status}-id_desc-{module_id}-{limit}-{page}.json"
        ).get("tasks", {})

    def get_task_detail(self, task_id: str) -> Tuple[bool, Dict]:
        """获取单个任务详情（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, task_info) task_info 包含 id, name, status, parent, assignedTo 等字段

        Note:
            此方法可获取任务的真实状态（包括已取消状态），适用于验证操作结果
        """
        # ponytail: 保留 (success, dict) 双元素返回，因为外部大量代码依赖这个
        # 包装协议（_change_task_status 在 BaseClient 内部就根据 success 决定
        # 是否继续）。仅在服务端真的返回 success 时才返回 True。
        success, _ = self.old_request("GET", f"/task-view-{task_id}.json")
        if not success:
            return False, {}
        return True, self._data_dict(f"/task-view-{task_id}.json", "task")

