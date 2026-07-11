# Wiki 数据审查 — 更新版

## 目标

将 `docs/wiki/build.py` 更新为覆盖全部最新数据。

## 当前数据源

| 数据 | 文件 | 条数 | 需更新 |
|------|------|------|--------|
| 武器 | `data/weapons.json` | 98 | ✅ 已有 |
| 怪物 | `data/monsters.json` | 88 | ❌ 新增（神话37 + 神灵30 + 经典7 + 野兽14） |
| 法术 | `data/spells.json` | 109 | ❌ 新增（12个法术模块） |
| 技能 | `data/skills.json` | 84 | ✅ 已有 |
| 规则 | `data/rules/*.json` | 191 (10模块) | ❌ 新增（当前仅有合并视图） |

## 产出

更新 `docs/wiki/build.py`，生成：

```
docs/wiki/
├── index.html           ← 首页导航（更新条目数）
├── weapons.html         ← 已有，确认分类最新
├── monsters.html        ← 新增
├── spells.html          ← 新增
├── skills.html          ← 已有
├── rules.html           ← 新增（按模块分组，附各模块页码范围）
└── rules/
    ├── sanity.html
    ├── combat.html
    ├── magic.html
    ├── chase.html
    ├── game_system.html
    └── ...（全部 10 模块）
```

## 每页必须包含

1. **页面标题** + 数据来源标注（章节名 + 页码范围）
2. **条目数统计**（标题旁）
3. **如果字段不全，标注缺失字段**（但当前数据全量完整，不需要）
4. **搜索/过滤**：输入框实时过滤表格行

## 代码风格

- 与现有 `build.py` 保持一致的 HTML 生成模式
- 怪物页：卡片式布局（属性六维表 + 战斗数据 + 技能法术）
- 法术页：简单表格式（名称/消耗/施法用时）
- 规则页：分类折叠（按模块折叠，每模块下列出 id + 触发 + 效果）

## 注意

- 不新增依赖，纯 Python 生成静态 HTML
- 按模块 commit：`feat(wiki): add monsters page` 等
- 生成后打开文件确认视觉效果
