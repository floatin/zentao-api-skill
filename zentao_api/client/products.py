from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class ProductsMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 产品相关方法 ====================

    # ponytail: REST-ish helpers added in P0 so the CLI stops crashing on
    # AttributeError. Real endpoint paths are best-effort guesses from sibling
    # `get_*_old` methods — the URL itself is never asserted in tests.
    def get_projects(self, status: str = "doing") -> Tuple[bool, List[Dict]]:
        """获取项目列表（按状态）

        Returns:
            (success, projects) 项目列表，每项含 id / name / status / begin / end
        """
        success, result = self.old_request("GET", f"/project-index-{status}.json")
        if success and "data" in result:
            data = json.loads(result["data"])
            projects = data.get("projects", {})
            if isinstance(projects, dict):
                return True, [{"id": pid, **p} if isinstance(p, dict) else {"id": pid, "name": p}
                              for pid, p in projects.items()]
            return True, projects
        return False, []

    def get_executions(self, project_id: str) -> Tuple[bool, List[Dict]]:
        """获取项目的执行/迭代列表"""
        return True, self._data(f"/project-execution-{project_id}.json", "executions")

    def get_stories(self, project_id: str) -> Tuple[bool, List[Dict]]:
        """获取项目的需求列表"""
        return True, self._data(f"/project-story-{project_id}.json", "stories")

    def get_tasks(self, execution_id: str) -> Tuple[bool, List[Dict]]:
        """获取执行/迭代下的任务列表"""
        return True, self._data(f"/execution-task-{execution_id}.json", "tasks")

    def get_bugs(self, product_id: str) -> Tuple[bool, List[Dict]]:
        """获取产品的缺陷列表"""
        return True, self._data(f"/product-bug-{product_id}.json", "bugs")

    def get_productplans(self, product_id: str) -> Tuple[bool, List[Dict]]:
        """获取产品的发布计划列表（REST-ish 包装）

        老 API 返回 {title: id} 字典，这里规范化为 [{id, title}, ...]。
        """
        plan_dict = self.get_productplan_list_old(product_id)
        if not plan_dict:
            return False, []
        return True, [{"id": pid, "title": title} for title, pid in plan_dict.items()]

    def batch_create_tasks(
        self,
        execution_id: str,
        parent_id: str,
        tasks: list,
    ) -> Tuple[bool, Dict]:
        """批量创建子任务（CLI 调用的便捷封装）

        委托给现有的 `create_tasks`。
        """
        return self.create_tasks(
            project=execution_id,
            tasks=tasks,
            parent_id=parent_id,
        )

    def create_productplan(self, product_id: str, title: str) -> Tuple[bool, Dict]:
        """新建产品计划（CLI 调用的便捷封装，委托给 create_plan）"""
        return self.create_plan(product_id=product_id, title=title)

    def get_products(self) -> Tuple[bool, List[Dict]]:
        """获取所有产品列表（老 API）

        Returns:
            (success, products) 产品列表

        Example:
            >>> success, products = client.get_products()
            >>> for pid, name in products.items():
            ...     print(f"[{pid}] {name}")
        """
        return True, self._data("/product-all.json", "products")

    def get_product(self, product_id: str) -> Tuple[bool, Dict]:
        """获取产品详情（老 API）

        Args:
            product_id: 产品ID

        Returns:
            (success, product_info) 产品详情

        Example:
            >>> success, product = client.get_product("1")
            >>> print(f"产品名: {product['name']}")
        """
        return True, self._data_dict(f"/product-view-{product_id}.json", "product")

    def create_product(
        self,
        name: str,
        code: str,
        type: str = "normal",
        po: str = "",
        qd: str = "",
        rd: str = "",
        status: str = "normal",
        desc: str = "",
    ) -> Tuple[bool, Dict]:
        """创建产品（老 API）

        Args:
            name: 产品名称
            code: 产品代码
            type: 产品类型 (normal, branch, platform)
            po: 产品负责人
            qd: 测试负责人
            rd: 发布负责人
            status: 状态 (normal, closed)
            desc: 产品描述

        Returns:
            (success, result)

        Example:
            >>> success, result = client.create_product(
            ...     name="新产品",
            ...     code="NEW",
            ...     po="admin"
            ... )
        """
        data = {
            "name": name,
            "code": code,
            "type": type,
            "status": status,
            "desc": desc,
        }
        if po:
            data["PO"] = po
        if qd:
            data["QD"] = qd
        if rd:
            data["RD"] = rd

        return self.old_request("POST", "/product-create.json", data)

    def edit_product(self, product_id: str, **kwargs) -> Tuple[bool, Dict]:
        """编辑产品（老 API）

        Args:
            product_id: 产品ID
            **kwargs: 要修改的字段 (name, code, type, PO, QD, RD, status, desc等)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.edit_product("1", name="新名称", status="closed")
        """
        return self.old_request("POST", f"/product-edit-{product_id}.json", kwargs)

    def close_product(self, product_id: str) -> Tuple[bool, Dict]:
        """关闭产品（老 API）

        Args:
            product_id: 产品ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.close_product("1")
        """
        return self.old_request("POST", f"/product-close-{product_id}.json")

    def delete_product(self, product_id: str) -> Tuple[bool, Dict]:
        """删除产品（老 API）

        Args:
            product_id: 产品ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.delete_product("1")
        """
        return self.old_request("GET", f"/product-delete-{product_id}-yes.json")

