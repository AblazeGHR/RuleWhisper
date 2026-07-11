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

from src.dice import resolver as dice_resolver



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
    from src.engine import rule_search
    query = " ".join(args)
    results = rule_search.search(query, top_k=20)
    output = rule_search.format_results(results)
    print(output)


def cmd_rebuild(args: list[str]):
    from src.engine import rule_search
    rule_search.get_index(force_rebuild=True)
    print("索引已重建。")


def cmd_weapon(args: list[str]):
    if not args:
        print("用法: python src/cli.py weapon \"武器名\"")
        return
    from src.engine import structured_query
    results = structured_query.query_weapons(" ".join(args), top_k=15)
    _print_json_results(results)


def cmd_monster(args: list[str]):
    if not args:
        print("用法: python src/cli.py monster \"怪物名\"")
        return
    from src.engine import structured_query
    results = structured_query.query_monsters(" ".join(args), top_k=15)
    _print_json_results(results)


def cmd_spell(args: list[str]):
    if not args:
        print("用法: python src/cli.py spell \"法术名\"")
        return
    from src.engine import structured_query
    results = structured_query.query_spells(" ".join(args), top_k=15)
    _print_json_results(results)


def cmd_skill(args: list[str]):
    if not args:
        print("用法: python src/cli.py skill \"技能名\"")
        return
    from src.engine import structured_query
    results = structured_query.query_skills(" ".join(args), top_k=15)
    _print_json_results(results)


def cmd_dice(args: list[str]):
    if not args:
        print("用法: python src/cli.py dice \".rc 侦查 55\"")
        return
    text = " ".join(args)
    try:
        result = dice_resolver.run(text)
    except ValueError as e:
        print(f"错误: {e}")
        return
    print(result.display)


COMMANDS = {
    "rule": cmd_rule,
    "rebuild": cmd_rebuild,
    "weapon": cmd_weapon,
    "monster": cmd_monster,
    "spell": cmd_spell,
    "skill": cmd_skill,
    "dice": cmd_dice,
}


def main():
    if len(sys.argv) < 2:
        print("RuleWhisper — COC 全能跑团助手")
        print()
        print("可用命令:")
        print("  rule <关键词>     搜索规则全文")
        print("  weapon <关键词>   查询武器")
        print("  monster <关键词>  查询怪物")
        print("  spell <关键词>    查询法术")
        print("  skill <关键词>    查询技能")
        print("  dice <命令>       掷骰 / 检定 (如 \".rc 侦查 55\")")
        print("  rebuild           重建文本索引")
        print()
        print("示例:")
        print('  python src/cli.py rule "霰弹枪伤害"')
        print('  python src/cli.py weapon "左轮"')
        print('  python src/cli.py monster "深潜者"')
        print('  python src/cli.py spell "联络术"')
        print('  python src/cli.py skill "侦查"')
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
