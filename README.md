# zentao-cli

命令行禅道项目管理工具。

## 特性

- **轻量**：纯 Python + `requests`，装一个包就能用
- **凭证外置**：`.env` 文件配置，与代码分离，方便轮转密码
- **28 个子命令**：7 个只读 + 21 个写操作（4 类工单：需求/任务/Bug/计划）
- **集成 Python 库**：也可作为 `from zentao_api.client import ZenTaoClient` 在代码中使用
- 148+ 个方法覆盖：产品、项目、需求、任务、Bug、QA 测试、发布、版本、计划

## 安装

推荐用 [pipx](https://pypa.github.io/pipx/) 全局安装 CLI 工具——它会为每个工具建独立虚拟环境，但命令暴露到 `$PATH`，不污染项目依赖。

```bash
# 首次：装 pipx（macOS / Debian / 自举三选一）
brew install pipx          # macOS
apt install pipx           # Debian/Ubuntu
pipx ensurepath            # 把 ~/.local/bin 加到 PATH

# 装包：zentao 命令可用
pipx install ys-zentao-api

# 试用不装：跑最新版的命令
pipx run --spec ys-zentao-api zentao --help

# 升级
pipx upgrade ys-zentao-api
```

需要 Python 3.8+。

### 从源码开发

```bash
git clone <repo>
cd ys-zentao-api
pipx install -e .          # 可编辑装到全局
# 或者
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pytest tests/ -v
```

## 配置

凭证放在 `~/.config/zentao-cli/.env`（格式：`.env`）：

```bash
mkdir -p ~/.config/zentao-cli
cat > ~/.config/zentao-cli/.env <<EOF
endpoint=http://zentao.xxx.com/zentao
username=xxx
password=xxx
EOF
chmod 600 ~/.config/zentao-cli/.env
```

字段说明：

| 字段 | 说明 |
|---|---|
| `endpoint` | 禅道地址，含 `http(s)://` 和子路径（如 `/zentao`） |
| `username` | 登录账号 |
| `password` | 登录密码 |

也可通过 `--env-file PATH` 指定其他路径（不指定则用默认）：

```bash
zentao --env-file /path/to/.env products
```

> `--help` 不会读凭证，可随时运行。

## 使用

```bash
zentao --help
```

输出 28 个子命令：

```
zentao [-h] [--env-file ENV_FILE]
       {products,projects,executions,stories,tasks,bugs,productplans,
        create-story, create-task, batch-create-tasks, create-productplan, review-story,
        start-task, pause-task, restart-task, finish-task, close-task, cancel-task,
        activate-task, assign-task,
        assign-bug, confirm-bug, resolve-bug, close-bug, activate-bug,
        assign-story, close-story, activate-story}
```

### 只读命令（7 个）

#### `products` — 查询产品列表

```bash
zentao products
```

#### `projects [--status STATUS]` — 查询项目列表

```bash
zentao projects                  # 默认 status=doing
zentao projects --status all    # 全部状态
```

#### `executions --project-id ID` — 查询执行列表

```bash
zentao executions --project-id 45
```

#### `stories --project-id ID [--limit N]` — 查询需求列表

```bash
zentao stories --project-id 45
zentao stories --project-id 45 --limit 10
```

#### `tasks --execution-id ID [--limit N]` — 查询任务列表

```bash
zentao tasks --execution-id 200
```

#### `bugs --product-id ID [--limit N]` — 查询缺陷列表

```bash
zentao bugs --product-id 35
```

#### `productplans --product-id ID` — 查询发布计划

```bash
zentao productplans --product-id 35
```

### 写操作命令（21 个）

写操作前会打印操作详情并要求 `y/n` 确认。CI/脚本中可管道 `echo y |` 自动确认。

#### 创建类（5 个）

##### `create-story` — 新建需求

```bash
zentao create-story \
    --product-id 35 \
    --execution-id 200 \
    --title "登录流程改造" \
    --plan-id 0
```

> ZenTao 旧 API 要求 `module` 字段（如 `[模块1]` / `[模块2]`），CLI 默认传 `module=0`（URL 占位符），body 不发送。如需绑定到具体模块，CLI 当前未支持 — 调 Python client。

##### `create-task` — 新建任务

```bash
zentao create-task \
    --execution-id 200 \
    --story-id 1234 \
    --name "前端登录页面" \
    --assign-to alice \
    --parent-id 999   # 可选，指定为子任务
```

##### `batch-create-tasks` — 批量创建子任务

```bash
zentao batch-create-tasks \
    --execution-id 200 \
    --parent-id 999 \
    --tasks "前端开发:8,后端开发:16,联调测试:4"
```

`--tasks` 格式：`名称1:工时,名称2:工时`。

##### `create-productplan` — 新建发布计划

```bash
zentao create-productplan --product-id 35 --title "Q3 计划"
```

##### `review-story` — 评审需求

```bash
zentao review-story --story-id 1234
```

#### 任务状态流转（8 个）

每个任务都有一套状态：`wait → doing → done → closed`（中间可 pause / restart / cancel / activate）。

| 命令 | 状态流转 | 备注 |
|---|---|---|
| `start-task` | wait → doing | ZenTao 服务端校验较严，部分服务器会拒绝 |
| `pause-task` | doing → pause | |
| `restart-task` | pause → doing | |
| `finish-task` | doing → done | |
| `close-task` | done → closed | |
| `cancel-task` | 任意 → cancel | |
| `activate-task` | done/closed → doing | |
| `assign-task` | 改 assignee | |

通用格式：`zentao <name> --task-id ID [--comment "..."]`，`assign-task` 额外需要 `--assigned-to USER`。

```bash
zentao start-task --task-id 1234 --comment "开始开发"
zentao assign-task --task-id 1234 --assigned-to alice
zentao finish-task --task-id 1234
zentao close-task --task-id 1234
zentao activate-task --task-id 1234  # 重新打开已关闭的
```

#### Bug 状态流转（5 个）

| 命令 | 状态流转 | 备注 |
|---|---|---|
| `assign-bug` | 改 assignee | |
| `confirm-bug` | active → confirmed | |
| `resolve-bug` | confirmed → resolved | 需 `--resolution` (`fixed`/`postponed`/`willnotfix`/`duplicate`/`tostory`) 和 `--build` |
| `close-bug` | resolved → closed | |
| `activate-bug` | closed/resolved → active | 重新打开 |

通用格式：`zentao <name> --bug-id ID`，`assign-bug` 额外需要 `--assigned-to`，`resolve-bug` 额外需要 `--resolution` + `--build`。

```bash
zentao confirm-bug --bug-id 1234
zentao resolve-bug --bug-id 1234 --resolution fixed --build 1
zentao close-bug --bug-id 1234
zentao assign-bug --bug-id 1234 --assigned-to alice
```

#### 需求状态流转（3 个）

| 命令 | 状态流转 |
|---|---|
| `assign-story` | 改 assignee（走 `change_story`） |
| `close-story` | active → closed |
| `activate-story` | closed → active |

```bash
zentao assign-story --story-id 1234 --assigned-to alice
zentao close-story --story-id 1234
zentao activate-story --story-id 1234
```

## 退出码

| 码 | 含义 |
|---|---|
| `0` | 成功 |
| `1` | 凭证缺失或读失败 |
| `2` | argparse 参数错误（如缺 `--project-id`） |
| 其他 | 工具内部异常 |

## 故障排查

**`❌ 未找到凭证文件：~/.config/zentao-cli/.env`**
凭证未创建或权限不够。重新创建并 `chmod 600`。

**`认证失败`**
`endpoint` 是否带子路径（如 `/zentao`）、用户名密码是否对、账号是否被禁用。

**CLI 命令列出了 0 条但实际有数据**
端点路径可能与禅道实际路径不一致。检查 `endpoint` 末尾的子路径。

**`--limit 0` 没有限制效果**
设计如此：`--limit 0` 等同于不传。要限制请传正整数。

**某些写操作 fake success（server 返回成功但实际未改状态）**
可能是 ZenTao 服务端验证规则问题（如 `start-task` 在某些 server 配置下被拒）。CLI 端已正确发出请求，错误在 server 端。

**`create-story` / `create-bug` 提示 "『所属模块』不能为空"**
ZenTao 老 API 要求 `module` 字段（`[模块1]` / `[模块2]` 格式），CLI 默认传 `module=0`（URL 占位符）。如需绑模块，调 Python client 直接传 `module="[模块1]"`。

## 作为 Python 库

```python
from zentao_api.client import ZenTaoClient

client = ZenTaoClient(
    endpoint="http://zentao.xxx.com/zentao",
    username="xxx",
    password="xxx",
)

# 列出产品
ok, products = client.get_products()
print(f"{len(products)} products")

# 查项目下的需求
ok, stories = client.get_stories("45")
for s in stories:
    print(f"[{s['id']}] {s['title']}")

# 任务状态流转
client.start_task("1234", comment="开始")
client.pause_task("1234")
client.finish_task("1234")
client.close_task("1234")

# 创建带模块的 Bug（CLI 不支持的细节）
client.create_bug(
    product_id="36", module="[模块1]", project="281", opened_build="1",
    title="bug 标题", steps="<p>步骤</p>",
    assigned_to="huaimin", type="codeerror", severity="3", pri="3",
    deadline="2026-12-31",
)
```

148+ 个方法覆盖：产品、项目、需求、任务、Bug、QA 测试、发布、版本、计划。

## 项目结构

```
ys-zentao-api/
├── zentao_api/
│   ├── __init__.py
│   ├── cli.py                # argparse + 命令字典分发（28 个子命令）
│   └── client/               # 11 个 mixin 组成的包
│       ├── _base.py          # 鉴权 + old_request + _data helpers
│       ├── _credentials.py   # .env 读取
│       ├── _legacy.py        # 老 API 兜底
│       ├── products.py       # 产品
│       ├── projects.py       # 项目
│       ├── stories.py        # 需求
│       ├── tasks.py          # 任务
│       ├── bugs.py           # 缺陷
│       ├── qa.py             # QA 测试
│       ├── releases.py       # 发布
│       ├── builds.py         # 版本
│       ├── plans.py          # 计划
│       └── writes.py         # 任务状态变更 + get_my_*
├── tests/                    # 166 个 mock 单元测试
├── .github/workflows/test.yml
├── pyproject.toml
└── README.md
```

## 测试

```bash
pip install -e . pytest
pytest tests/ -v
```

166 个 mock 测试覆盖：
- 11 个 mixin 的核心方法
- CLI 28 个子命令的 parser 注册 + dispatch
- `.env` 解析与路径处理
- 失败 / 取消 / 参数错误各路径

CI 在 3 OS × 3 Python 版本（3.8/3.10/3.12）矩阵上跑（`.github/workflows/test.yml`）。

## 许可证

MIT