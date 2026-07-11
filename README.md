# Hy3 提取任务（工作树 d:/project/ai_coc_hy3）

## 提取原则

**不用 Python 脚本/正则提取。** 用 Read 工具直接读取文本，理解后输出 JSON。
（已有正则提取的数据存在截断、遗漏等问题，证明脚本不可靠。）

## 任务列表（按顺序执行）

### 1. prompt2.md — 理智模块字段补全
只补字段、不增规则。15 条规则缺判定流程/相关检定/症状表。

### 2. prompt3.md — 法术数据提取
第十二章全部法术，当前仅有 24 条联络/请神术，目标 50+。

---

## 已完成（可跳过）

### prompt.md — 怪物数据提取
✅ 88 只怪物已提取完毕（37神话生物 + 30神话神灵 + 7经典妖魔 + 14野兽）

---

## 工具

合并脚本（所有任务通用）：
```python
import json
base = json.load(open('data/<target>.json', encoding='utf-8'))
new  = json.load(open('_temp.json', encoding='utf-8'))
ids  = [x['id'] for x in base]
merged = base + [x for x in new if x['id'] not in ids]
json.dump(merged, open('data/<target>.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
```

校验：
```python
import json; json.load(open('data/<target>.json', encoding='utf-8'))
```
