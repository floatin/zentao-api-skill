# 写操作启用与验证 Plan

## 背景

`zentao-cli` 当前有 5 个写操作已实现（在 `zentao_api/cli.py` 的 `COMMANDS` 字典里）：

| 命令 | 作用 | ZenTao API |
|---|---|---|
| `create-story` | 新建需求 | `POST /story-create-...` |
| `create-task` | 新建任务 | `POST /task-create-...` |
| `batch-create-tasks` | 批量创建子任务 | `POST /task-batchCreate-...` |
| `create-productplan` | 新建发布计划 | `POST /productplan-create-...` |
| `review-story` | 评审需求 | `POST /story-review-...` |

每个都通过 `_confirm()` 要求 `y/n` 确认。**功能完整，但从未在真实环境验证过**（之前 smoke test 只跑了只读接口）。

## 目标

1. **开**：写操作本来就"开"着（不需要改代码），但要在**受控沙箱**里跑，不污染生产数据
2. **验证**：每个写操作走通"写→读回确认→清理"闭环

## 前置条件

```bash
# 1. CLI 可用
zentao --help   # exit 0
which zentao    # /usr/local/bin/zentao (pipx) 或 .venv/bin/zentao

# 2. 凭证就绪
ls -la ~/.config/zentao-cli/.env
# 读权限 -rw------- (chmod 600)
```

## 沙箱选择

**找 1 个低风险产品/项目**做测试。优先级：

1. **首选**：找名字含 `test` / `sandbox` / `dev` / `示例` 的产品
2. **次选**：选活跃度低的（创建日期早、最近没改动的）
3. **避免**：核心业务产品（AI选得准、ERP 等），因为误操作影响范围大

**用代码找**：
```bash
# 列出所有产品
zentao products

# 找一个不重要的项目
zentao projects --status closed | head -20
# 或找一个长期 doing 但没故事的
zentao projects --status doing > projects.txt
# 手挑 ID 最大的（多半是早期测试项目）
```

**记下**：
- `PRODUCT_ID`（测试用产品）
- `EXECUTION_ID`（测试用执行/迭代）
- `PROJECT_ID`（测试用项目，可选）

## 验证流程（每个写操作）

通用模板：

```bash
# 1. 记录当前状态
BEFORE=$(zentao stories --project-id $PROJECT_ID 2>&1 | grep -c '|')
echo "Stories before: $BEFORE"

# 2. 跑写操作（echo y 自动确认）
echo "y" | zentao create-story \
    --product-id $PRODUCT_ID \
    --execution-id $EXECUTION_ID \
    --title "TEST_$(date +%s)_创建需求"

# 3. 读回确认
AFTER=$(zentao stories --project-id $PROJECT_ID 2>&1 | grep -c '|')
echo "Stories after: $AFTER"
[ $AFTER -eq $((BEFORE + 1)) ] && echo "✅ verified" || echo "❌ FAILED"

# 4. 找新创建的那条（用 TEST_ 前缀搜索）
zentao stories --project-id $PROJECT_ID | grep "TEST_"
```

### 步骤 1：验证 `create-story`

```bash
echo "y" | zentao create-story \
    --product-id $PRODUCT_ID \
    --execution-id $EXECUTION_ID \
    --title "TEST_$(date +%s)_验证写操作_create-story" \
    --reviewer huaimin
```

**期望**：返回 `✅ 新建成功，需求 ID: <数字>`

**验证**：再 `zentao stories --project-id $PROJECT_ID` 看列表多一条，标题含 `TEST_`

### 步骤 2：验证 `create-task`

```bash
# 用刚创建的 story_id
STORY_ID=<上面返回的 ID>

echo "y" | zentao create-task \
    --execution-id $EXECUTION_ID \
    --story-id $STORY_ID \
    --name "TEST_$(date +%s)_验证_create-task" \
    --assign-to huaimin
```

**期望**：`✅ 新建成功，任务 ID: <数字>`

**验证**：`zentao tasks --execution-id $EXECUTION_ID | grep TEST_` 能找到

