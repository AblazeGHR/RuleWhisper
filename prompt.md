# P4 — Router 调度层

## 目标

统一查询入口，四档智能分发。替代 `cli.py` 的硬编码命令路由。

## 架构

```
用户输入
    │
    ▼
┌─────────────┐   识别 "武器"/"怪物"/"法术"/"技能" 前缀 + 实体名
│ 结构化查询   │   → weapon "左轮" / monster "深潜者" / spell "联络术" / skill "侦查"
└──────┬──────┘
       │ 未命中
       ▼
┌─────────────┐   jieba + TF-IDF 倒排索引 → 返回规则段落（复用 indexer.py）
│ 全文搜索     │
└──────┬──────┘
       │ 相关性 < 阈值（< 30分）
       ▼
┌─────────────┐   chromadb + bge-small-zh → 语义最近邻
│ RAG 检索     │   （本阶段可先跳过，全文搜索已覆盖大部分场景）
└──────┬──────┘
       │ 仍无 或 模糊自然语言
       ▼
┌─────────────┐   LLM 理解意图 → 返回最佳猜测或询问澄清
│ LLM 兜底     │   （本阶段输出空结果即可，不实现 LLM 调用）
└─────────────┘
```

## 产出文件

```
src/engine/router.py         ← 核心路由逻辑
src/cli.py                   ← 调用 router，简化入口
```

## 接口设计

```python
from src.engine.router import route_query

result = route_query("霰弹枪伤害")
# → { "source": "keyword_search", "results": [...paragraphs...] }

result = route_query("左轮 .38")
# → { "source": "structured", "type": "weapon", "results": [{weapon dicts}] }

result = route_query("深潜者属性")
# → { "source": "structured", "type": "monster", "results": [{monster dicts}] }

result = route_query("侦查技能")
# → { "source": "structured", "type": "skill", "results": [{skill dicts}] }
```

## 路由规则

1. 包含武器特征词（"伤害"、"射程"、"码"、"D"）→ 尝试结构化 weapon
2. 包含怪物特征词（"STR"、"HP"、"护甲"、"理智损失"、"深潜者"等实体名）→ 结构化 monster
3. 包含法术特征词（"消耗"、"施法用时"、"术"）→ 结构化 spell
4. 包含 "%" 或 "基础值" → 结构化 skill
5. 以上均不命中 → 全文搜索
6. 全文搜索得分 < 阈值 → 空结果

## 注意

- 不写正则提取脚本，用 Read 理解需求后写代码
- 复用已有的 `structured_query.py` 和 `rule_search.py`
- 先做 1-5 档（结构化 + 全文），6 档 RAG 和 7 档 LLM 可以后加
- 每完成一层，写个测试查询验证
- commit 信息用 `feat(router): xxx` 格式
