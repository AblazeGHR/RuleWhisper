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
| `roll_dice` | `game_id: str | null` | `.rc`/`.st` 需要角色卡上下文 |
| `get_weapon` | `game_id: str | null` | 不同 game 可使用不同规则版本 |
| `get_monster` | `game_id: str | null` | 同上 |
| `get_spell` | `game_id: str | null` | 同上 |
| `get_skill` | `game_id: str | null` | 同上 |
| `query_rule` | `game_id: str | null` | 同上 |

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
