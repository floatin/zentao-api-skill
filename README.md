# zentao-cli

命令行禅道项目管理工具 — 一份二进制，免 Python 环境。

## 特性

- **独立可执行**：多平台编译，无运行时依赖
- **只读优先**：7 个 GET 类子命令 + 5 个写操作子命令（含确认 prompt）
- **Session 复用**：登录态持久化到 `~/.zentao-cli/`
- **凭证外置**：`.env` 文件配置，与二进制分离，方便轮转密码

## 安装

### 方式一：下载预编译二进制（推荐）

到 [Releases](../../releases) 页面下载对应平台的可执行文件：

| 平台 | 文件 |
|---|---|
| macOS (arm64) | `zentao-cli` |
| Linux (x86_64) | `zentao-cli` |
| Windows | `zentao-cli.exe` |

```bash
chmod +x zentao-cli
mv zentao-cli /usr/local/bin/   # 或任意 PATH 目录
zentao-cli --help
```

### 方式二：从源码构建

```bash
git clone <repo>
cd zentao-api-skill
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install nuitka

# 编译
python -m nuitka --standalone --enable-plugin=anti-bloat \
    --jobs=1 --disable-ccache \
    --remove-output --output-filename=zentao-cli \
    zentao_api/cli.py
# 产物：cli.dist/zentao-cli
```

> **macOS Homebrew 用户必加 `--disable-ccache`**：本机 `ccache` 依赖 `libfmt.11.dylib`，但 Homebrew 装的是 12，会静默失败。

### 方式三：作为 Python 模块

```bash
pip install -e .
zentao --help   # 安装时通过 [project.scripts] 注册
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
zentao-cli --env-file /path/to/.env products
```

> `--help` 查看更详细的使用说明。

## 使用

```bash
zentao-cli --help
```

输出所有 12 个子命令。语法：

```
zentao-cli [-h] [--env-file ENV_FILE]
           {products,projects,executions,stories,tasks,bugs,productplans,
            create-story,create-task,batch-create-tasks,create-productplan,review-story}
```

### 只读命令

#### `products` — 查询产品列表

```bash
zentao-cli products
```

```
📋 查询禅道产品列表


ID | 产品名称      | 状态 | 负责人
---+------------+----+----
35 | xxx      |    |
34 | xxx    |    |
...
```

#### `projects [--status STATUS]` — 查询项目列表

```bash
zentao-cli projects                  # 默认 status=doing
zentao-cli projects --status all    # 全部状态
zentao-cli projects --status closed
```

#### `executions --project-id ID` — 查询执行列表

```bash
zentao-cli executions --project-id 45
```

#### `stories --project-id ID [--limit N]` — 查询需求列表

```bash
zentao-cli stories --project-id 45
zentao-cli stories --project-id 45 --limit 10
```

#### `tasks --execution-id ID [--limit N]` — 查询任务列表

```bash
zentao-cli tasks --execution-id 200
zentao-cli tasks --execution-id 200 --limit 20
```

#### `bugs --product-id ID [--limit N]` — 查询缺陷列表

```bash
zentao-cli bugs --product-id 35
```

#### `productplans --product-id ID` — 查询发布计划

```bash
zentao-cli productplans --product-id 35
```

### 写操作命令（5 个，会触发确认 prompt）

写操作前会打印操作详情并要求输入 `y/n` 确认。CI/脚本中可管道 `echo y |` 自动确认。

#### `create-story` — 新建需求

```bash
zentao-cli create-story \
    --product-id 35 \
    --execution-id 200 \
    --title "xxx流程改造" \
    --plan-id 0 \
    --reviewer alice
```

#### `create-task` — 新建任务

```bash
zentao-cli create-task \
    --execution-id 200 \
    --story-id 1234 \
    --name "xxx登录页面" \
    --assign-to alice \
    --parent-id 999   # 可选，指定为子任务
```

#### `batch-create-tasks` — 批量创建子任务

```bash
zentao-cli batch-create-tasks \
    --execution-id 200 \
    --parent-id 999 \
    --tasks "前端开发:8,后端开发:16,联调测试:4"
```

`--tasks` 格式：`名称1:工时,名称2:工时`。

#### `create-productplan` — 新建发布计划

```bash
zentao-cli create-productplan --product-id 35 --title "Q3 计划"
```

#### `review-story` — 评审需求

```bash
zentao-cli review-story --story-id 1234
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

148 个方法覆盖：产品、项目、需求、任务、Bug、QA 测试、发布、版本、计划。

## 项目结构

```
zentao-api-skill/
├── zentao_api/
│   ├── __init__.py
│   ├── cli.py                # argparse + 命令字典分发
│   └── client/               # 12 个 mixin 组成的包
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
│       └── writes.py         # 状态变更 + get_my_*
├── tests/                    # 97 个 mock 单元测试
├── cli.dist/
│   └── zentao-cli            # 编译产物（gitignored）
├── pyproject.toml
└── README.md
```

## 测试

```bash
.venv/bin/python -m pytest tests/ -v
```

97 个 mock 测试覆盖所有 mixin 的核心方法、CLI 命令分发、`.env` 解析。

## 许可证

MIT
