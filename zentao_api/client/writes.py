from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json


class WritesMixin:
    """Mixin for ZenTaoClient."""
    # ==================== 写操作方法（需要确认）====================
    # ponytail: the live create_story lives further down (line ~1800) with the
    # generalised (product_id, title, **kwargs) signature. The earlier
    # positional form was overwritten by Python's last-defines-wins rule and
    # is now dead code — kept here as a marker.

    def create_subtasks(
        self,
        execution_id: str,
        parent_id: str,
        tasks: list,
        story_id: str = "0",
        module_id: str = "0",
    ) -> Tuple[bool, Dict]:
        """创建子任务（老 API）

        Args:
            execution_id: 执行/项目ID
            parent_id: 父任务ID
            tasks: 任务列表，每个任务包含 name, estimate, assignedTo 等
            story_id: 需求ID，默认 "0"
            module_id: 模块ID，默认 "0"

        Returns:
            (success, result)
        """
        # ponytail: was 124 lines of hand-rolled multipart. ``requests`` builds
        # the multipart body from a files dict; (None, value) makes it a regular
        # form field rather than a file upload.
        files: Dict[str, Any] = {}
        for i, task in enumerate(tasks):
            name = task.get("name", "")
            estimate = task.get("estimate", "")
            assigned_to = task.get("assignedTo", "admin")
            task_type = task.get("type", "devel")
            pri = task.get("pri", "3")

            if i == 0:
                files["module[0]"] = (None, "0")
                files["parent[0]"] = (None, parent_id)
                files["name[0]"] = (None, name)
                files["type[0]"] = (None, task_type)
                files["assignedTo[0]"] = (None, assigned_to)
                files["estimate[0]"] = (None, str(estimate))
                files["pri[0]"] = (None, str(pri))
            else:
                files[f"module[{i}]"] = (None, "0")
                files[f"parent[{i}]"] = (None, "ditto")
                files[f"story[{i}]"] = (None, "ditto")
                files[f"name[{i}]"] = (None, name)
                files[f"type[{i}]"] = (None, "ditto")
                files[f"assignedTo[{i}]"] = (None, "ditto")
                files[f"estimate[{i}]"] = (None, str(estimate))
                files[f"pri[{i}]"] = (None, "ditto")

        url = f"{self.old_api_base}/task-batchCreate-{execution_id}-{story_id}-{module_id}-{parent_id}.html"
        response = self.session.post(
            url, files=files, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {
                "message": "创建子任务成功",
                "status_code": response.status_code,
            }
        return False, {
            "message": f"创建失败: HTTP {response.status_code}",
            "status_code": response.status_code,
        }

    def _change_task_status(
        self,
        task_id: str,
        new_status: str,
        comment: str = "",
    ) -> Tuple[bool, Dict]:
        """共享状态变更后端。

        ``task-edit-{id}.json`` 需要任务现有字段全回传，只换 status。
        cancel_task / start_task 共用这个模式。
        """
        success, task = self.get_task_detail(task_id)
        if not success:
            return False, {"message": f"获取任务失败: {task}"}
        data = {
            "id": task_id,
            "parent": task.get("parent", "0"),
            "project": task.get("project", "0"),
            "module": task.get("module", "0"),
            "story": task.get("story", "0"),
            "name": task.get("name", ""),
            "type": task.get("type", "devel"),
            "pri": task.get("pri", "3"),
            "estimate": task.get("estimate", "0"),
            "left": task.get("left", "0"),
            "consumed": task.get("consumed", "0"),
            "assignedTo": task.get("assignedTo", "admin"),
            "status": new_status,
        }
        if comment:
            data["comment"] = comment
        return self.old_request("POST", f"/task-edit-{task_id}.json", data)

    def cancel_task(self, task_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """取消任务（老 API）

        Note:
            取消后任务状态变为 'cancel'，但可能不显示在项目任务列表中。
            建议使用 get_task_detail(task_id) 验证取消结果。

        Example:
            >>> success, result = client.cancel_task("6", "功能暂缓开发")
            >>> if success:
            >>>     ok, task = client.get_task_detail("6")
            >>>     print(f"任务状态: {task.get('status')}")  # cancel
        """
        return self._change_task_status(task_id, "cancel", comment)

    def delete_task(self, task_id: str) -> Tuple[bool, Dict]:
        """删除任务（老 API）

        Args:
            task_id: 任务ID

        Returns:
            (success, result)
        """
        return self.old_request("POST", f"/task-delete-{task_id}.json")

    def close_task(self, task_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """关闭任务（老 API）

        Args:
            task_id: 任务ID
            comment: 关闭备注（可选）

        Returns:
            (success, result)
            注意：即使返回 success=False（因为返回HTML），任务也可能已关闭。
            请使用 get_task_detail(task_id) 验证结果。

        Note:
            关闭后任务状态变为 'closed'。
            可直接关闭 wait 状态的任务，无需先完成。

        Example:
            >>> success, result = client.close_task("7", "已完成")
            >>> # 验证关闭结果
            >>> ok, task = client.get_task_detail("7")
            >>> print(f"任务状态: {task.get('status')}")  # 应为 'closed'
            >>> print(f"关闭人: {task.get('closedBy')}")
        """
        data = {}
        if comment:
            data["comment"] = comment
        return self.old_request("POST", f"/task-close-{task_id}.json", data=data)

    def start_task(self, task_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """开始任务（老 API）

        Note:
            开始后任务状态变为 'doing'。
            实际使用 task-edit 接口修改状态，因为 task-start 接口会直接完成任务。

        Example:
            >>> success, result = client.start_task("10", "开始开发")
            >>> # 验证开始结果
            >>> ok, task = client.get_task_detail("10")
            >>> print(f"任务状态: {task.get('status')}")  # doing
        """
        return self._change_task_status(task_id, "doing", comment)

    def record_estimate(
        self, task_id: str, records: List[Dict[str, str]]
    ) -> Tuple[bool, Dict]:
        """记录任务工时（老 API）

        Args:
            task_id: 任务ID
            records: 工时记录列表，每条记录包含:
                - date: 日期 (YYYY-MM-DD)
                - consumed: 本次消耗工时
                - left: 剩余工时
                - work: 工作内容

        Returns:
            (success, result) 注意：返回 HTML 页面，解析会失败。
            请使用 get_task_detail(task_id) 验证 consumed 和 left 是否更新。

        Note:
            - 索引从 1 开始，不是 0
            - 必须使用 .html?onlybody=yes 端点
            - 可以一次提交多条工时记录

        Example:
            >>> from datetime import datetime
            >>> today = datetime.now().strftime("%Y-%m-%d")
            >>> records = [
            ...     {"date": today, "consumed": "2", "left": "6", "work": "开发功能A"},
            ...     {"date": today, "consumed": "1", "left": "5", "work": "测试"}
            ... ]
            >>> success, result = client.record_estimate("13", records)
            >>> ok, task = client.get_task_detail("13")
            >>> print(f"消耗: {task['consumed']}, 剩余: {task['left']}")
        """
        data = {}
        for i, record in enumerate(records, start=1):
            data[f"id[{i}]"] = record.get("id", "")
            data[f"dates[{i}]"] = record.get("date", "")
            data[f"consumed[{i}]"] = record.get("consumed", "")
            data[f"left[{i}]"] = record.get("left", "")
            data[f"work[{i}]"] = record.get("work", "")

        url = f"{self.old_api_base}/task-recordEstimate-{task_id}.html?onlybody=yes"
        response = self.session.post(
            url, data=data, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {
                "message": "记录工时成功",
                "status_code": response.status_code,
            }
        else:
            return False, {
                "message": f"记录失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def get_estimate(self, estimate_id: str) -> Tuple[bool, Dict]:
        """获取工时记录详情（老 API）

        Args:
            estimate_id: 工时记录ID

        Returns:
            (success, estimate_info)
        """
        success, result = self.old_request(
            "GET", f"/task-editEstimate-{estimate_id}.json"
        )
        if success and "data" in result:
            data = json.loads(result["data"])
            estimate = data.get("estimate", {})
            return True, estimate
        return False, {}

    def edit_estimate(
        self, estimate_id: str, consumed: str = None, left: str = None, work: str = None
    ) -> Tuple[bool, Dict]:
        """编辑工时记录（老 API）

        Args:
            estimate_id: 工时记录ID
            consumed: 消耗工时（可选）
            left: 剩余工时（可选）
            work: 工作内容（可选）

        Returns:
            (success, result) 注意：返回 HTML 页面。
            请使用 get_estimate(estimate_id) 验证修改结果。

        Example:
            >>> success, result = client.edit_estimate("1", consumed="5", left="3", work="修改记录")
            >>> ok, estimate = client.get_estimate("1")
            >>> print(f"消耗: {estimate['consumed']}, 剩余: {estimate['left']}")
        """
        data = {}
        if consumed is not None:
            data["consumed"] = consumed
        if left is not None:
            data["left"] = left
        if work is not None:
            data["work"] = work

        url = f"{self.old_api_base}/task-editEstimate-{estimate_id}.json"
        response = self.session.post(
            url, data=data, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {
                "message": "编辑工时成功",
                "status_code": response.status_code,
            }
        else:
            return False, {
                "message": f"编辑失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def delete_estimate(self, estimate_id: str) -> Tuple[bool, Dict]:
        """删除工时记录（老 API）

        Args:
            estimate_id: 工时记录ID

        Returns:
            (success, result) 注意：返回 HTML 页面。
            请使用 get_estimate(estimate_id) 验证删除结果（应返回失败）。

        Note:
            删除工时记录后，任务的 consumed 和 left 会自动更新。

        Example:
            >>> success, result = client.delete_estimate("1")
            >>> ok, estimate = client.get_estimate("1")
            >>> if not ok:
            >>>     print("工时记录已删除")
        """
        url = f"{self.old_api_base}/task-deleteEstimate-{estimate_id}-yes.json"
        response = self.session.get(url, params={"zentaosid": self.sid}, timeout=30)

        if response.status_code == 200:
            return True, {
                "message": "删除工时成功",
                "status_code": response.status_code,
            }
        else:
            return False, {
                "message": f"删除失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def finish_task(self, task_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """完成任务（老 API）

        Args:
            task_id: 任务ID
            comment: 完成备注（可选）

        Returns:
            (success, result) 注意：返回 HTML 页面。
            请使用 get_task_detail(task_id) 验证完成结果。

        Note:
            - 任务状态变为 'done'
            - 会记录 finishedBy 和 finishedDate
            - 建议先记录工时（left=0）再完成任务

        Example:
            >>> # 先记录工时
            >>> client.record_estimate("15", [{"date": "2026-03-27", "consumed": "3", "left": "0", "work": "完成"}])
            >>> # 再完成任务
            >>> success, result = client.finish_task("15", "已完成")
            >>> ok, task = client.get_task_detail("15")
            >>> print(f"状态: {task['status']}")  # done
            >>> print(f"完成人: {task['finishedBy']}")
        """
        if not self.sid:
            self.get_session()

        data = {}
        data["status"] = "done"
        if comment:
            data["comment"] = comment

        url = f"{self.old_api_base}/task-finish-{task_id}.json"
        response = self.session.post(
            url, data=data, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {
                "message": "完成任务成功",
                "status_code": response.status_code,
            }
        else:
            return False, {
                "message": f"完成失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def pause_task(self, task_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """暂停任务（老 API）

        Args:
            task_id: 任务ID
            comment: 暂停备注（可选）

        Returns:
            (success, result) 注意：返回 HTML 页面。
            请使用 get_task_detail(task_id) 验证暂停结果。

        Note:
            - 任务状态变为 'pause'
            - 仅对 doing 状态的任务有效

        Example:
            >>> success, result = client.pause_task("17", "暂停开发")
            >>> ok, task = client.get_task_detail("17")
            >>> print(f"状态: {task['status']}")  # pause
        """
        if not self.sid:
            self.get_session()

        data = {}
        data["status"] = "pause"
        if comment:
            data["comment"] = comment

        url = f"{self.old_api_base}/task-pause-{task_id}.json"
        response = self.session.post(
            url, data=data, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {
                "message": "暂停任务成功",
                "status_code": response.status_code,
            }
        else:
            return False, {
                "message": f"暂停失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def restart_task(self, task_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """继续任务（老 API）

        Args:
            task_id: 任务ID
            comment: 继续备注（可选）

        Returns:
            (success, result) 注意：返回 HTML 页面。
            请使用 get_task_detail(task_id) 验证继续结果。

        Note:
            - 将 pause 状态的任务恢复为 doing
            - 仅对 pause 状态的任务有效

        Example:
            >>> success, result = client.restart_task("17", "继续开发")
            >>> ok, task = client.get_task_detail("17")
            >>> print(f"状态: {task['status']}")  # doing
        """
        if not self.sid:
            self.get_session()

        data = {}
        data["status"] = "doing"
        if comment:
            data["comment"] = comment

        url = f"{self.old_api_base}/task-restart-{task_id}.json"
        response = self.session.post(
            url, data=data, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {
                "message": "继续任务成功",
                "status_code": response.status_code,
            }
        else:
            return False, {
                "message": f"继续失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def activate_task(self, task_id: str, comment: str = "") -> Tuple[bool, Dict]:
        """激活任务（老 API）

        Args:
            task_id: 任务ID
            comment: 激活备注（可选）

        Returns:
            (success, result) 注意：返回 HTML 页面。
            请使用 get_task_detail(task_id) 验证激活结果。

        Note:
            - 将 done/closed 状态的任务恢复为 doing
            - 对于 cancel 状态的任务可能无法激活

        Example:
            >>> success, result = client.activate_task("17", "重新开始")
            >>> ok, task = client.get_task_detail("17")
            >>> print(f"状态: {task['status']}")  # doing
        """
        if not self.sid:
            self.get_session()

        data = {}
        data["status"] = "doing"
        if comment:
            data["comment"] = comment

        url = f"{self.old_api_base}/task-activate-{task_id}.json"
        response = self.session.post(
            url, data=data, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {
                "message": "激活任务成功",
                "status_code": response.status_code,
            }
        else:
            return False, {
                "message": f"激活失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def assign_task(
        self, task_id: str, assigned_to: str, comment: str = ""
    ) -> Tuple[bool, Dict]:
        """指派任务（老 API）

        Args:
            task_id: 任务ID
            assigned_to: 指派给谁（用户名）
            comment: 指派备注（可选）

        Returns:
            (success, result) 注意：返回空响应。
            请使用 get_task_detail(task_id) 验证指派结果。

        Example:
            >>> success, result = client.assign_task("17", "zhangsan", "请处理")
            >>> ok, task = client.get_task_detail("17")
            >>> print(f"指派给: {task['assignedTo']}")  # zhangsan
        """
        if not self.sid:
            self.get_session()

        data = {"assignedTo": assigned_to}
        data["status"] = "doing"
        if comment:
            data["comment"] = comment

        url = f"{self.old_api_base}/task-assignTo-{task_id}.json"
        response = self.session.post(
            url, data=data, params={"zentaosid": self.sid}, timeout=30
        )

        if response.status_code == 200:
            return True, {
                "message": "指派任务成功",
                "status_code": response.status_code,
            }
        else:
            return False, {
                "message": f"指派失败: HTTP {response.status_code}",
                "status_code": response.status_code,
            }

    def create_task(
        self,
        project: str,
        name: str,
        type: str = "devel",
        story: str = "0",
        module: str = "0",
        assignedTo: str = "",
        pri: str = "3",
        desc: str = "",
        estimate: str = "0",
        **kwargs,
    ) -> Tuple[bool, Dict]:
        """创建任务（老 API）

        Args:
            project: 所属项目ID *必填
            name: 任务名称 *必填
            type: 任务类型 *必填，取值: design, devel, test, study, discuss, ui, affair, misc
            story: 相关需求ID
            module: 所属模块ID
            assignedTo: 指派给（用户名）
            pri: 优先级 (0-4)
            desc: 任务描述
            estimate: 预计工时

        Returns:
            (success, result)

        Example:
            >>> success, result = client.create_task(
            ...     project="1",
            ...     name="用户登录功能开发",
            ...     type="devel",
            ...     assignedTo="admin",
            ...     pri="3"
            ... )
        """
        return self.create_tasks(
            project=project,
            tasks=[
                {
                    "name": name,
                    "type": type,
                    "story": story,
                    "module": module,
                    "assignedTo": assignedTo or "admin",
                    "pri": pri,
                    "desc": desc,
                    "estimate": estimate,
                }
            ],
            **kwargs,
        )

    def create_tasks(
        self,
        project: str,
        tasks: List[Dict],
        story_id: str = "0",
        module_id: str = "0",
        parent_id: str = "0",
        **kwargs,
    ) -> Tuple[bool, Dict]:
        """批量创建任务（老 API）

        Args:
            project: 所属项目ID *必填
            tasks: 任务列表，每个任务包含 name, type, story, module, assignedTo, pri, desc, estimate
            story_id: 需求ID，默认 "0"
            module_id: 模块ID，默认 "0"
            parent_id: 父任务ID，默认 "0"

        Returns:
            (success, result)

        Example:
            >>> success, result = client.create_tasks(
            ...     project="1",
            ...     tasks=[
            ...         {"name": "任务1", "type": "devel", "assignedTo": "admin"},
            ...         {"name": "任务2", "type": "test", "assignedTo": "admin"}
            ...     ]
            ... )
        """
        if not self.sid:
            self.get_session()

        data = {}
        for i, task in enumerate(tasks):
            data[f"module[{i}]"] = task.get("module", "0")
            data[f"story[{i}]"] = task.get("story", "0")
            data[f"parent[{i}]"] = task.get("parent", "0")
            data[f"name[{i}]"] = task.get("name", "")
            data[f"type[{i}]"] = task.get("type", "devel")
            data[f"assignedTo[{i}]"] = task.get("assignedTo", "admin")
            data[f"estimate[{i}]"] = str(task.get("estimate", "0"))
            data[f"pri[{i}]"] = str(task.get("pri", "3"))
            data[f"desc[{i}]"] = task.get("desc", "")
            # ponytail: the task form label "任务方" is `developEnd` not
            # `execution`. Empty value triggers "任务方不能为空" 422.
            # Default to "0" (no specific task-side) — server accepts it.
            data[f"developEnd[{i}]"] = task.get("developEnd", "0")

        return self.old_request(
            "POST",
            f"/task-batchCreate-{project}-{story_id}-{module_id}-{parent_id}.json",
            data,
        )

    def get_my_tasks(self, task_type: str = "assignedTo") -> Tuple[bool, List[Dict]]:
        """获取我的任务列表（老 API）

        Args:
            task_type: 任务类型，可选值: assignedTo(指派给我), openedBy(由我创建), finishedBy(由我完成), closedBy(由我关闭), canceledBy(由我取消)

        Returns:
            (success, tasks) 任务列表

        Example:
            >>> success, tasks = client.get_my_tasks("assignedTo")
            >>> for task in tasks:
            ...     print(f"[{task['id']}] {task['name']} ({task['status']})")
        """
        return True, self._data(f"/my-task-{task_type}.json", "tasks")

    def get_my_bugs(
        self, bug_type: str = "assignedTo", order_by: str = "id_desc"
    ) -> Tuple[bool, List[Dict]]:
        """获取我的Bug列表（老 API）

        Args:
            bug_type: Bug类型，可选值: assignedTo(指派给我), openedBy(由我创建), resolvedBy(由我解决), closedBy(由我关闭)
            order_by: 排序字段，默认 id_desc

        Returns:
            (success, bugs) Bug列表

        Example:
            >>> success, bugs = client.get_my_bugs("assignedTo")
            >>> for bug in bugs:
            ...     print(f"[{bug['id']}] {bug['title']} ({bug['status']})")
        """
        return True, self._data(f"/my-bug-{bug_type}-{order_by}.json", "bugs")

    def get_my_stories(self, story_type: str = "assignedTo") -> Tuple[bool, List[Dict]]:
        """获取我的需求列表（老 API）

        Args:
            story_type: 需求类型，可选值: assignedTo(指派给我), openedBy(由我创建), reviewedBy(由我评审), closedBy(由我关闭)

        Returns:
            (success, stories) 需求列表

        Example:
            >>> success, stories = client.get_my_stories("assignedTo")
            >>> for story in stories:
            ...     print(f"[{story['id']}] {story['title']} ({story['status']})")
        """
        return True, self._data(f"/my-story-{story_type}.json", "stories")

    def get_my_projects(self) -> Tuple[bool, List[Dict]]:
        """获取我的项目列表（老 API）

        Returns:
            (success, projects) 项目列表

        Example:
            >>> success, projects = client.get_my_projects()
            >>> for project in projects:
            ...     print(f"[{project['id']}] {project['name']}")
        """
        return True, self._data("/my-project.json", "projects")

