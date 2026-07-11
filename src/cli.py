#!/usr/bin/env python3
"""RuleWhisper — CLI entry point.

Usage:
  python src/cli.py rule <query>           搜索规则
  python src/cli.py rebuild                重建索引
  python src/cli.py version create <id> <name> 创建版本
"""
import json
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine import rule_search, structured_query, versioning


def _parse_version_flag(args: list[str]) -> tuple[list[str], str | None]:
    """Extract --version <id> from args. Returns (remaining_args, version_id)."""
    if "--version" in args:
        idx = args.index("--version")
        version_id = args[idx + 1] if idx + 1 < len(args) else None
        remaining = args[:idx] + args[idx + 2:]
        return remaining, version_id
    return args, None


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


# ---------------------------------------------------------------------------
# Core commands
# ---------------------------------------------------------------------------

def cmd_rule(args: list[str]):
    if not args:
        print("用法: python src/cli.py rule \"搜索关键词\"")
        return
    args, _ = _parse_version_flag(args)
    query = " ".join(args)
    results = rule_search.search(query, top_k=20)
    output = rule_search.format_results(results)
    print(output)


def cmd_rebuild(args: list[str]):
    rule_search.get_index(force_rebuild=True)
    print("索引已重建。")


def cmd_weapon(args: list[str]):
    if not args:
        print("用法: python src/cli.py weapon \"武器名\" [--version <id>]")
        return
    args, version = _parse_version_flag(args)
    results = structured_query.query_weapons(" ".join(args), top_k=15, version=version)
    _print_json_results(results)


def cmd_monster(args: list[str]):
    if not args:
        print("用法: python src/cli.py monster \"怪物名\" [--version <id>]")
        return
    args, version = _parse_version_flag(args)
    results = structured_query.query_monsters(" ".join(args), top_k=15, version=version)
    _print_json_results(results)


def cmd_spell(args: list[str]):
    if not args:
        print("用法: python src/cli.py spell \"法术名\" [--version <id>]")
        return
    args, version = _parse_version_flag(args)
    results = structured_query.query_spells(" ".join(args), top_k=15, version=version)
    _print_json_results(results)


def cmd_skill(args: list[str]):
    if not args:
        print("用法: python src/cli.py skill \"技能名\" [--version <id>]")
        return
    args, version = _parse_version_flag(args)
    results = structured_query.query_skills(" ".join(args), top_k=15, version=version)
    _print_json_results(results)


# ---------------------------------------------------------------------------
# Version subcommands
# ---------------------------------------------------------------------------

def _version_usage():
    print("Version 子命令:")
    print("  version list                          列出所有版本")
    print("  version create <id> <name>            创建新版本")
    print("  version modify <id> <type> <name> <field> <value>  修改规则")
    print("  version remove <id> <type> <name>      删除规则")
    print("  version add <id> <type> <name> [json]  添加自定义规则")
    print("  version diff <from> <to>              比较版本差异")
    print("  version use <id>                      设为默认版本")
    print("  version export <id> [filepath]        导出版本")
    print("  version import <filepath>             导入版本")
    print()
    print("  <type>: weapons | monsters | spells | skills | rules")


def _version_list(args: list[str]):
    versions = versioning.get_version_list()
    if not versions:
        print("(无版本)")
        return
    default = versioning.get_default_version()
    for v in versions:
        marker = " *" if v["id"] == default else ""
        ro = " [只读]" if v.get("readonly") else ""
        base = f" (基于 {v['based_on']})" if v.get("based_on") else ""
        print(f"  {v['id']}: {v['name']}{ro}{base}{marker}")
    if default:
        print(f"\n默认版本: {default}")


def _version_create(args: list[str]):
    if len(args) < 2:
        print("用法: version create <id> <name>")
        return
    try:
        versioning.create_version(args[0], " ".join(args[1:]))
        print(f"版本 '{args[0]}' 已创建。")
    except Exception as e:
        print(f"错误: {e}")


def _version_modify(args: list[str]):
    if len(args) < 5:
        print("用法: version modify <id> <type> <name> <field> <value>")
        return
    try:
        version_id, category, name, field, value = args[0], args[1], args[2], args[3], args[4]
        versioning.modify_rule(version_id, category, {"名称": name}, {field: value})
        print(f"已修改 '{name}' 的 {field} -> {value}")
    except Exception as e:
        print(f"错误: {e}")


