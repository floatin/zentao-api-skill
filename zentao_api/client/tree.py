"""Tree / Module CRUD mixin."""
from __future__ import annotations

from typing import Dict, List, Tuple


class TreeMixin:
    """Module (tree node) read + write operations."""

    # ------------------------------------------------------------------ read

    def list_modules(
        self,
        product_id: str,
        view_type: str = "story",
    ) -> Tuple[bool, List[Dict]]:
        """列出产品下的模块。

        Args:
            product_id: 产品 ID
            view_type: 视图类型 ``"story"`` / ``"bug"`` / ``"task"``

        Returns:
            ``(success, [{id, name, parent, type, ...}, ...])``
        """
        inner = self._data_unwrap(f"/tree-browse-{product_id}-{view_type}.json")
        sons = inner.get("sons") or []
        return True, sons

    # ----------------------------------------------------------------- write

    def create_module(
        self,
        product_id: str,
        name: str,
        view_type: str = "story",
        parent: str = "0",
    ) -> Tuple[bool, Dict]:
        """新建模块。

        Args:
            product_id: 所属产品 ID
            name: 模块名称
            view_type: ``"story"`` / ``"bug"`` / ``"task"``
            parent: 父模块 ID，``"0"`` 为根级
        """
        return self.old_request(
            "POST",
            f"/tree-create-{product_id}-{view_type}.json",
            {"type": view_type, "parent": parent, "name": name},
        )

    def edit_module(
        self,
        module_id: str,
        name: str,
        view_type: str = "story",
    ) -> Tuple[bool, Dict]:
        """编辑模块名称。"""
        return self.old_request(
            "POST",
            f"/tree-update-{module_id}.json",
            {"type": view_type, "name": name},
        )

    def delete_module(
        self,
        module_id: str,
        view_type: str = "story",
    ) -> Tuple[bool, Dict]:
        """删除模块。"""
        return self.old_request(
            "GET",
            f"/tree-delete-{module_id}-{view_type}-yes.json",
        )
