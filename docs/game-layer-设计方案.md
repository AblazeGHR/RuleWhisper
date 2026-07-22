# Game Layer 设计方案

> 从 `character.py` 的全局单例角色卡升级为多团多角色持久化层。
> 状态：设计中，待确认项逐条标记 ⚠️。

---

## 一、目录结构

```
game/
├── {game_id}/
│   ├── game.json           ← 跑团会话元数据
│   └── characters/
│       ├── 哈维.json
│       ├── 丽萨.json
│       └── ...
└── ...
```

- `game_id`：UUID 自动生成，首次引用时创建。
- `game.json` 元数据：

```json
{
  "game_id": "<UUID>",
  "label": "周三跑团",
  "created_at": "2026-07-22T...",
  "group_id": null,
  "mode": "coc7th"
}
```

| 字段 | 用途 |
|------|------|
| `game_id` | 唯一标识（UUID） |
| `label` | 可读名称 |
| `created_at` | 创建时间戳 |
| `group_id` | 关联 QQ 群号（Pan session 定位用），可为 null |
| `mode` | 规则版本（默认 coc7th） |

- `keeper_id` 暂不存储。
- 🟢 已确认。

---

## 二、game 创建方式

- **第一阶段**：CLI 手动创建（`python src/cli.py game new "周三跑团"` → 打印 game_id）。
- 后续可扩展自动创建（群首次使用 RuleWhisper 时 Pan 触发）。
- CLI 命令存在后，创建方式更改成本低。
- 🟢 已确认。

---

## 三、game_id 传参方式

- 使用 **MCP 工具参数**，而非 MCP Server 启动参数。
- 每个 MCP tool 接受 `game_id` 参数：
  ```
  roll_dice(game_id, expression) → ...
  get_weapon(game_id, name) → ...
  query_rule(game_id, query) → ...    # game_id 可选：规则查询不依赖 game
  ```
- Pan 侧在 session metadata 存储 game_id，每次调用 MCP tool 时传入。
- 🟢 已确认。

---

## 四、角色卡 schema

沿用现有 `character.py` DEFAULT_CHAR 结构，增加战斗属性：

```json
{
  "name": "哈维",
  "attributes": {
    "力量": 65, "体质": 60, "敏捷": 55, "外貌": 50,
    "智力": 75, "意志": 70, "教育": 70, "幸运": 60,
    "体力": 60, "体型": 65
  },
  "skills": {
    "侦查": 55, "图书馆使用": 25, "聆听": 40
  },
  "san": 60,
  "hp": 12,
  "mp": 14,
  "luck": 60,
  "created_at": "2026-07-22T..."
}
```

- `hp`/`mp`/`luck` 存进卡，初始值按规则公式计算；为 P8 战斗系统铺路。
- 新卡模板沿用 DEFAULT_CHAR（先跑通流程，模板策略后续细化）。
- 🟢 已确认。

---

## 五、CLI 命令清单

```
game 相关：
  python src/cli.py game new <label>          → 创建新 game，打印 game_id
  python src/cli.py game bind <game_id> <group_id> → 绑定 QQ 群
  python src/cli.py game list                 → 列出所有 game
  python src/cli.py game info <game_id>       → 查看 game 详情

char 相关：
  python src/cli.py char new <game_id> <name> → 创建角色（DEFAULT_CHAR 模板）
  python src/cli.py char list <game_id>       → 列出团内所有角色
  python src/cli.py char show <game_id> <name>→ 查看角色详情
```

- `.st`/`.rc` 链路改为按 `game_id` 读写角色卡。
- 🟢 已确认。

## 六、MCP 工具更新

所有 6 个 MCP tool 均接受 `game_id` 参数（允许 `null`）：

