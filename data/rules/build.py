#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3 规则模块化构建脚本。

职责：
1. 为 data/rules.json 中每条规则补上 `模块` 字段（按章节归类，少数规则覆盖到幕间成长模块）。
2. 按模块拆分输出到 data/rules/<module_key>.json。
3. 保留合并视图 data/rules.json 作为单一事实来源（single source of truth）。

模块划分（字段值 / 文件名 key）：
    创建调查员  character_creation   第三章
    技能        skills              第四章
    游戏系统    game_system         第五章（核心检定系统）
    幕间成长    interlude           第五章中"幕间/技能增长/背景演变"相关规则
    战斗        combat              第六章
    追逐        chase               第七章
    理智        sanity             第八章
    魔法        magic              第九章
    主持游戏    keeper             第十章
    附录        appendix           第十六章

运行：python data/rules/build.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # data/
RULES = os.path.join(ROOT, "rules.json")

# 章节名 -> (模块字段值, 文件名key)
CHAPTER_MODULE = {
    "第三章 创建调查员": ("创建调查员", "character_creation"),
    "第四章 技能": ("技能", "skills"),
    "第五章 游戏系统": ("游戏系统", "game_system"),
    "第六章 战斗": ("战斗", "combat"),
    "第七章 追逐": ("追逐", "chase"),
    "第八章 理智": ("理智", "sanity"),
    "第九章 魔法": ("魔法", "magic"),
    "第十章 主持游戏": ("主持游戏", "keeper"),
    "第十六章 附录": ("附录", "appendix"),
}

# 少数 Ch5 规则属于"幕间成长"而非核心"游戏系统"
INTERLUDE_OVERRIDE = {
    "interlude_growth",
    "modify_background",
    "interlude_employment_cr",
    "training",
}


def assign_module(rule):
    ch = rule.get("章节", "")
    if rule.get("id") in INTERLUDE_OVERRIDE:
        return ("幕间成长", "interlude")
    if ch in CHAPTER_MODULE:
        return CHAPTER_MODULE[ch]
    # 兜底：已有模块字段则沿用
    if rule.get("模块"):
        return (rule["模块"], None)
    return ("未分类", "uncategorized")


def main():
    rules = json.load(open(RULES, encoding="utf-8"))
    buckets = {}
    for r in rules:
        mod_val, mod_key = assign_module(r)
        r["模块"] = mod_val
        buckets.setdefault(mod_key or _key_from_val(mod_val), []).append(r)

    # 回写合并视图（带模块字段）
    json.dump(rules, open(RULES, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # 拆分输出
    summary = []
    for key, items in sorted(buckets.items()):
        out = os.path.join(HERE, f"{key}.json")
        json.dump(items, open(out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        summary.append((key, len(items)))

    print("rules.json total:", len(rules))
    for k, n in summary:
        print(f"  {k:20s} {n}")


def _key_from_val(val):
    for _, (v, k) in CHAPTER_MODULE.items():
        if v == val:
            return k
    return "uncategorized"


if __name__ == "__main__":
    main()
