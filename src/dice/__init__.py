#!/usr/bin/env python3
"""骰子模块包入口。"""

from .parser import DiceCommand, parse, parse_natural
from .resolver import DiceResult, resolve, run, success_level

__all__ = [
    "DiceCommand",
    "DiceResult",
    "parse",
    "parse_natural",
    "resolve",
    "run",
    "success_level",
]