| tool | 新增参数 | 说明 |
|------|---------|------|
| `roll_dice` | `game_id` | `.rc`/`.st` 需要角色卡上下文 |
| `query_rule` | `game_id` | 不同 game 可使用不同规则版本 |
| `get_weapon` | `game_id` | 同上 |
| `get_monster` | `game_id` | 同上 |
| `get_spell` | `game_id` | 同上 |
| `get_skill` | `game_id` | 同上 |
| `game_create` | — | KP 在群内建团 |
| `game_list` | — | 列出所有团 |
| `game_info` | `game_id` | 查看团元数据 |
| `game_bind` | `game_id`, `group_id` | 绑定 QQ 群 |
| `char_create` | `game_id`, `name` | 添加调查员 |
| `char_list` | `game_id` | 列出团内角色 |
| `char_show` | `game_id`, `name` | 查看角色卡详情 |
| `char_update` | `game_id`, `name`, `values` | 更新角色卡属性/技能 |
| `version_list` | — | 列出可用规则版本 |
| `version_info` | `version_id` | 查看版本详情 |

所有 tool 的 `game_id` 参数允许 `null`（尚未建团时使用默认规则版本）。`rebuild_index` 唯一不暴露给 LLM。

- `game_id` 为 `null` 时使用默认规则版本（v1.0），代表尚未创建 game。
- 🟢 已确认。

## 七、Pan-manifest 联动更新（⚠️ 待确认）

Pan session 的 game_id 从哪来？

**方案**：Pan 的 session metadata 存 `game_id`。群首次使用 RuleWhisper 时，由 CLI 手动创建 game 并绑定 group_id；Pan 通过 group_id 查 game_id 存入 session。后续 MCP tool 调用从 session 取 game_id 传入。

`manifest.json` 的 `mcp_servers` 不需要改——game_id 是 MCP 工具参数，不是 Server 启动参数。

**问题**：manifest 是否需要增加 `game_bind_command`（如 `.game bind <id>` 的声明）让 Pan 的 command_routes 能路由到 RuleWhisper CLI？

---

## 八、决议清单

| # | 问题 | 状态 |
|---|------|------|
| 1 | 目录结构 + game.json 字段 | ✅ |
| 2 | game 创建方式（先 CLI 手动） | ✅ |
| 3 | game_id 传参方式（MCP 工具参数） | ✅ |
| 4 | 角色卡 schema（加 hp/mp/luck） | ✅ |
| 5 | 新卡模板（DEFAULT_CHAR 先跑通） | ✅ |
| 6 | CLI 命令清单 | ✅ |
| 7 | 所有 MCP tool 接受 game_id（允许 null） | ✅ |
| 8 | manifest 不改 | ✅ |

---

*创建：2026-07-22 · 状态：已确认，待实现*


---

## 九、实施计划与关键注意点

### 9.1 实施顺序

**第 1 步：创建 `game/` 基础设施**
- 新增 `src/game/__init__.py`（game 管理逻辑）
- 新增 `src/game/character_store.py`（角色卡 CRUD）
- 不需要 new 目录——game 目录在首次 `game new` 时自动创建

**第 2 步：实现 CLI 命令**
- 在 `src/cli.py` 增加 `game` 和 `char` 两个子命令
- `cmd_game(args)` → 解析 `new|list|info|bind`
- `cmd_char(args)` → 解析 `new|list|show`

**第 3 步：改造 character.py**
- `character.py` 从全局单例改为接受 `game_id` + `char_name` 参数
- `set_attr(game_id, char_name, attr, value)` 读 `game/{game_id}/characters/{char_name}.json`
- `get_attr`/`set_skill`/`set_san` 同理
- 保留向后兼容：`game_id=None` 时回退到原 `data/character.json` 行为

**第 4 步：更新 MCP Server**
- `src/server/mcp.py` 的 6 个 tool 全部增加 `game_id: str | None = None` 参数
- `roll_dice` 传入 `game_id` 给 resolver（resolver 内部用 `character.set_attr(game_id, ...)`）
- `get_weapon`/`get_monster`/`get_spell`/`get_skill`→`query_rule` 用 `game_id` 查 game.json 的 `mode` → 决定规则版本

**第 5 步：更新 HTTP API**
- `src/server/__init__.py` 的端点增加可选 `game_id` 参数
- `/api/dice`、`/api/query`、`/api/weapon|monster|spell|skill/{name}` 的请求体/query param 加 `game_id`（可选）

