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

**核心原则：你（LLM）亲自阅读原文，亲自确认每一句引用。** 不要写正则或脚本去自动匹配"哪段文字对应哪条规则"——你读，你判断，你摘抄。

**允许的脚本操作：**
- 校验 JSON 格式

**不允许：**
- 用正则/split/findall 从规则书文本中自动提取引用

**步骤：**

1. 用 Read 工具读取 `data/守秘人规则书.txt` 中对应页码的文本
2. 对照每条规则的 `机制效果`，在原文中找到与机制描述一致的关键句子
3. 手动抄写那句原文到 JSON 中（1-3 句话，不摘整段）
4. 直接编辑 `data/rules/sanity.json`，只追加 `原文引用` 字段
5. 校验并 commit

## 注意

- 原文引用应摘录规则书中的关键句子，而非自行归纳
- 长度控制在 1-3 句话，不要摘整段
- 保留原文标点和书写习惯