### 步骤 3：验证 `batch-create-tasks`

先创建一个父任务：
```bash
echo "y" | zentao create-task \
    --execution-id $EXECUTION_ID \
    --story-id $STORY_ID \
    --name "TEST_父任务_$(date +%s)" \
    --assign-to huaimin
PARENT_ID=<返回的 ID>
```

再批量创建子任务：
```bash
echo "y" | zentao batch-create-tasks \
    --execution-id $EXECUTION_ID \
    --parent-id $PARENT_ID \
    --tasks "子任务A:2,子任务B:3,子任务C:1"
```

**期望**：`✅ 创建子任务成功`（或类似）

**验证**：
```bash
zentao tasks --execution-id $EXECUTION_ID | grep "TEST_"
# 应看到父任务 + 3 个子任务
```

### 步骤 4：验证 `create-productplan`

```bash
echo "y" | zentao create-productplan \
    --product-id $PRODUCT_ID \
    --title "TEST_$(date +%s)_发布计划"
```

**期望**：`✅ 新建成功，计划 ID: <数字>`

**验证**：`zentao productplans --product-id $PRODUCT_ID | grep TEST_`

### 步骤 5：验证 `review-story`

⚠️ **这个会修改 story 状态**（从 `active` → `reviewed`），需谨慎：

```bash
# 先看 story 当前状态
zentao stories --project-id $PROJECT_ID | head -10
# 选一条状态是 active 的、不是我们刚创建的，做评审
# 或者直接评审我们刚创建的 TEST_ 需求（如果它还没评审过）

echo "y" | zentao review-story --story-id $STORY_ID
```

**期望**：`✅ 需求 <ID> 评审通过`

**验证**：
```bash
# review 后 get_story 看 status 字段
.venv/bin/python -c "
from zentao_api.client import ZenTaoClient
c = ZenTaoClient('http://zentao.yishou.com/zentao', 'huaimin', 'shen0527')
ok, s = c.get_story('$STORY_ID')
print(f'status: {s.get(\"status\")}, reviewedBy: {s.get(\"reviewedBy\")}')"
```

## 清理

**问题**：ZenTao 老 API 没有 `delete-story` / `delete-task` 方法（只有 `close`、`cancel`）。

清理方式（**这些操作本身也需确认**，所以建议留下测试数据让用户手动清）：

1. **软清理**（推荐，保留审计痕迹）：把测试数据用 `close-task` / `cancel-task` 标"关闭"或"取消"
   - 但 `close_task` / `cancel_task` 没在 CLI 里暴露，得直接调 Python：
     ```python
     c.cancel_task(task_id, "测试数据，关闭")
     ```
2. **不清理**：留 `TEST_<timestamp>` 前缀，以后人工删/移到归档项目

**建议**：测试完不删，统一加 `TEST_` 前缀定期清理。

## 安全措施

| 风险 | 缓解 |
|---|---|
| 误操作生产数据 | 选不活跃的产品/项目；所有数据加 `TEST_<timestamp>` 前缀 |
| 重复执行 | 用 `$(date +%s)` 每次唯一 |
| 误把子任务当父任务 | 操作前 `--project-id` 重新确认 |
| 评审误触发 | 步骤 5 单独做，先看 story 当前状态 |

## 长期改进

| 改进 | 说明 |
|---|---|
| `--dry-run` 标志 | 所有写操作加这个标志，只打印不发请求 |
| 集成测试 | 跑本地 mock ZenTao 服务（类似 `httpserver`）做端到端测试 |
| 操作记录 | 写操作结果写入 `~/.zentao-cli/operations.log` 方便回溯 |
| 二次确认 | 写操作在已确认后倒计时 5 秒再执行，给取消机会 |

## 验证完成判定

每个写操作满足：
1. ✅ CLI exit 0
2. ✅ 确认 prompt 正常显示
3. ✅ 输入 `y` 后执行成功（消息含 ID）
4. ✅ 立即 `GET` 能读到刚创建的数据
5. ✅ 字段值正确（标题、状态等）

5 个全过 = 验证完成。
