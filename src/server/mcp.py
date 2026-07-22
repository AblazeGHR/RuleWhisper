#!/usr/bin/env python3
"""RuleWhisper MCP Server (P1，Pan 联动方案)。

把规则/骰子引擎暴露为 MCP tools，供 Pan 的 LLM Worker（cbc/kimi）通过
--mcp-config 注入后工具调用。不依赖 Pan 任何改造——独立进程即可。

启动：
  python -m src.server.mcp                 # stdio（默认，供 CLI 子进程模式）
  python -m src.server.mcp --transport sse --port 9733   # SSE transport
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.dice import resolver as dice_resolver
from src.engine import router, structured_query

mcp = FastMCP("RuleWhisper")


def _serialize_route(result: dict) -> dict:
    source = result.get("source")
    results = result.get("results", [])
    if source == "keyword_search":
        results = [asdict(e) for e in results]
    return {"source": source, "type": result.get("type"), "results": results}


def _serialize_dice(result) -> dict:
    return {
        "display": result.display,
        "dice_roll": result.dice_roll,
        "success_level": result.success_level,
        "extra_info": result.extra_info,
    }


@mcp.tool()
def query_rule(query: str, top_k: int = 10) -> dict:
    """查询 COC 规则。输入自然语言问题或关键词，返回匹配的规则条目。

    Returns:
        {"source": "structured"|"keyword_search"|null, "type": ..., "results": [...]}
    """
    return _serialize_route(router.route_query(query, top_k=top_k))


@mcp.tool()
def roll_dice(expression: str) -> dict:
    """执行 COC7 骰子检定。表达式如: .rc 1d100 侦察检定, .ra 50, .rb 30, .dam 1d6

    Returns:
        {"display": ..., "dice_roll": ..., "success_level": ..., "extra_info": ...}
    """
    try:
        result = dice_resolver.run(expression)
    except ValueError as e:
        return {"error": f"无效的骰令: {e}"}
    return _serialize_dice(result)


@mcp.tool()
def get_weapon(name: str, top_k: int = 5) -> list[dict]:
    """查询武器数据。返回武器名称、伤害、射程、价格、故障值等。"""
    return structured_query.query_weapons(name, top_k=top_k)


@mcp.tool()
def get_monster(name: str, top_k: int = 5) -> list[dict]:
    """查询怪物数据。返回怪物属性、技能、攻击方式、理智损失等。"""
    return structured_query.query_monsters(name, top_k=top_k)


@mcp.tool()
def get_spell(name: str, top_k: int = 5) -> list[dict]:
    """查询法术数据。返回法术消耗、施法时间、效果描述等。"""
    return structured_query.query_spells(name, top_k=top_k)


@mcp.tool()
def get_skill(name: str, top_k: int = 5) -> list[dict]:
    """查询技能数据。返回技能名称、基础值、关联属性等。"""
    return structured_query.query_skills(name, top_k=top_k)


def main():
    parser = argparse.ArgumentParser(description="RuleWhisper MCP Server")
    parser.add_argument("--transport", default="stdio",
                        choices=["stdio", "sse", "streamable-http"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9733)
    args = parser.parse_args()

    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
