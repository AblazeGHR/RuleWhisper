# COC 全能跑团助手 — 项目状态与规划

> 本文档面向开发者，记录当前进度、数据架构和未来路线。

## 当前状态

### 已完成

| 模块 | 产出 | 状态 |
|------|------|------|
| **P1 规则搜索引擎** | `src/engine/indexer.py` / `rule_search.py`，jieba 分词 + TF-IDF 倒排索引，CLI `rule` 命令 | ✅ |
| **P2 武器数据** | `data/weapons.json`，98 武器，12 分类，完整覆盖规则书附录 | ✅ |
| **P2 查询引擎** | `src/engine/structured_query.py`，CLI `weapon`/`monster`/`spell`/`skill` 命令 | ✅ |
| **P2 技能数据** | `data/skills.json`，84 技能，名称 + 基础值 | ✅ |
| **P3 规则数据** | `data/rules.json`（83 条）+ `data/rules/*.json`（191 条，10 模块） | ✅ |
| **P3 怪物数据** | `data/monsters.json`，88 怪物（神话生物 37 + 神灵 30 + 经典 7 + 野兽 14），hy3 提取 | ✅ |
| **Wiki 可视化** | `docs/wiki/build.py`，静态 HTML 生成，可审查全部数据 | ✅ |

### 进行中

| 模块 | 内容 | 分支 |
|------|------|------|
| **理智字段补全** | 15 条规则缺判定流程/相关检定，需 Read 补字段 | `hy3-monsters` (prompt2.md) |
| **法术数据提取** | 第十二章 50+ 法术，当前仅 24 条联络/请神术 | `hy3-monsters` (prompt3.md) |

### 数据层架构

```
data/
├── 守秘人规则书.txt              # 原始 txt (1.5MB, 400页)
├── weapons.json                  # 武器 (98, P2)
├── monsters.json                 # 怪物 (88, P3/hy3)
├── spells.json                   # 法术 (24, P2 — 待 P3/hy3 补全)
├── skills.json                   # 技能 (84, P2)
├── rules.json                    # 规则合并视图 (83条)
└── rules/                        # 规则模块化源文件 (191条, 10模块)
    ├── build.py                  # 模块 → 合并视图 编译脚本
    ├── sanity.json               # 理智 (29) — 待补字段
    ├── combat.json               # 战斗 (42)
    ├── magic.json                # 魔法 (20)
    ├── chase.json                # 追逐 (30)
    ├── game_system.json          # 游戏系统 (20)
    ├── character_creation.json   # 创建调查员 (19)
    ├── skills.json               # 技能规则 (10)
    ├── interlude.json            # 幕间成长 (4)
    ├── keeper.json               # 主持游戏 (9)
    └── appendix.json             # 附录 (8)
```

**数据走向：** 模块 JSON（手编/手动校验）→ `build.py` → `rules.json`（查询用）→ 搜索引擎/RAG

### 查询能力

```
python src/cli.py rule "霰弹枪伤害"      → 全文搜索（P1）
python src/cli.py weapon "左轮"         → 武器查询（P2）
python src/cli.py monster "深潜者"      → 怪物查询（P2）
python src/cli.py spell "联络术"        → 法术查询（P2）
python src/cli.py skill "侦查"          → 技能查询（P2）
```

## 未来路线

### P4 — RAG 语义检索
- `chromadb` 本地向量库
- `BAAI/bge-small-zh-v1.5` 中文 embedding
- 规则书全文 + 结构化 JSON 混合检索

### P5 — QQ Bot 接入
- NapCat HTTP API 解耦接入
- Q 群内 `!coc 规则` / `.rc` 骰令

### P6 — 骰子与机制引擎
- COC 7th 完整骰子（奖励骰/惩罚骰/成功等级判定）
- 兼容塔骰/豹骰命令格式

### P7 — 生成器引擎
- NPC 工厂（年代/职业/难度）
- 随机遭遇表
- 线索/场景生成器

### P8 — 自定义规则
- 基于 `data/rules/` 模块化 JSON，支持派生子规则
- 武器/怪物/法术的自定义修改与版本管理
