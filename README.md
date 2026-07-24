# zentao-cli

命令行禅道项目管理工具。

## 特性

- **轻量**：纯 Python + `requests`，装一个包就能用
- **凭证外置**：`.env` 文件配置，与代码分离，方便轮转密码
- **只读优先**：7 个 GET 类子命令 + 5 个写操作子命令（含确认 prompt）
- **集成 Python 库**：也可作为 `from zentao_api.client import ZenTaoClient` 在代码中使用
- 148 个方法覆盖：产品、项目、需求、任务、Bug、QA 测试、发布、版本、计划

## 安装

```bash
pip install ys-zentao-api
```

或从源码：

```bash
git clone <repo>
cd ys-zentao-api
pip install -e .
```

`zentao` 命令会注册到 `$PATH`。

要求 Python 3.8+。

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

输出所有 12 个子命令。语法：

```
zentao [-h] [--env-file ENV_FILE]
       {products,projects,executions,stories,tasks,bugs,productplans,
        create-story,create-task,batch-create-tasks,create-productplan,review-story}
```

### 只读命令

#### `products` — 查询产品列表

```bash
zentao products
```

```
📋 查询禅道产品列表

✅ 共 22 条

ID | 产品名称      | 状态 | 负责人
---+------------+----+----
35 | xxx      |    |
34 | xxx    |    |
...
```

#### `projects [--status STATUS]` — 查询项目列表

```bash
zentao projects                  # 默认 status=doing
zentao projects --status all    # 全部状态
zentao projects --status closed
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
zentao tasks --execution-id 200 --limit 20
```

#### `bugs --product-id ID [--limit N]` — 查询缺陷列表

```bash
zentao bugs --product-id 35
```

#### `productplans --product-id ID` — 查询发布计划

```bash
zentao productplans --product-id 35
```

### 写操作命令

写操作前会打印操作详情并要求输入 `y/n` 确认。CI/脚本中可管道 `echo y |` 自动确认。

#### `create-story` — 新建需求

```bash
zentao create-story \
    --product-id 35 \
    --execution-id 200 \
    --title "xxx流程改造" \
    --plan-id 0 \
    --reviewer alice
```

#### `create-task` — 新建任务

```bash
zentao create-task \
    --execution-id 200 \
    --story-id 1234 \
    --name "xxx登录页面" \
    --assign-to alice \
    --parent-id 999   # 可选，指定为子任务
```

#### `batch-create-tasks` — 批量创建子任务

```bash
zentao batch-create-tasks \
    --execution-id 200 \
    --parent-id 999 \
    --tasks "前端开发:8,后端开发:16,联调测试:4"
```

`--tasks` 格式：`名称1:工时,名称2:工时`。

#### `create-productplan` — 新建发布计划

```bash
zentao create-productplan --product-id 35 --title "Q3 计划"
```

#### `review-story` — 评审需求

```bash
zentao review-story --story-id 1234
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
```

## 项目结构

```
ys-zentao-api/
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
├── .github/workflows/test.yml
├── pyproject.toml
└── README.md
```

## 测试

```bash
pip install -e .
pip install pytest
pytest tests/ -v
```

97 个 mock 测试覆盖所有 mixin 的核心方法、CLI 命令分发、`.env` 解析。CI 在 3 OS × 3 Python 版本（3.8/3.10/3.12）矩阵上跑。

## 许可证

MIT