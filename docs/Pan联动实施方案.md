# RuleWhisper → Pan 联动实施方案

> 出发点：RuleWhisper 不再"自己造所有轮子"，而是成为 Pan 生态的工具提供方。通过 Pan 的 QQ Bot 通道获得消息入口，通过 Pan 管理的 CLI Worker 获得 LLM 推理能力，自身聚焦把 COC 规则/骰子/角色卡的领域能力做好、暴露好。

---

## 一、为什么要跟 Pan 联动

### 1.1 RuleWhisper 目前缺什么

| 能力 | 原 PLAN | 问题 |
|------|---------|------|
| QQ Bot | P6：自建 NapCat HTTP 接入 | 需另起 NoneBot2/NapCat 进程，自维护 bot 生命周期 |
| LLM 接入 | P4 留空、P6 自然语言问答 | 需自建 provider 抽象、密钥管理、prompt 工程、RAG 管线 |
| 用户入口 | CLI only（`python src/cli.py ...`） | 不适合群内使用 |

### 1.2 Pan 已经有这些

- **QQ Bot 通道**：NoneBot2 + NapCat，已跑通群聊 at、私聊，有 HTTP/WS 桥接。
- **Worker 管理**：cbc/kimi CLI 子进程，可 spawn、发任务、轮询结果、resume。
- **Dashboard**：Web UI 可观察 Worker 状态、历史、流式输出。

### 1.3 联动策略

```
RuleWhisper（你专注做的事）
  ├── HTTP API 层     → 给 Pan QQ Bot 用（确定性指令）
  ├── MCP Server      → 给 Pan Worker 用（LLM 工具调用）
  └── 引擎（不变）     → 规则检索 / 骰子 / 结构化查询

Pan（你已经有的）
  ├── QQ Bot 通道     → 消息入口，群内 at bot 触发
  ├── Worker 管理     → spawn LLM agent，发送任务，取回结果
  └── Dashboard       → 观察跑团 session 的 LLM 行为
```

**RuleWhisper 不再实现自己的 QQ Bot 和 LLM provider 抽象。** P6 的 "NapCat HTTP" 目标由 Pan 的 QQ Bot + 本方案的两层暴露（HTTP API + MCP）替代。

---

## 二、实施计划总览

| 阶段 | 内容 | 改动量 | 依赖 Pan 的状态 |
|------|------|--------|----------------|
| P0 | HTTP API 层（RuleWhisper 本体改造） | ~150 行 | 无 |
| P1 | MCP Server（工具暴露） | ~120 行 | 无 |
| P2 | Pan 端 MCP 透传（配合 Pan 改造） | ~0 行（在 Pan 侧） | Pan 完成 MCP 透传改造 |
| P3 | 联调：QQ 群内跑团全链路 | ~50 行 | Pan QQ 命令路由 + profile |

**本方案文档涵盖 P0、P1、P3**；P2 在 Pan 项目侧实施（参见 `Pan/docs/plans&overviews/RuleWhisper联动与框架优化建议.md`）。

---

## 三、P0：HTTP API 层

### 3.1 设计

新增 `src/server.py`，用 FastAPI 把现有 CLI 命令包装成 REST 接口。**不重写逻辑，只是薄封装**——直接 import `src.engine` 的函数。

新增依赖：`fastapi`、`uvicorn`，追加到 `requirements.txt` 取消注释（替换 `aiohttp` 占位为实际依赖）。

### 3.2 端点

| 端点 | 方法 | 入参 | 出参 | 映射到 |
|------|------|------|------|--------|
| `/api/query` | POST | `{"text": "短剑伤害"}` | `{"hits": [...], "source": "structured"}` | `router.route()` |
| `/api/dice` | POST | `{"text": ".rc 1d100"}` | `{"formula": "1d100", "result": 42}` | `dice.parser` + `dice.resolver` |
| `/api/weapon/{name}` | GET | path param | weapon JSON | `structured_query.query_weapon()` |
| `/api/monster/{name}` | GET | path param | monster JSON | `structured_query.query_monster()` |
| `/api/spell/{name}` | GET | path param | spell JSON | `structured_query.query_spell()` |
| `/api/skill/{name}` | GET | path param | skill JSON | `structured_query.query_skill()` |
| `/api/rule/{id}` | GET | path param | rule JSON | `rule_search` by ID |
| `/api/health` | GET | — | `{"status": "ok"}` | — |