def _version_remove(args: list[str]):
    if len(args) < 3:
        print("用法: version remove <id> <type> <name>")
        return
    try:
        version_id, category, name = args[0], args[1], args[2]
        versioning.remove_rule(version_id, category, {"名称": name})
        print(f"已移除 '{name}'")
    except Exception as e:
        print(f"错误: {e}")


def _version_add(args: list[str]):
    if len(args) < 3:
        print("用法: version add <id> <type> <name> [json]")
        print("  json 应为额外字段的 JSON 对象, 如 '{\"伤害\":\"4D10\",\"技能\":\"射击(步枪)\"}'")
        return
    try:
        version_id, category, name = args[0], args[1], args[2]
        data = {"名称": name}
        if len(args) >= 4:
            extra = " ".join(args[3:])
            data.update(json.loads(extra))
        versioning.add_rule(version_id, category, data)
        print(f"已添加 '{name}'")
    except Exception as e:
        print(f"错误: {e}")


def _version_diff(args: list[str]):
    if len(args) < 2:
        print("用法: version diff <from> <to>")
        return
    try:
        diffs = versioning.diff_versions(args[0], args[1])
        has_diff = False
        for cat, changes in diffs.items():
            if changes:
                has_diff = True
                print(f"--- {cat} ({len(changes)} changes) ---")
                for c in changes:
                    if c["change"] == "removed":
                        print(f"  - {c['name']}")
                    elif c["change"] == "added":
                        print(f"  + {c['name']}")
                    elif c["change"] == "modified":
                        print(f"  ~ {c['name']}: {c['field']}: {c['old']} -> {c['new']}")
                print()
        if not has_diff:
            print(f"{args[0]} 与 {args[1]} 无差异。")
    except Exception as e:
        print(f"错误: {e}")


def _version_use(args: list[str]):
    if not args:
        print("用法: version use <id>  (使用 'none' 恢复默认)")
        return
    try:
        ver = None if args[0] == "none" else args[0]
        versioning.set_default_version(ver)
        if ver:
            print(f"默认版本已设为 '{ver}'")
        else:
            print("已恢复使用原始规则数据。")
    except Exception as e:
        print(f"错误: {e}")


def _version_export(args: list[str]):
    if not args:
        print("用法: version export <id> [filepath]")
        return
    try:
        version_id = args[0]
        filepath = args[1] if len(args) > 1 else f"{version_id}_export.json"
        out = versioning.export_version(version_id, filepath)
        print(f"版本 '{version_id}' 已导出到 {out}")
    except Exception as e:
        print(f"错误: {e}")


def _version_import(args: list[str]):
    if not args:
        print("用法: version import <filepath>")
        return
    try:
        result = versioning.import_version(args[0])
        print(f"版本已导入为 '{result}'")
    except Exception as e:
        print(f"错误: {e}")


_VERSION_SUB = {
    "list": _version_list,
    "create": _version_create,
    "modify": _version_modify,
    "remove": _version_remove,
    "add": _version_add,
    "diff": _version_diff,
    "use": _version_use,
    "export": _version_export,
    "import": _version_import,
}


def cmd_version(args: list[str]):
    if not args or args[0] not in _VERSION_SUB:
        _version_usage()
        return
    _VERSION_SUB[args[0]](args[1:])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

COMMANDS = {
    "rule": cmd_rule,
    "rebuild": cmd_rebuild,
    "weapon": cmd_weapon,
    "monster": cmd_monster,
    "spell": cmd_spell,
    "skill": cmd_skill,
    "version": cmd_version,
}


def main():
    if len(sys.argv) < 2:
        print("RuleWhisper — COC 全能跑团助手")
        print()
        print("可用命令:")
        print("  rule <关键词>          搜索规则全文")
        print("  weapon <关键词>        查询武器 [--version <id>]")
        print("  monster <关键词>       查询怪物 [--version <id>]")
        print("  spell <关键词>         查询法术 [--version <id>]")
        print("  skill <关键词>         查询技能 [--version <id>]")
        print("  rebuild                重建文本索引")
        print("  version <子命令> ...    规则版本管理")
        print()
        print("示例:")
        print('  python src/cli.py rule "霰弹枪伤害"')
        print('  python src/cli.py weapon "左轮"')
        print('  python src/cli.py version create v2.0 "我的房规"')
        print('  python src/cli.py weapon "霰弹枪" --version v2.0')
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
