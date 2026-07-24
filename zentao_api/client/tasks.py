from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any


class TasksMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 任务模块补充方法 ====================

    def edit_task(self, task_id: str, **kwargs) -> Tuple[bool, Dict]:
        """编辑任务（老 API）

        Args:
            task_id: 任务ID
            **kwargs: 要修改的字段 (name, type, pri, estimate, left, assignedTo, status, etc.)

        Returns:
            (success, result)

        Example:
            >>> success, result = client.edit_task("10", name="新任务名", pri="2")
        """
        return self.old_request("POST", f"/task-edit-{task_id}.json", kwargs)

    def move_task(self, task_id: str, project_id: str) -> Tuple[bool, Dict]:
        """移动任务到其他项目（老 API）

        Args:
            task_id: 任务ID
            project_id: 目标项目ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.move_task("10", "2")
        """
        return self.old_request("POST", f"/task-move-{task_id}-{project_id}.json")

    def copy_task(self, task_id: str, project_id: str = None) -> Tuple[bool, Dict]:
        """复制任务（老 API）

        Args:
            task_id: 任务ID
            project_id: 目标项目ID（可选，不传则复制到当前项目）

        Returns:
            (success, result)

        Example:
            >>> success, result = client.copy_task("10", "2")
        """
        if project_id:
            return self.old_request("POST", f"/task-copy-{task_id}-{project_id}.json")
        return self.old_request("POST", f"/task-copy-{task_id}.json")

    def get_task_subtasks(self, task_id: str) -> Tuple[bool, List[Dict]]:
        """获取任务的子任务列表（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, subtasks) 子任务列表

        Example:
            >>> success, subtasks = client.get_task_subtasks("10")
            >>> for task in subtasks:
            ...     print(f"[{task['id']}] {task['name']}")
        """
        return True, self._data(f"/task-viewSubtasks-{task_id}.json", "children")

    def link_task_story(self, task_id: str, story_id: str) -> Tuple[bool, Dict]:
        """任务关联需求（老 API）

        Args:
            task_id: 任务ID
            story_id: 需求ID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_task_story("10", "5")
        """
        return self.old_request("POST", f"/task-linkStory-{task_id}-{story_id}.json")

    def link_task_bug(self, task_id: str, bug_id: str) -> Tuple[bool, Dict]:
        """任务关联Bug（老 API）

        Args:
            task_id: 任务ID
            bug_id: BugID

        Returns:
            (success, result)

        Example:
            >>> success, result = client.link_task_bug("10", "3")
        """
        return self.old_request("POST", f"/task-linkBug-{task_id}-{bug_id}.json")

    def get_task_history(self, task_id: str) -> Tuple[bool, List[Dict]]:
        """获取任务历史记录（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, history) 历史记录列表

        Example:
            >>> success, history = client.get_task_history("10")
            >>> for record in history:
            ...     print(f"{record['date']}: {record['action']}")
        """
        return True, self._data(f"/task-history-{task_id}.json", "history")

