#!/usr/bin/env python3
"""COC 全能跑团助手 — CLI entry point.

Usage:
  python src/cli.py rule <query>      搜索规则
  python src/cli.py rebuild           重建索引
"""
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine import rule_search


def cmd_rule(args: list[str]):
    """Search rules. Usage: python cli.py rule "query text" """
    if not args:
        print("用法: python src/cli.py rule \"搜索关键词\"")
        return

    query = " ".join(args)
    results = rule_search.search(query, top_k=20)
    output = rule_search.format_results(results)
    print(output)


def cmd_rebuild(args: list[str]):
    """Rebuild the search index."""
    rule_search.get_index(force_rebuild=True)
    print("索引已重建。")


COMMANDS = {
    "rule": cmd_rule,
    "rebuild": cmd_rebuild,
}


def main():
    if len(sys.argv) < 2:
        print("COC 全能跑团助手")
        print()
        print("可用命令:")
        print("  rule <关键词>   搜索规则")
        print("  rebuild         重建索引")
        print()
        print("示例:")
        print('  python src/cli.py rule "霰弹枪伤害"')
        print('  python src/cli.py rule "理智值归零"')
        print('  python src/cli.py rule "追逐规则"')
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd in COMMANDS:
        COMMANDS[cmd](args)
    else:
        print(f"未知命令: {cmd}")
        print(f"可用命令: {', '.join(COMMANDS.keys())}")


if __name__ == "__main__":
    main()
