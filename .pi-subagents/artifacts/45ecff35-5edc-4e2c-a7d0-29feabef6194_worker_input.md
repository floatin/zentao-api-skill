# Task for worker

You are a delegated subagent running from a fork of the parent session. Treat the inherited conversation as reference-only context, not a live thread to continue. Do not continue or answer prior messages as if they are waiting for a reply. Your sole job is to execute the task below and return a focused result for that task using your tools.

Task:
## 任务：P0 + P4 — 修复 CLI 断链 + 删除重复 `create_story`

### 上下文
仓库：`/Users/floating/workspace/zentao-api-skill/`
- `zentao_api/cli.py` (557 行) 调用 `zentao_api/client.py` (3567 行，137 方法) 的方法
- `zentao_api/client.py` 是单个 `ZenTaoClient` 类
- 已存在测试目录：`scripts/test_*.py`（针对真实 ZenTao 服务，**不要**修改）

### P0 — 修复 CLI 断链

`cli.py` 调用了 `client.py` **不存在**的方法：

| cli.py 调用 | client.py 实际情况 |
|---|---|
| `client.get_projects(status)` | 只有 `get_project_list_old()` |
| `client.get_executions(project_id)` | **完全不存在**（需新增） |
| `client.get_stories(project_id)` | **完全不存在**（需新增） |
| `client.get_tasks(execution_id)` | 只有 `get_project_tasks_old()` |
| `client.get_bugs(product_id)` | 只有 `get_bug_list_old()` 和 `get_project_bugs()` |
| `client.get_productplans(product_id)` | 只有 `get_productplan_list_old()` |
| `client.batch_create_tasks(...)` | 只有 `create_tasks()` 和 `create_subtasks()` |
| `client.create_productplan(...)` | 只有 `create_plan()` |

**要求：**
- 优先**在 `client.py` 中补齐缺失方法**，保持与现有命名风格一致
- 新方法复用现有 `_data_get` 模式（如果存在）或 `old_request + json.loads` 模式
- `cli.py` 中已有降级到老 API 的回退逻辑；优先补 REST-ish 方法，方法名与 `cli.py` 调用一致

补齐的方法（最终要满足 cli.py 调用）：
1. `get_projects(status='doing') -> Tuple[bool, List[Dict]]` — 用 `/project-index-{status}.json` 端点
2. `get_executions(project_id) -> Tuple[bool, List[Dict]]` — 用 `/project-execution-{project_id}.json`
3. `get_stories(project_id) -> Tuple[bool, List[Dict]]` — 用 `/project-story-{project_id}.json`
4. `get_tasks(execution_id) -> Tuple[bool, List[Dict]]` — 用 `/execution-task-{execution_id}.json`
5. `get_bugs(product_id) -> Tuple[bool, List[Dict]]` — 用 `/product-bug-{product_id}.json`
6. `get_productplans(product_id) -> Tuple[bool, List[Dict]]` — 把 `_old` 字典返回转成 `[{id, title}, ...]` 列表形式
7. `batch_create_tasks(execution_id, parent_id, tasks) -> Tuple[bool, Dict]` — 委托给现有 `create_tasks()` 或 `create_subtasks()`
8. `create_productplan(product_id, title) -> Tuple[bool, Dict]` — 委托给 `create_plan()`

**注意：** URL 端点路径如果不确定，看现有方法（如 `get_my_*`）的路径风格去猜，但**不要**瞎编。在测试中 mock 掉 `old_request`，所以实际 URL 不重要，只要函数签名匹配即可。

### P4 — 删除重复 `create_story`

`client.py` 中 `create_story` 定义了**两次**：
- 行 350：`(product_id, execution_id, title, module, plan_id, branch, reviewer)`
- 行 1711：`(product_id, title, module, plan, execution_id, branch, **kwargs)` ← 覆盖前者

**要求：**
- 保留**签名更通用**的版本（行 1711，带 `**kwargs`），删除行 350 的版本
- 同时更新 cli.py 中 `cmd_create_story` 的 `client.create_story` 调用以匹配新签名

### 测试要求（mock 方式）

在 `tests/` 目录下新建测试文件（用 `unittest.mock` mock `requests` / `old_request`）：

1. `tests/test_client_missing_methods.py` — 覆盖 P0 新增的 8 个方法，每个方法一个测试，mock `old_request` 返回 `{"status":"success","data":"{\"key\": [...]}"}`，断言返回值正确解析
2. `tests/test_create_story_signature.py` — 验证 `create_story` 的最终签名是 `(product_id, title, ...)` 形式，验证 cli.py 调用能匹配
3. `tests/test_cli_command_routing.py` — mock 掉 `ZenTaoClient`，验证 cli.py 的 `parse_args` 能解析中文命令（如 "禅道需求列表 项目=176"），并分发到正确的 cmd 函数

测试必须：
- 不依赖网络（全部 mock）
- 用 `python -m pytest tests/ -v` 全过
- 不引入新的第三方依赖

### 提交流程
每完成一个里程碑就 `git commit`：
1. `git add tests/ zentao_api/client.py` 然后 commit "P0: 补齐 cli 缺失方法"
2. `git add zentao_api/client.py zentao_api/cli.py` 然后 commit "P4: 合并重复的 create_story"
3. `git add tests/` 然后 commit "test: cli 路由与 create_story 签名测试"

### 不要做
- 不要碰 `scripts/test_*.py`（这些是真服务器测试）
- 不要拆 client.py（P1 才做）
- 不要重写 cli.py（P3 才做）
- 不要改 `pyproject.toml` 或 `requirements.txt`（除非需要 pytest）

完成后报告：
- 改了哪些文件、行数
- 测试通过的命令与输出
- 三个 commit 的 hash
- 任何未解决的疑问

## Acceptance Contract
Acceptance level: reviewed
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Implement the requested change without widening scope
- criterion-2: Return evidence sufficient for an independent acceptance review

Required evidence: changed-files, tests-added, commands-run, validation-output, residual-risks, no-staged-files

Review gate: required by reviewer.

Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
`criteriaSatisfied[].status` must be exactly one of: satisfied, not-satisfied, not-applicable.
`commandsRun[].result` must be exactly one of: passed, failed, not-run.
`manualNotes` and `notes` are optional strings; an empty string means no note and does not satisfy `manual-notes` evidence.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    },
    {
      "id": "criterion-2",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```