### 3.3 核心代码结构（`src/server.py`）

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.engine.router import route
from src.dice.parser import parse
from src.dice.resolver import resolve
from src.engine.structured_query import query_weapon, query_monster, query_spell, query_skill

app = FastAPI(title="RuleWhisper API")

class QueryRequest(BaseModel):
    text: str

@app.post("/api/query")
def query(req: QueryRequest):
    return route(req.text)

@app.post("/api/dice")
def dice(req: QueryRequest):
    parsed = parse(req.text)
    if parsed is None:
        raise HTTPException(400, "Invalid dice expression")
    result = resolve(parsed)
    return {"formula": req.text, **result}

# ... GET endpoints 较短，略
```

### 3.4 启动

```bash
# 新增 entry
python -m src.server  # → http://127.0.0.1:9731
```

端口 `9731` 避让 Pan(8767)、NapCat(3001)、NoneBot(8080)，在 `.env.example` 或文档中约定。

### 3.5 对 PAN 的价值

此 API 层建成后，Pan 的 QQ Bot 命令路由（`.rc`、`.coc` 等前缀）就可以直连 RuleWhisper 处理确定性指令——不消耗 LLM token，毫秒级响应。这是 P3 联调的前提。

---

## 四、P1：MCP Server

### 4.1 为什么是 MCP

- cbc/kimi CLI 都是 MCP Client，支持通过 `--mcp-config`（或等价机制）注入外部 MCP Server。
- RuleWhisper 用 [fastmcp](https://github.com/jlowin/fastmcp)（Python MCP SDK）把工具暴露为 MCP tools，LLM agent 就能用 `call_tool("roll_dice", {"text": ".rc 1d100 侦察检定"})` 来调规则引擎。
- **不依赖 Pan 的任何改造**——MCP Server 独立进程，Pan 只是配一下 `--mcp-config` 就能用。但优雅的做法是配合 Pan 的 MCP 透传改造（P2），让 profile 自动注入。

### 4.2 Tools 设计

```python
# src/server/mcp.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RuleWhisper")

@mcp.tool()
def query_rule(query: str) -> dict:
    """查询 COC 规则。输入自然语言问题或关键词，返回匹配的规则条目。"""
    from src.engine.router import route
    return route(query)

@mcp.tool()
def roll_dice(expression: str) -> dict:
    """执行 COC7 骰子检定。表达式如: .rc 1d100 侦察检定, .ra 50, .rb 30, .dam 1d6"""
    from src.dice.parser import parse
    from src.dice.resolver import resolve
    result = parse(expression)
    if result is None:
        return {"error": "Invalid dice expression"}
    return resolve(result)

@mcp.tool()
def get_weapon(name: str) -> dict:
    """查询武器数据。返回武器名称、伤害、射程、价格等。"""
    from src.engine.structured_query import query_weapon
    return query_weapon(name)

@mcp.tool()
def get_monster(name: str) -> dict:
    """查询怪物数据。返回怪物属性、技能、攻击方式等。"""
    from src.engine.structured_query import query_monster
    return query_monster(name)

@mcp.tool()
def get_spell(name: str) -> dict:
    """查询法术数据。返回法术消耗、施法时间、效果描述等。"""
    from src.engine.structured_query import query_spell
    return query_spell(name)

@mcp.tool()
def get_skill(name: str) -> dict:
    """查询技能数据。返回技能名称、基础值、关联属性等。"""
    from src.engine.structured_query import query_skill
    return query_skill(name)
