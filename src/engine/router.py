"""Unified query router — automatic dispatch across structured data and full-text search."""
import json
import re
import sys
from pathlib import Path
from typing import Optional

import jieba

# Ensure src is on path for same-package imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import engine.rule_search as rule_search
from engine.structured_query import query_weapons, query_monsters, query_spells, query_skills

RELEVANCE_THRESHOLD = 30

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_ENTITY_NAMES: Optional[dict[str, list[str]]] = None


def _load_entity_names() -> dict[str, list[str]]:
    """Lazy-load entity names from structured data files, sorted longest-first."""
    global _ENTITY_NAMES
    if _ENTITY_NAMES is not None:
        return _ENTITY_NAMES

    _ENTITY_NAMES = {}

    configs = [
        ("weapon", "weapons.json", "名称"),
        ("monster", "monsters.json", "名称"),
        ("spell", "spells.json", "名称"),
        ("skill", "skills.json", "名称"),
    ]

    for key, filename, name_field in configs:
        path = _DATA_DIR / filename
        if not path.exists():
            _ENTITY_NAMES[key] = []
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        names = []
        for entry in data:
            name = entry.get(name_field, "")
            if name and len(name) >= 2:
                names.append(name)
            alias = entry.get("别名")
            if alias:
                if isinstance(alias, list):
                    names.extend(a for a in alias if len(a) >= 2)
                elif isinstance(alias, str) and len(alias) >= 2:
                    names.append(alias)
        # Sort by length descending so "战斗霰弹枪" matches before "霰弹枪"
        _ENTITY_NAMES[key] = sorted(set(names), key=len, reverse=True)

    return _ENTITY_NAMES


# Common Chinese terms that are too generic for reverse entity matching
_REVERSE_MATCH_STOP_WORDS = {
    "战斗", "攻击", "武器", "怪物", "法术", "技能", "规则", "使用",
    "射击", "格斗", "投掷", "远程", "近战", "造成", "目标", "生命",
    "属性", "力量", "体型", "敏捷", "智力", "意志", "教育", "体质",
    "魅力", "移动", "回避", "判定", "检定", "对抗", "惩罚", "奖励",
}


def _match_entity_names(query: str) -> list[str]:
    """Return list of entity types whose names appear in the query.

    Matches both:
    - Entity name is a substring of query (e.g., "深潜者" in "深潜者属性")
    - Query term is a substring of entity name (e.g., "左轮" in ".38/9mm左轮手枪")
    """
    entity_names = _load_entity_names()
    matched = []
    for t, names in entity_names.items():
        for name in names:
            if name in query:
                matched.append(t)
                break
    if matched:
        return matched

    # Reverse match: query terms in entity names (min 2 chars, filter stop words)
    query_terms = [
        w for w in jieba.lcut(query)
        if len(w) >= 2 and w not in _REVERSE_MATCH_STOP_WORDS
    ]
    if not query_terms:
        return matched

    for t, names in entity_names.items():
        if t in matched:
            continue
        for name in names:
            if any(term in name for term in query_terms):
                matched.append(t)
                break

    return matched


def _classify_by_feature_words(query: str) -> list[str]:
    """Classify query by type-specific feature words (heuristic fallback)."""
    types = []

    # Weapon: dice notation, range, or weapon-specific fields
    if re.search(r'\d+D\d+', query) or re.search(r'\d+码', query):
        types.append("weapon")
    else:
        weapon_words = ["伤害", "射程", "故障值", "装弹量"]
        if any(w in query for w in weapon_words):
            types.append("weapon")

    # Monster: stat abbreviations or combat-specific fields
    monster_words = ["STR", "HP", "护甲", "理智损失", "伤害加值", "体格", "每回合攻击"]
    if any(w in query for w in monster_words):
        types.append("monster")

    # Spell: cost/casting time or 术 suffix
    spell_words = ["消耗", "施法用时"]
    if any(w in query for w in spell_words) or query.endswith("术"):
        types.append("spell")

    # Skill: percentage notation or base value
    if "%" in query or "基础值" in query:
        types.append("skill")

    return types


_QUERY_FNS = {
    "weapon": query_weapons,
    "monster": query_monsters,
    "spell": query_spells,
    "skill": query_skills,
}


def _try_structured(query: str, types: list[str], top_k: int) -> Optional[dict]:
    """Try structured queries for given types, return first with results."""
    for t in types:
        if t not in _QUERY_FNS:
            continue
        results = _QUERY_FNS[t](query, top_k)
        if results:
            return {"source": "structured", "type": t, "results": results}
    return None


def route_query(query: str, top_k: int = 10) -> dict:
    """Route a natural-language query to the best engine.

    Returns:
        {"source": "structured", "type": "weapon"|"monster"|"spell"|"skill", "results": [...]}
        {"source": "keyword_search", "type": None, "results": [IndexEntry, ...]}
        {"source": None, "type": None, "results": []}
    """
    query = query.strip()
    if not query:
        return {"source": None, "type": None, "results": []}

    # Tier 1: Explicit prefix — strip and route directly
    prefix_map = {
        "武器": "weapon",
        "怪物": "monster",
        "法术": "spell",
        "技能": "skill",
    }
    for prefix, t in prefix_map.items():
        if query.startswith(prefix + " "):
            clean_query = query[len(prefix) + 1:].strip()
            if clean_query:
                result = _try_structured(clean_query, [t], top_k)
                if result:
                    return result
            break  # prefix matched, don't check others even if no results

    # Tier 2: Feature word heuristics (stronger intent signal, checked first)
    feature_types = _classify_by_feature_words(query)
    if feature_types:
        result = _try_structured(query, feature_types, top_k)
        if result:
            return result

    # Tier 3: Entity name match (weaker signal, checked after feature words)
    entity_types = _match_entity_names(query)
    if entity_types:
        result = _try_structured(query, entity_types, top_k)
        if result:
            return result

    # Tier 4: Full-text search fallback
    search_results = rule_search.search(query, top_k=top_k)
    if search_results and search_results[0].score >= RELEVANCE_THRESHOLD:
        return {"source": "keyword_search", "type": None, "results": search_results}

    # Tier 5: No match
    return {"source": None, "type": None, "results": []}
