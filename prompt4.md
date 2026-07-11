# 理智模块原文引用补全

## 任务

`data/rules/sanity.json` 中 10 条规则缺少 `原文引用` 字段。读取规则书原文，为每条补上与机制效果对应的原文摘录。

## 源文件

`data/守秘人规则书.txt` 第八章 理智，txt 第 130-143 页。

## 缺失条目

| 规则 ID | 页码 | 需要补 |
|---------|------|--------|
| sanity_fail_involuntary_action | 130 | 原文引用 |
| insanity_three_states | 131 | 原文引用 |
| insanity_three_phases | 131 | 原文引用 |
| insanity_bout_duration | 133 | 原文引用 |
| insanity_chronic_latent | 134 | 原文引用 |
| insanity_bout_immediate_symptoms | 133 | 原文引用 |
| insanity_bout_summary | 134 | 原文引用 |
| sanity_loss_examples | 131 | 原文引用 |
| insanity_bout_modifies_background | 132 | 原文引用 |
| sanity_recovery_self_help | 167 | 原文引用 |

## 执行

- 不写脚本，用 Read 工具定位对应页码的文本，找到与 `机制效果` 对应的原文段落
- 直接编辑 `data/rules/sanity.json`，在每条规则末尾追加 `"原文引用": "..."` 字段
- 只追加 `原文引用`，不修改任何已有字段
- Python 校验：`python -c "import json;json.load(open('data/rules/sanity.json','utf-8'))"`
- 完成后 commit

## 注意

- 原文引用应摘录规则书中的关键句子，而非自行归纳
- 长度控制在 1-3 句话，不要摘整段
- 保留原文标点和书写习惯