```

### 4.3 独立启动

```bash
python -m src.server.mcp  # stdio transport（默认，供 CLI 调用）
# 或
python -m src.server.mcp --transport sse --port 9733  # SSE transport
```

两种 transport 都支持：stdio 适合 `--mcp-config` 方式是子进程模式（cbc 默认行为）；SSE 适合 HTTP 模式。

### 4.4 依赖更新

```text
# requirements.txt 新增
fastapi
uvicorn
mcp
httpx  # 调用 Pan HTTP API 时用
```

---

## 五、P2：Pan 端 MCP 透传（协同改动）

此阶段在 Pan 侧实施，RuleWhisper 无需改代码。参考文档：`Pan/docs/plans&overviews/RuleWhisper联动与框架优化建议.md` 的"改动一"。

核心变化是 Pan 的 `config.json` 里可以写：

```jsonc
{
  "profiles": {
    "coc-keeper": {
      "adapter": "cbc",
      "model": "deepseek-v4-pro",
      "permission_mode": "bypassPermissions",
      "mcp_servers": [
        {"name": "rulewhisper", "command": "python", "args": ["-m", "src.server.mcp"]}
      ],
      "system_prompt": [
        "你是 COC 守秘人(KP)。",
        "所有规则查询和骰子检定都通过 RuleWhisper 工具进行，绝不自己编数据。"
      ]
    }
  }
}
```

Pan Worker spawn 时自动注入 `--mcp-config`，cbc 启动后就能调 RuleWhisper MCP tools。

---

## 六、P3：联调 —— 完整链路

### 6.1 确定性指令链路（P0 产物）

```
QQ 群消息 ".rc 1d100 侦察检定"
  → Pan NoneBot plugin.py (on_message)
  → 命中前缀路由 ".rc"
  → POST http://127.0.0.1:9731/api/dice {"text": ".rc 1d100 侦察检定"}
  → RuleWhisper dice engine 计算
  → 返回 {"formula": "1d100", "result": 42, "skill": "侦察检定"}
  → Pan QQ Bot 群内回复
```

延迟：HTTP 往返 ~5ms + 骰子计算 ~0ms = 毫秒级，不消耗 LLM token。

### 6.2 自然语言问答链路（P1 产物）

```
QQ 群消息 "短剑的伤害是多少？如果恐怖猎手用短剑捅我，我要怎么闪避？"
  → Pan NoneBot plugin.py (on_message)
  → 未命中前缀路由 → 走 LLM 路径
  → Pan 用 "coc-keeper" profile spawn cbc Worker（绑定 RuleWhisper MCP）
  → Worker 收到任务，LLM 分析需要:
    → call_tool("get_weapon", {"name": "短剑"}) → 返回武器属性
    → call_tool("get_monster", {"name": "恐怖猎手"}) → 返回怪物属性
    → call_tool("query_rule", {"query": "闪避规则"}) → 返回闪避规则
  → LLM 综合以上数据生成回复
  → Pan QQ Bot 群内分段回复
```

延迟：LLM 推理 ~2-5s + MCP tool calls ~各次 ~50ms = 几秒，群内交互可接受。

---

## 七、原有 PLAN 更新

原 `docs/PLAN.md` P6 "QQ Bot NapCat HTTP" 目标做以下调整：

| 原计划 | 新方案 |
|--------|--------|
| 自建 NapCat HTTP 接入 | 不建——用 Pan 现有 QQ Bot |
| 自建 LLM provider 抽象 | 不建——LLM 推理由 Pan Worker 承担 |
| `aiohttp` 依赖 | 替换为 `fastapi + uvicorn + mcp + httpx` |

P6 方向调整为：**RuleWhisper HTTP API + MCP Server，对接 Pan Bot 生态**。功能不变（群内规则速查 + 骰令 + 自然语言问答），实现路径不同。

---

## 八、不改的东西

- **不新增自建 QQ Bot 代码**。NapCat/NoneBot2 的维护成本由 Pan 承担。
- **不动 `src/cli.py`**。CLI 是调试/开发入口，保留不变。server 并行存在。
- **不动 `src/engine/`**（除 router Tier 5 预留）。引擎函数给 HTTP API 和 MCP Server 复用，不需要改。
- **`src/engine/router.py` Tier 5** 暂时不改。LLM 档不放在 RuleWhisper 进程里跑；而是由外部（Pan Worker + MCP）承担。如果未来需要 RuleWhisper 独立运行（无 Pan），可以再回来填 Tier 5 走 RAG + LLM 调用。

---

## 九、端口规划

| 进程 | 端口 | 说明 |
|------|------|------|
| RuleWhisper HTTP API | `9731` | FastAPI（uvicorn） |
| RuleWhisper MCP (SSE) | `9733` | 需 SSE transport 时用，stdio 模式不用端口 |
| Pan Core | `8767` | 已有 |
| Pan QQ Bot (NoneBot) | `8080` | 已有 |
| NapCat | `3001` | 已有 |

---

## 十、实施顺序

```
P0 (RuleWhisper HTTP API)     ← 本阶段可立即开始，0 外部依赖
  │
  ├─→ 可单独测试：curl POST /api/dice
  │
  ├─→ P1 (RuleWhisper MCP Server)    ← 并行开始，独立
  │     │
  │     └─→ 可单独测试：mcp dev 或直接 spawn cbc --mcp-config
  │
  └─→ 等待 Pan P2 (MCP 透传 + QQ 命令路由) 完成后
        │
        └─→ P3 (联调)：QQ 群内完整跑团链路验证