### 9.2 关键注意点

#### ⚠️ game_id 与 resolver 的耦合点

`resolver.py` 的 `_resolve_value` 调用 `character.get_skill()` / `character.get_attr()`。

**改造方式**：不要改 resolver 的签名（保持 `resolve(cmd: DiceCommand) -> DiceResult`）。在调用 resolver 之前，先用 `game_id` 设置 `character` 模块的当前上下文。

建议：`character.py` 新增 `set_current(game_id, char_name)` → 后续所有 `get_attr`/`set_skill` 等操作自动走该上下文。这样 resolver 内部代码无需改动。

```
# 调用方（MCP/CLI/HTTP API）
character.set_current(game_id, "哈维")
result = resolver.run(".rc 侦查 60")
```

#### ⚠️ 规则版本切换

`structured_query.query_weapons` 等函数已接受 `version` 参数——但当前 `version` = 版本 ID（如 `v1.0`），不是 `game_id`。

**中间层**：新增 `src/game/version.py`，提供 `get_mode(game_id) -> str`：
```python
def get_mode(game_id: str | None) -> str:
    if game_id is None:
        return versioning.get_default_version() or "v1.0"
    game_json = load_game(game_id)
    mode = game_json.get("mode", "coc7th")
    return mode_to_version(mode)  # "coc7th" → "v1.0"
```

#### ⚠️ game_id 为 null 的降级

所有接受 `game_id` 的函数必须处理 `None`：
- `get_mode(None)` → 默认版本 v1.0
- `character.set_current(None, ...)` → 使用原 `data/character.json` 单例
- 这使得未创建 game 的场景仍然可用，向后兼容

#### ⚠️ .gitignore

`game/` 目录应加入 `.gitignore`——角色卡数据是用户运行时数据，不应提交到仓库。

#### ⚠️ manifest.json 不变

`pan_plugin/manifest.json` 的 `mcp_servers` 不需要加 `--game-id`——game_id 已经是 MCP 工具参数，Pan session 调 tool 时动态传入，不在 spawn 时确定。

### 9.3 验证方式

```bash
# CLI 测试
python src/cli.py game new "测试团"              # → 打印 game_id
python src/cli.py game list                      # → 列出，含刚创建的
python src/cli.py char new <game_id> "哈维"      # → 创建角色卡
python src/cli.py char list <game_id>             # → 列出卡
python src/cli.py dice ".st 侦查 60"              # → 设置（走 game_id 上下文）
python src/cli.py dice ".rc 侦查"                 # → 检定（读 game_id 下卡）

# MCP 测试
python -c "import asyncio; import src.server.mcp as m; print(asyncio.run(m.mcp.list_tools()))"
# → 确认 6 个 tool 都有 game_id 参数

# HTTP 测试
curl http://127.0.0.1:9731/api/health
curl -X POST http://127.0.0.1:9731/api/dice -H 'Content-Type:application/json'      -d '{"text":".rc 侦查 60","game_id":"<game_id>"}'
```

### 9.4 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/game/__init__.py` | 新建 | game 管理模块（创建/列出/绑定 group_id） |
| `src/game/character_store.py` | 新建 | 角色卡 CRUD（读写 `game/{id}/characters/`） |
| `src/game/version.py` | 新建 | game_id → 规则版本查询 |
| `src/dice/character.py` | 改造 | 支持 `set_current(game_id, name)` 上下文 |
| `src/dice/resolver.py` | 不改 | 继续用 character 模块当前上下文 |
| `src/cli.py` | 增加 | `game`/`char` 子命令 |
| `src/server/__init__.py` | 改造 | 端点增加可选 `game_id` |
| `src/server/mcp.py` | 改造 | 6 个 tool 增加可选 `game_id` |
| `.gitignore` | 增加 | `game/` |
| `docs/game-layer-设计方案.md` | 本文件 | 设计文档 |

---

*创建：2026-07-22 · 状态：方案已确认，待实现（本文件即为实现手册）*
