#!/usr/bin/env python3
"""骰子机制引擎 (resolver)。

执行 :class:`DiceCommand` 并返回 :class:`DiceResult`，
实现 COC 7th 的掷骰、技能/属性检定、奖励/惩罚骰、多次检定与理智检定。
纯标准库实现。
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from . import character
from .parser import DiceCommand, parse, parse_natural

_DICE_PATTERN = re.compile(r"\d+d\d+", re.IGNORECASE)

# 成功等级里带「！」的（即成功类）
_SUCCESS_WITH_EXCL = {"大成功", "极难成功", "困难成功", "常规成功"}


@dataclass
class DiceResult:
    dice_roll: int | None = None
    success_level: str = ""
    display: str = ""
    extra_info: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# 骰子表达式求值器
# --------------------------------------------------------------------------- #
class _DiceExpr:
    """递归下降解析并掷骰。支持 + - * / 括号 与 k(取高)/kl(取低)。"""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random
        self.has_keep = False

    def eval(self, expr: str):
        self.toks = self._tokenize(expr)
        self.pos = 0
        val, disp = self._expr()
        return val, disp, self.has_keep

    # ---- 词法 ----
    @staticmethod
    def _tokenize(s: str):
        toks = []
        i, n = 0, len(s)
        dice_re = re.compile(r"^\d*d\d+(?:k\d+)?(?:kl\d+)?", re.IGNORECASE)
        while i < n:
            c = s[i]
            if c.isspace():
                i += 1
                continue
            m = dice_re.match(s, i)
            if m:
                toks.append(("DICE", m.group(0)))
                i = m.end()
                continue
            if c.isdigit():
                j = i
                while j < n and s[j].isdigit():
                    j += 1
                toks.append(("NUM", s[i:j]))
                i = j
                continue
            if c in "+-*/()":
                toks.append(("OP", c))
                i += 1
                continue
            i += 1  # 跳过未知字符
        return toks

    # ---- 语法 ----
    def _peek(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else None

    def _eat(self):
        t = self.toks[self.pos]
        self.pos += 1
        return t

    def _expr(self):
        val, disp = self._term()
        while True:
            t = self._peek()
            if t and t[0] == "OP" and t[1] in "+-":
                self._eat()
                rval, rdisp = self._term()
                if t[1] == "+":
                    val += rval
                    disp = f"{disp} + {rdisp}"
                else:
                    val -= rval
                    disp = f"{disp} - {rdisp}"
            else:
                return val, disp

    def _term(self):
        val, disp = self._factor()
        while True:
            t = self._peek()
            if t and t[0] == "OP" and t[1] in "*/":
                self._eat()
                rval, rdisp = self._factor()
                if t[1] == "*":
                    val *= rval
                    disp = f"{disp} * {rdisp}"
                else:
                    val = val // rval if rval else 0
                    disp = f"{disp} / {rdisp}"
            else:
                return val, disp

    def _factor(self):
        t = self._peek()
        if t is None:
            return 0, "0"
        if t == ("OP", "("):
            self._eat()
            val, disp = self._expr()
            if self._peek() == ("OP", ")"):
                self._eat()
            return val, f"({disp})"
        if t[0] == "NUM":
            self._eat()
            return int(t[1]), t[1]
        if t[0] == "DICE":
            self._eat()
            return self._roll_dice(t[1])
        self._eat()
        return 0, "0"

    def _roll_dice(self, token: str):
        m = re.match(r"^(\d*)d(\d+)(k(\d+))?(kl(\d+))?$", token, re.IGNORECASE)
        if not m:
            return 0, "0"
        count = int(m.group(1)) if m.group(1) else 1
        sides = int(m.group(2))
        keep_high = int(m.group(4)) if m.group(4) else None
        keep_low = int(m.group(6)) if m.group(6) else None
        rolls = [self.rng.randint(1, sides) for _ in range(count)]
        if keep_high is not None:
            self.has_keep = True
            kept = sorted(rolls, reverse=True)[:keep_high]
            disp = "[" + ",".join(str(r) for r in rolls) + "]"
            return sum(kept), disp
        if keep_low is not None:
            self.has_keep = True
            kept = sorted(rolls)[:keep_low]
            disp = "[" + ",".join(str(r) for r in rolls) + "]"
            return sum(kept), disp
        return sum(rolls), "+".join(str(r) for r in rolls)


# --------------------------------------------------------------------------- #
# 成功等级判定 (COC 7th)
# --------------------------------------------------------------------------- #
def success_level(roll: int, skill: int) -> str:
    """依据 COC 7th 规则判定成功等级。"""
    if roll <= 1:                        # 出 01：大成功
        return "大成功"
    if roll >= 100:                      # 出 00：大失败
        return "大失败"
    if skill >= 1 and roll <= skill // 5:
        return "极难成功"
    if skill >= 1 and roll <= skill // 2:
        return "困难成功"
    if roll <= skill:
        return "常规成功"
    if roll <= 95:
        return "失败"
    return "大失败"


def _with_excl(level: str) -> str:
    return level + "！" if level in _SUCCESS_WITH_EXCL else level


# --------------------------------------------------------------------------- #
# 各类命令的解析 / 执行
# --------------------------------------------------------------------------- #
def _resolve_value(cmd: DiceCommand) -> tuple[int, bool]:
    """返回 (目标值, 是否查卡得到)。"""
    looked_up = cmd.skill_value is None
    if not looked_up:
        return cmd.skill_value, False
    if cmd.type == "ra":
        v = character.get_attr(cmd.skill_name)
    else:
        v = character.get_skill(cmd.skill_name)
        if v is None:
            v = character.lookup_skill_base(cmd.skill_name)
    if v is None:
        raise ValueError(f"未找到「{cmd.skill_name}」的数值，请指定或先用 .st 设定")
    return v, True


def resolve_roll(cmd: DiceCommand) -> DiceResult:
    expr = cmd.dice_expr.strip()
    if not expr:
        raise ValueError("缺少掷骰表达式")
    val, disp, has_keep = _DiceExpr().eval(expr)
    label = expr.upper().replace(" ", "")
    text = f"{label} = {disp} → {val}" if has_keep else f"{label} = {disp} = {val}"
    return DiceResult(dice_roll=val, display=text)


def resolve_check(cmd: DiceCommand) -> DiceResult:
    skill, looked_up = _resolve_value(cmd)
    prefix = f"{character.name()} {cmd.skill_name}{skill} → " if looked_up else ""

    if cmd.type in ("rb", "rp"):
        n = 1 + max(cmd.extra_dice, 1)
        rolls = [random.randint(1, 100) for _ in range(n)]
        if cmd.type == "rb":
            chosen = min(rolls)
            note = "奖励骰取优"
        else:
            chosen = max(rolls)
            note = "惩罚骰取劣"
        level = success_level(chosen, skill)
        bonus = "(" + ",".join(str(r) for r in rolls) + ")"
        text = f"{prefix}[{chosen}{bonus}/{skill}] {level}（{note}）"
        return DiceResult(dice_roll=chosen, success_level=level, display=text,
                          extra_info={"rolls": rolls})

    roll = random.randint(1, 100)
    level = success_level(roll, skill)
    text = f"{prefix}[{roll}/{skill}] {_with_excl(level)}"
    return DiceResult(dice_roll=roll, success_level=level, display=text)


def resolve_multi(cmd: DiceCommand) -> DiceResult:
    skill, looked_up = _resolve_value(cmd)
    prefix = f"{character.name()} {cmd.skill_name}{skill} → " if looked_up else ""
    parts = []
    for i in range(1, max(cmd.repeat, 1) + 1):
        roll = random.randint(1, 100)
        level = success_level(roll, skill)
        parts.append(f"#{i} [{roll}/{skill}] {level}")
    text = prefix + " / ".join(parts)
    return DiceResult(display=text)


def _loss_display(expr: str, val: int, disp: str) -> str:
    # 与 prompt 示例保持一致：骰子损失写作「掷1D10=6，损失6」，
    # 纯数值损失写作「损失 0」（成功示例带空格）。
    if _DICE_PATTERN.search(expr):
        return f"掷{expr.upper()}={disp}，损失{val}"
    return f"损失 {val}"


def resolve_san(cmd: DiceCommand) -> DiceResult:
    san = character.get_san()
    if san is None:
        raise ValueError("角色卡缺少 SAN 值，请先用 .st 设定")
    roll = random.randint(1, 100)
    if roll <= san:
        val, disp, _ = _DiceExpr().eval(cmd.san_success_loss)
        text = f"SAN检定 [{roll}/{san}] 成功，{_loss_display(cmd.san_success_loss, val, disp)}"
    else:
        val, disp, _ = _DiceExpr().eval(cmd.san_failure_loss)
        text = f"SAN检定 [{roll}/{san}] 失败，{_loss_display(cmd.san_failure_loss, val, disp)}"
    return DiceResult(dice_roll=roll, display=text, extra_info={"san": san, "loss": val})


def resolve_set(cmd: DiceCommand) -> DiceResult:
    if cmd.skill_value is None:
        raise ValueError("请指定数值，如 .st 力量 65")
    if character.get_attr(cmd.skill_name) is not None or cmd.skill_name in character.DEFAULT_CHAR["attributes"]:
        character.set_attr(cmd.skill_name, cmd.skill_value)
    else:
        character.set_skill(cmd.skill_name, cmd.skill_value)
    text = f"{character.name()} {cmd.skill_name} → {cmd.skill_value}"
    return DiceResult(dice_roll=cmd.skill_value, display=text)


def resolve(cmd: DiceCommand) -> DiceResult:
    """执行命令并返回结果。"""
    if cmd.type in ("r", "dam"):
        return resolve_roll(cmd)
    if cmd.type in ("rc", "ra", "rb", "rp"):
        return resolve_check(cmd)
    if cmd.type == "rs":
        return resolve_multi(cmd)
    if cmd.type == "sc":
        return resolve_san(cmd)
    if cmd.type == "st":
        return resolve_set(cmd)
    raise ValueError(f"不支持的命令类型: {cmd.type}")


def run(text: str) -> DiceResult:
    """一行入口：解析（失败回退自然语言）并执行。"""
    try:
        cmd = parse(text)
    except ValueError:
        cmd = parse_natural(text)
    return resolve(cmd)
