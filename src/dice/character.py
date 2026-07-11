#!/usr/bin/env python3
"""角色卡 (character card)。

提供当前调查员（默认「哈维」）的属性 / 技能 / SAN 存取，
并能在技能未写卡时回退到规则书基础值 (data/skills.json)。

数据会持久化到 data/character.json，以便 .st 设定的值跨会话保留。
"""
from __future__ import annotations

import json
import os
from typing import Optional

# data/ 位于项目根目录
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CHAR_PATH = os.path.join(_ROOT, "data", "character.json")
_SKILLS_PATH = os.path.join(_ROOT, "data", "skills.json")

DEFAULT_CHAR = {
    "name": "哈维",
    "attributes": {
        "力量": 65, "体质": 60, "敏捷": 55, "外貌": 50,
        "智力": 75, "意志": 70, "教育": 70, "幸运": 60,
        "体力": 60, "体型": 65,
    },
    "skills": {
        "侦查": 55, "图书馆使用": 25, "聆听": 40, "心理学": 41,
        "斗殴": 25, "手枪": 20, "急救": 30, "克苏鲁神话": 0,
    },
    "san": 60,
}

_char: Optional[dict] = None
_skill_base: Optional[dict] = None


def get_character() -> dict:
    global _char
    if _char is None:
        _char = _load()
    return _char


def _load() -> dict:
    try:
        with open(_CHAR_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # 与默认结构合并，保证新字段存在
        merged = dict(DEFAULT_CHAR)
        merged.update(data)
        for key in ("attributes", "skills"):
            merged[key] = {**DEFAULT_CHAR.get(key, {}), **data.get(key, {})}
        return merged
    except FileNotFoundError:
        return dict(DEFAULT_CHAR)


def save() -> None:
    if _char is None:
        return
    with open(_CHAR_PATH, "w", encoding="utf-8") as f:
        json.dump(_char, f, ensure_ascii=False, indent=2)


def name() -> str:
    return get_character().get("name", "调查员")


def set_attr(attr: str, value: int) -> None:
    c = get_character()
    c.setdefault("attributes", {})[attr] = value
    save()


def set_skill(skill: str, value: int) -> None:
    c = get_character()
    c.setdefault("skills", {})[skill] = value
    save()


def get_attr(attr: str) -> Optional[int]:
    return get_character().get("attributes", {}).get(attr)


def get_skill(skill: str) -> Optional[int]:
    return get_character().get("skills", {}).get(skill)


def get_san() -> Optional[int]:
    return get_character().get("san")


def set_san(value: int) -> None:
    get_character()["san"] = value
    save()


def lookup_skill_base(skill: str) -> Optional[int]:
    """回退到规则书技能基础值。"""
    global _skill_base
    if _skill_base is None:
        try:
            with open(_SKILLS_PATH, encoding="utf-8") as f:
                rows = json.load(f)
            _skill_base = {r["名称"]: r.get("基础值") for r in rows if "名称" in r}
        except (FileNotFoundError, json.JSONDecodeError):
            _skill_base = {}
    # 支持前缀匹配（如「侦查」命中「侦查」）
    if skill in _skill_base:
        return _skill_base[skill]
    for k, v in _skill_base.items():
        if k.startswith(skill) or skill.startswith(k):
            return v
    return None
