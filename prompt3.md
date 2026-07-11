# 法术数据提取

## 任务

现有 `data/spells.json` 仅 24 条（联络/请神术），来自正则提取，覆盖不全。需要从第十二章提取全部法术，重新生成。

## 源文件

- `data/守秘人规则书.txt` — 规则书全文（1.5MB）
- 第十二章 法术：txt 第 206-230 页

## 快速定位命令

```python
with open('data/守秘人规则书.txt', encoding='utf-8') as f:
    data = f.read()
idx = data.find('===== 第 206 页 =====')
idx_end = data.find('===== 第 232 页 =====')
with open('data/ch12_raw.txt', 'w', encoding='utf-8') as f:
    f.write(data[idx:idx_end])
```

## 输出格式

每个法术一条 JSON，参考已有怪物格式：

```json
{
  "id": "grey_binding",
  "名称": "灰色束缚",
  "别名": ["僵尸创建术变体"],
  "消耗": "8点魔法值；1D6点理智值",
  "施法用时": "1小时",
  "效果": "泼洒仪式液体到准备好的尸身上，创建不死仆役",
  "来源章节": "第十二章 法术"
}
```

**字段说明：**
- `id`: 英文标识（拼音或翻译）
- `名称`: 中文名称
- `别名`: 可选，法术的其他称呼
- `消耗`: 魔法值/理智值/POW 消耗
- `施法用时`: 施法所需时间
- `效果`: 法术效果简述（1-3句话）
- `来源章节`: 固定为 "第十二章 法术"
- `特殊说明`: 可选，如 "KP 决定特殊原料" 等

## 执行方法

**核心原则：你（LLM）是人类，不是脚本。** 你必须亲自阅读文本、理解每一个法术的内容、手动写出 JSON。不要试图让 Python 替你理解文本——正则做不到这件事，旧的 spells.json（24 条，大量遗漏）就是正则失败的证明。

**允许使用脚本的地方（仅限以下）：**
- 从完整规则书中截取第十二章文本 → 上面那行 Python（一次执行）
- 将你写好的临时 JSON 合并到 `data/spells.json` → 下面那行 Python
- 校验 JSON 格式 → `python -c`

**禁止使用脚本的地方：**
- 绝对不要写正则或 Python 程序从文本中自动提取法术
- 不要试图用 split/regex/findall 解析法术名、消耗、效果

**正确流程：**

1. 生成 `data/ch12_raw.txt`（一行 Python，仅文件截取）
2. **用 Read 工具读取文本片段**（每次 250-400 行），你亲自阅读法术语的段落
3. 你亲自判断每条法术的名称、消耗、施法用时和效果，手动写出 JSON 到临时文件
4. 每组法术写出后，用 Python 去重合并回 `data/spells.json`
5. 每完成一个法术类别 commit 一次
6. 校验：`python -c "import json;json.load(open('data/spells.json','utf-8'))"`

合并脚本同怪物提取：
```python
import json
base = json.load(open('data/spells.json', encoding='utf-8'))
new  = json.load(open('_temp.json', encoding='utf-8'))
ids  = [x['id'] for x in base]
merged = base + [x for x in new if x['id'] not in ids]
json.dump(merged, open('data/spells.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
```

## 注意事项

- 法术按字母排列，有多种别名
- 有些法术只有消耗没有效果描述（说明在其他处）
- 联络/请神/召唤类法术已在旧 JSON 中，但数据格式不统一，应全部用新格式重做
- 旧 `data/spells.json` 中的 24 条可以不去重（新格式会覆盖）
- 法术变体（僵尸创建术的深层版等）应作为独立条目
- 第十二章前半是魔法系统说明，后半（法术列表）才是数据
- 保留原文书写，不转换标点或精简化
