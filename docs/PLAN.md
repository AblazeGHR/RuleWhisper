# RuleWhisper — 项目状态与规划
> COC 全能跑团助手。面向开发者。社区版可见 [README.md](../README.md)。

## 当前状态

### 已完成

| 模块 | 产出 | 状态 |
|------|------|------|
| P1 规则搜索引擎 | jieba + TF-IDF 倒排索引，CLI `rule` 命令 | ✅ |
| P2 武器数据 | `weapons.json`，98 武器，12 分类 | ✅ |
| P2 技能数据 | `skills.json`，84 技能 | ✅ |
| P2 查询引擎 | `structured_query.py`，CLI `weapon`/`monster`/`spell`/`skill` | ✅ |
| P3 规则知识库 | `rules/*.json`，191 条，10 模块，字段完整 | ✅ |
| P3 怪物数据 | `monsters.json`，88 只（神话 37+神灵 30+经典 7+野兽 14） | ✅ |
| P3 法术数据 | `spells.json`，109 法术（第十二章全量提取） | ✅ |
| P4 智能路由 | `router.py`，四档分发（结构化 → 全文 → RAG → LLM） | ✅ |
| P5 骰子引擎 | `src/dice/`，parser + resolver + character，COC 7th 全命令 | ✅ |
| P9 规则版本 | `versioning.py`，创建/修改/比较/导出规则版本 | ✅ |
| Wiki 可视化 | `docs/wiki/build.py`，静态 HTML 审查 + README 渲染 | ✅ |
| Wiki 部署 | Cloudflare Worker + Assets，自动部署 | ✅ |

### 数据全景

```
data/
├── weapons.json           (98，全溯源)
├── monsters.json          (88，全溯源)
├── spells.json            (109，全溯源)
├── skills.json            (84，全溯源)
└── rules/                 (191 条，10 模块，全溯源)
```

### 查询能力（CLI 9 个命令）

```
python src/cli.py query   → 智能路由
python src/cli.py rule    → 全文搜索
python src/cli.py weapon  → 武器查询
python src/cli.py monster → 怪物查询
python src/cli.py spell   → 法术查询
python src/cli.py skill   → 技能查询
python src/cli.py dice    → 骰子检定
python src/cli.py version → 规则版本管理
python src/cli.py rebuild → 重建索引
```

## 下一步开发

| 阶段 | 内容 |
|------|------|
| P6 QQ Bot | NapCat HTTP API 接入，群内 `!coc` 规则速查 + `.rc` 骰令 + 自然语言问答 |
| P7 角色卡 | CRUD + Excel 导入解析 + 跑团后导出更新卡 |
| P8 战斗/追逐 | 敏捷排序 → 攻防判定 → 战技/贯穿/伤害结算 → 状态追踪全自动 |
| P10 生成器 | NPC 工厂（年代/职业/难度）、集群生成、场景叙事文本辅助 |

## 工作树

```
D:/project/ai_coc/          → main
D:/project/ai_coc_dice/     → dice-engine   (已合并)
D:/project/ai_coc_router/   → router        (已合并)
D:/project/ai_coc_rules/    → rules-version (已合并)
D:/project/ai_coc_wiki/     → wiki-view     (维护中)
```
