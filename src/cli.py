#!/usr/bin/env python3
"""RuleWhisper — CLI entry point.

Usage:
  python src/cli.py rule <query>      搜索规则
  python src/cli.py rebuild           重建索引
"""
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine import rule_search, structured_query, router


def _print_json_results(results: list[dict], top_k: int = 8):
    """Print structured query results with key fields."""
    if not results:
        print("未找到匹配结果。")
        return

    for i, entry in enumerate(results[:top_k], 1):
        name = entry.get("名称", entry.get("名称", "?"))
        fields = []
        for key in ["伤害", "STR", "HP", "消耗", "基础值", "射程", "类别"]:
            val = entry.get(key)
            if val is not None:
                fields.append(f"{key}={val}")
        print(f"#{i} {name}")
        if fields:
            print(f"   {'  '.join(fields)}")
        print()


def cmd_rule(args: list[str]):
    if not args:
        print("用法: python src/cli.py rule \"搜索关键词\"")
        return
    query = " ".join(args)
    results = rule_search.search(query, top_k=20)
    output = rule_search.format_results(results)
    print(output)


def cmd_rebuild(args: list[str]):
    rule_search.get_index(force_rebuild=True)
    print("索引已重建。")


def cmd_weapon(args: list[str]):
    if not args:
        print("用法: python src/cli.py weapon \"武器名\"")
        return
    results = structured_query.query_weapons(" ".join(args), top_k=15)
    _print_json_results(results)


def cmd_monster(args: list[str]):
    if not args:
        print("用法: python src/cli.py monster \"怪物名\"")
        return
    results = structured_query.query_monsters(" ".join(args), top_k=15)
    _print_json_results(results)


def cmd_spell(args: list[str]):
    if not args:
        print("用法: python src/cli.py spell \"法术名\"")
        return
    results = structured_query.query_spells(" ".join(args), top_k=15)
    _print_json_results(results)


def cmd_skill(args: list[str]):
    if not args:
        print("用法: python src/cli.py skill \"技能名\"")
        return
    results = structured_query.query_skills(" ".join(args), top_k=15)
    _print_json_results(results)


def cmd_query(args: list[str]):
    """Smart query — auto-routes to the best engine."""
    if not args:
        print("用法: python src/cli.py query \"查询内容\"")
        return
    query = " ".join(args)
    result = router.route_query(query)
    if result["source"] == "structured":
        print(f"[路由: {result['type']} 结构化查询]")
        print()
        _print_json_results(result["results"])
    elif result["source"] == "keyword_search":
        print("[路由: 全文搜索]")
        print()
        print(rule_search.format_results(result["results"]))
    else:
        print("未找到匹配结果。")


COMMANDS = {
    "query": cmd_query,
    "rule": cmd_rule,
    "rebuild": cmd_rebuild,
    "weapon": cmd_weapon,
    "monster": cmd_monster,
    "spell": cmd_spell,
    "skill": cmd_skill,
}


def main():
    if len(sys.argv) < 2:
        print("RuleWhisper — COC 全能跑团助手")
        print()
        print("可用命令:")
        print("  query <关键词>     智能查询（自动路由）")
        print("  rule <关键词>      搜索规则全文")
        print("  weapon <关键词>    查询武器")
        print("  monster <关键词>   查询怪物")
        print("  spell <关键词>     查询法术")
        print("  skill <关键词>     查询技能")
        print("  rebuild            重建文本索引")
        print()
        print("示例:")
        print('  python src/cli.py query "霰弹枪伤害"')
        print('  python src/cli.py query "左轮 .38"')
        print('  python src/cli.py query "深潜者属性"')
        print('  python src/cli.py query "侦查技能"')
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
