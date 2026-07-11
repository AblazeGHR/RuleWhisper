# P9 — 规则版本管理

## 目标

基于 `data/rules/`、`data/weapons.json`、`data/monsters.json`、`data/spells.json` 实现规则集的版本管理。KP 可以创建房规版本、修改规则、比较差异、导出分享。

## 产出文件

```
src/engine/versioning.py     ← 版本管理核心
data/versions/               ← 各版本数据存储目录
data/versions/v1.0/          ← 默认七版规则（只读基线）
data/versions/v2.0/          ← 第一批房规版本（示例）
```

## 核心功能

### 1. 版本创建

```python
# 从默认规则创建新版本
create_version("v2.0", "我的模组房规", based_on="v1.0")
# → 复制 v1.0 全部数据 → v2.0/
```

### 2. 规则修改

```python
# 修改某条规则
modify_rule("v2.0", "weapons", {"名称": "12号泵动式霰弹枪"}, {"时代": "禁用"})
# → v2.0 的 weapons.json 中更新该条

# 删除某条规则
remove_rule("v2.0", "monsters", {"名称": "修格斯"})
# → v2.0 的 monsters.json 中移除修格斯

# 新增自定义规则
add_rule("v2.0", "weapons", {"名称": "激光步枪", "伤害": "4D10", ...})
```

### 3. 版本切换

```python
# 查询时指定版本
query_weapons("霰弹枪", version="v2.0")
# → v2.0 的结果中不包含被禁用的武器

# 全局切换默认版本
set_default_version("v2.0")
# → 后续所有查询默认使用 v2.0
```

### 4. 版本比较

```python
# 比较两个版本的差异
diff_versions("v1.0", "v2.0")
# → {
#     "weapons": [
#       {"name": "12号泵动式霰弹枪", "change": "modified", "field": "时代", "old": "1920s，现代", "new": "禁用"},
#       {"name": "AK-47", "change": "removed"},
#     ],
#     "monsters": [...]
#   }
```

### 5. 版本导出/导入

```python
# 导出为 JSON 文件
export_version("v2.0", "my_house_rules.json")
# → 单文件，包含所有修改（从 v1.0 继承的部分不重复存储）

# 其他 KP 导入
import_version("my_house_rules.json", as_name="v3.0")
```

## 数据存储

```
data/versions/
├── v1.0/                  ← 默认规则，只读
│   ├── weapons.json
│   ├── monsters.json
│   ├── spells.json
│   ├── skills.json
│   └── rules/
│       └── ... (10 files)
├── v2.0/                  ← 房规版本，仅存差异
│   ├── diff.json          ← {"weapons": [{"名称": "AK", "时代": "禁用"}, ...]}
│   └── meta.json          ← {"name": "我的模组房规", "based_on": "v1.0", ...}
└── index.json             ← 版本列表 [{"id": "v1.0", "name": "七版标准规则", "readonly": true}, ...]
```

## 实现策略

**先做最小可行版本：**
1. 版本创建 — 基于 v1.0 复制（实际不在磁盘复制，用 diff 存储）
2. 单个条目修改 — 只改 diff.json
3. 查询时版本合并 — 加载 v1.0 + v2.0 的 diff，覆盖查询结果
4. 版本比较 — 输出 diff.json 的人类可读版本

**后续扩展（本次可不做）：**
- 导出/导入
- 全局版本切换命令
- 多级继承链（v2 → v3 → v4）

## 注意

- v1.0 数据只读，不允许修改
- diff 增量存储，不重复保存全量数据
- 支持的数据类型：weapons, monsters, spells, skills, rules（各模块）
- 每完成一个功能 commit，格式 `feat(version): xxx`
