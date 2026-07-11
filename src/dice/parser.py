#!/usr/bin/env python3
"""提示词命令解析器 (parser)。

负责把用户输入的骰子命令（及自然语言）解析成结构化的 :class:`DiceCommand`。
纯标准库实现，兼容塔骰 / 豹骰 命令格式。
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class DiceCommand:
    """一条解析后的骰子命令。"""

    type: str                       # rc | ra | rb | rp | rs | sc | r | dam | st
    skill_name: str = ""            # 技能 / 属性名，如 "侦查"
    skill_value: int | None = None  # 检定目标值，缺省时查角色卡
    extra_dice: int = 0             # 奖励/惩罚骰数量 (rb/rp)
    repeat: int = 1                 # 多次检定次数 (rs)
    dice_expr: str = ""             # 纯掷骰表达式 (r / dam)
    san_success_loss: str = ""      # 理智检定：成功时损失表达式 (sc)
    san_failure_loss: str = ""      # 理智检定：失败时损失表达式 (sc)
    raw: str = ""                   # 原始输入


_DICE_TYPES = {"rc", "ra", "rb", "rp", "rs", "sc", "r", "dam", "st"}

# 属性关键字（用于自然语言区分 ra / rc）
_KNOWN_ATTR = {
    "力量", "体质", "敏捷", "外貌", "智力", "意志", "教育",
    "幸运", "体力", "体型", "dex", "str", "con", "siz", "int",
    "pow", "edu", "app", "luck",
}

_DICE_PATTERN = re.compile(r"\d+d\d+", re.IGNORECASE)


def parse(text: str) -> DiceCommand:
    """解析形如 `.rc 侦查 55` 的命令字符串。"""
    if text is None:
        raise ValueError("空命令")
    text = text.strip()
    if not text:
        raise ValueError("空命令")
    # 允许省略前导点号
    if text.startswith("."):
        text = text[1:].strip()

    head, _, rest = text.partition(" ")
    ctype = head.lower()
    rest = rest.strip()
    if ctype not in _DICE_TYPES:
        raise ValueError(f"未知骰子命令: .{ctype}")

    cmd = DiceCommand(type=ctype, raw=text)

    if ctype in ("r", "dam"):
        cmd.dice_expr = rest
    elif ctype == "sc":
        _parse_sc(rest, cmd)
    elif ctype == "rs":
        _parse_rs(rest, cmd)
    elif ctype in ("rc", "ra", "rb", "rp"):
        _parse_check(rest, cmd)
    elif ctype == "st":
        _parse_st(rest, cmd)
    return cmd


def _split_name_value(rest: str):
    """把 `名称 值 [额外骰]` 拆开，返回 (名称, 值, 额外骰)。"""
    parts = rest.split()
    if not parts:
        return "", None, 0
    name = parts[0]
    value = None
    extra = 0
    if len(parts) >= 2:
        try:
            value = int(parts[1])
        except ValueError:
            value = None
    if len(parts) >= 3:
        try:
            extra = int(parts[2])
        except ValueError:
            extra = 0
    return name, value, extra


def _parse_check(rest: str, cmd: DiceCommand) -> None:
    name, value, extra = _split_name_value(rest)
    cmd.skill_name = name
    cmd.skill_value = value
    # 奖励/惩罚骰：缺省 1 颗
    cmd.extra_dice = extra if extra > 0 else 1


def _parse_rs(rest: str, cmd: DiceCommand) -> None:
    # 形如 `3#侦查 55`
    m = re.match(r"^(\d+)\s*#\s*(\S+)\s*(\d+)?", rest)
    if not m:
        raise ValueError(f"无法解析多次检定: {rest!r}")
    cmd.repeat = int(m.group(1))
    cmd.skill_name = m.group(2)
    cmd.skill_value = int(m.group(3)) if m.group(3) else None


def _parse_sc(rest: str, cmd: DiceCommand) -> None:
    # 形如 `0/1d6`  或  `1/1d10`
    if "/" not in rest:
        raise ValueError(f"理智检定格式应为 成功损失/失败损失，如 .sc 0/1d6")
    succ, fail = rest.split("/", 1)
    cmd.san_success_loss = succ.strip()
    cmd.san_failure_loss = fail.strip()


def _parse_st(rest: str, cmd: DiceCommand) -> None:
    name, value, _ = _split_name_value(rest)
    cmd.skill_name = name
    cmd.skill_value = value


def parse_natural(text: str) -> DiceCommand:
    """解析自然语言输入，如 '侦查 55'、'投个 3d6'、'力量检定'。"""
    if text is None:
        raise ValueError("空命令")
    text = text.strip()
    if not text:
        raise ValueError("空命令")

    # 1) 直接含有骰子表达式 -> 纯掷骰
    m = _DICE_PATTERN.search(text)
    if m:
        expr = m.group(0)
        # 若句子里还带 k (取高) 等，尽量抓取后续 keep 修饰
        km = re.search(r"\d+d\d+\s*(k\s*\d+)?", text, re.IGNORECASE)
        return DiceCommand(type="r", dice_expr=km.group(0).replace(" ", "") if km else expr, raw=text)

    # 2) "X检定 [数值]"  -> rc / ra
    m = re.search(r"([一-龥A-Za-z]+)\s*检定\s*(\d+)?", text)
    if m:
        name = m.group(1)
        val = int(m.group(2)) if m.group(2) else None
        ctype = "ra" if name in _KNOWN_ATTR else "rc"
        return DiceCommand(type=ctype, skill_name=name, skill_value=val, raw=text)

    # 3) "伤害 / dam ..."  -> 伤害掷骰
    if "伤害" in text or "dam" in text.lower():
        dm = re.search(r"([\d+dDkK\+\-\*/\(\)\s]+)", text)
        expr = dm.group(1).strip() if dm else ""
        return DiceCommand(type="dam", dice_expr=expr, raw=text)

    # 4) "名称 数值" 或 "名称"  -> rc / ra
    m = re.search(r"([一-龥A-Za-z]+)\s*(\d+)?", text)
    if m:
        name = m.group(1)
        val = int(m.group(2)) if m.group(2) else None
        ctype = "ra" if name in _KNOWN_ATTR else "rc"
        return DiceCommand(type=ctype, skill_name=name, skill_value=val, raw=text)

    # 5) 兜底：当普通命令解析
    return parse(text)
