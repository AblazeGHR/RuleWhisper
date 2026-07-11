# 理智模块字段补全

## 任务

`data/rules/sanity.json`（29 条）作为最早提取的章节，部分可选字段缺失。读取第十四章原始文本，补全这些字段。

## 缺失字段汇总

| 规则 ID | 缺失字段 |
|---------|---------|
| sanity_loss_format | 相关检定 |
| sanity_fail_involuntary_action | 相关检定 |
| sanity_fumble | 判定流程、相关检定 |
| max_sanity | 相关检定 |
| insanity_three_states | 相关检定 |
| insanity_three_phases | 相关检定 |
| indefinite_insanity_trigger | 相关检定 |
| permanent_insanity | 判定流程、相关检定 |
| insanity_bout_duration | 相关检定 |
| insanity_chronic_latent | 相关检定 |
| insanity_bout_immediate_symptoms | 判定流程、相关检定、症状表 |
| insanity_bout_summary | 判定流程、相关检定 |
| sanity_loss_examples | 判定流程、参考表 |
| insanity_bout_modifies_background | 判定流程、相关检定 |
| sanity_recovery_self_help | 判定流程 |

## 执行

**重要：不写脚本，用 Read 工具读取文本，直接理解并输出 JSON。**

1. Read `data/ch14_raw.txt` 定位理智相关段落（第 130-143 页区域）
2. 对照每条缺失规则，补全字段值
3. 直接编辑 `data/rules/sanity.json`，不需要重新生成
4. Python 校验：`python -c "import json;json.load(open('data/rules/sanity.json','utf-8'))"`
5. commit

## 注意

- `判定流程` 应为步骤列表（数组），不是长文本
- `相关检定` 应为检定名数组，如 `["智力检定", "体质检定"]`
- `症状表` 应列出具体症状内容（即时症状 10 条 / 恐惧症 / 躁狂症）
- `参考表` 对应 sanity_loss_examples 的理智损失参考值
- 不要修改已有字段值，只追加缺失字段
- 不新增规则，只补全现有 29 条的字段
