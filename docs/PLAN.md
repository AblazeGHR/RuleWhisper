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
| P3 规则知识库 | `rules/*.json`，191 条，10 模块，全模块字段完整 | ✅ |
| P3 怪物数据 | `monsters.json`，88 只（神话 37+神灵 30+经典 7+野兽 14） | ✅ |
| Wiki 可视化 | `docs/wiki/build.py`，静态 HTML 审查工具 | ✅ |

### 进行中（hy3 自动提取）

| 任务 | 说明 | 分支 |
|------|------|------|
| prompt3 — 法术提取 | 第十二章 50+ 法术 | `hy3-monsters` |
| prompt4 — 原文引用补全 | sanity.json 10 条 | `hy3-monsters` |

### 工作树

```
D:/project/ai_coc/        → main
D:/project/ai_coc_hy3/    → hy3-monsters (prompt3/prompt4)
D:/project/ai_coc_wiki/   → wiki-view (审查工具)
```

## 数据层架构

```
data/
├── 守秘人规则书.txt
├── weapons.json          (98)
├── monsters.json         (88)
├── spells.json           (24)          ← hy3 补全中
├── skills.json           (84)
└── rules/                (191 条，10 模块)
    ├── build.py          # 编译 → rules.json
    ├── sanity.json       # 理智 (29) ✅
    ├── combat.json       # 战斗 (42) ✅
    ├── magic.json        # 魔法 (20) ✅
    ├── chase.json        # 追逐 (30) ✅
    ├── game_system.json  # 游戏系统 (20) ✅
    └── ...
```

## 下一步开发

### 当前：数据收尾

1. prompt3 — hy3 提取法术（第十二章 50+ 条）
2. prompt4 — hy3 补 sanity 原文引用（10 条）
3. 合并 hy3 → main，清理工作树

### 接下来：Router + RAG（P4）

统一查询调度层，四档分发：

```
用户输入
    │
    ▼
┌─────────────┐   规则匹配 → weapon/monster/spell/skill 结构化查询
│ 规则匹配     │
└──────┬──────┘
       │ 未命中
       ▼
┌─────────────┐   jieba + TF-IDF → 返回规则段落
│ 全文搜索     │
└──────┬──────┘
       │ 相关性 < 阈值
       ▼
┌─────────────┐   chromadb + bge-small-zh → 语义最近邻
│ RAG 检索     │
└──────┬──────┘
       │ 仍无
       ▼
┌─────────────┐   LLM 理解自然语言意图
│ LLM 兜底     │
└─────────────┘
```

技术栈：`chromadb` + `BAAI/bge-small-zh-v1.5`（本地 embedding）

### 远期路线

| 阶段 | 内容 |
|------|------|
| P5 骰子引擎 | `.rc`/`.ra`/`.rb`/`.rp`/`.sc`/`.dam`，成功等级自动判定，兼容塔骰/豹骰命令 |
| P6 QQ Bot | NapCat HTTP API 接入，群内 `!coc` 规则速查 + `.rc` 骰令 + 自然语言问答 |
| P7 角色卡 | CRUD + Excel 导入解析 + 跑团后导出更新卡 |
| P8 战斗/追逐 | 敏捷排序 → 攻防判定 → 战技/贯穿/伤害结算 → 状态追踪全自动 |
| P9 规则派生 | 版本管理：创建/继承/比较/导出，v1.0 锁只读 |
| P10 生成器 | NPC 工厂（年代/职业/难度）、集群生成、场景叙事文本辅助 |