```

---

## 十一、进度追踪与下一阶段（P2 / P3）

### 11.1 进度

| 阶段 | 状态 | 说明 |
|------|------|------|
| P0 HTTP API | ✅ 完成 | `src/server/`，FastAPI，端口 9731；8 个端点全部验证通过 |
| P1 MCP Server | ✅ 完成 | `src/server/mcp.py`，fastmcp，注册 6 个工具；stdio / SSE 均可 |
| 插件声明 | ✅ 完成 | `pan_plugin/manifest.json`，声明 profiles/routes/mcp_servers(coc-keeper model=hy3)；Pan 通过通用 loader 加载 |
| P2 通用 Manifest Loader | ⏳ 待 Pan | Pan 实现 loader 读取 manifest 并合并 profiles/mcp/routes；RuleWhisper 零改动 |
| P3 联调 | ⏳ 待 P2 | QQ 群内跑团全链路验证，依赖 Pan 完成 P2 |

> 提交记录：`feat(P0/P1): 实现 HTTP API 与 MCP Server，对接 Pan 生态`（main，已推送 origin）。

### 11.2 下一阶段行动项

**P2（Pan 侧，RuleWhisper 零改动）**
1. Pan `config.json` 增加 `plugin_manifests` 引用 RuleWhisper 的 `pan_plugin/manifest.json`（一行路径，不含领域字面量）。
2. Pan 实现通用 manifest loader：读取 manifest → 合并 `profiles`/`mcp_servers`/`command_routes` 到全局池。
3. 解析 `${PLUGIN_DIR}` → manifest 所在目录，供 MCP Server 的 `cwd` 使用。

**P3（联调，QQ 群内）**
1. Pan NoneBot 命令路由：前缀 `.rc`/`.ra`/`.rb`/`.rp`/`.rs`/`.sc`/`.dam` → `POST /api/dice`；`.coc`/`.rule`/无前缀自然语言 → 走 LLM（coc-keeper profile，自动调 RuleWhisper MCP）。
2. 确定性链路冒烟：群内发 `.rc 1d100 侦察检定`，应在毫秒级收到 RuleWhisper 计算结果。
3. 自然语言链路冒烟：群内问「短剑伤害多少？恐怖猎手怎么闪避？」，LLM 应调用 `get_weapon`/`get_monster`/`query_rule` 后综合回复。
4. 回归：确认 P0 的 `/api/health` 在联调期间持续返回 `{"status":"ok"}`。

### 11.3 RuleWhisper 侧的后续独立阶段

完成 P2/P3 后，RuleWhisper 仓库按原 `docs/PLAN.md` 继续：
- **P7 角色卡**：CRUD + Excel 导入解析 + 跑团后导出更新卡（当前 `src/dice/character.py` 仅有内存态，需持久化）。
- **P8 战斗/追逐**：敏捷排序 → 攻防判定 → 战技/贯穿/伤害结算 → 状态追踪。
- **P10 生成器**：NPC 工厂、集群生成、场景叙事文本辅助。

---

*创建：2026-07-22 · 关联：`Pan/docs/plans&overviews/RuleWhisper联动与框架优化建议.md`*
