"""Structured query engine for weapons, monsters, spells, skills."""
import json
import re
from pathlib import Path
from typing import Optional
import jieba

from . import versioning

_DATA = Path(__file__).resolve().parent.parent.parent / "data"

_CACHE: dict[str, list[dict]] = {}


def _load(filename: str) -> list[dict]:
    """Load a JSON data file with caching."""
    if filename not in _CACHE:
        path = _DATA / filename
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            _CACHE[filename] = json.load(f)
    return _CACHE[filename]


def _jaccard_sim(query_terms: set[str], target_terms: set[str]) -> float:
    """Simple term overlap similarity."""
    if not query_terms or not target_terms:
        return 0
    return len(query_terms & target_terms) / max(1, len(query_terms | target_terms))


def _match_score(query: str, entry: dict, field: str = "名称") -> float:
    """Score an entry against a query."""
    target = entry.get(field, "").lower()
    q = query.lower()

    # Exact match
    if q == target:
        return 2.0

    # Substring match (e.g., "左轮" in ".38/9mm左轮手枪")
    if q in target:
        return 1.0

    # Jieba overlap
    q_words = set(jieba.lcut(q))
    t_words = set(jieba.lcut(target))
    return _jaccard_sim(q_words, t_words)


def _resolve_version(version: Optional[str]) -> Optional[str]:
    """Resolve version parameter: explicit > default > None (use raw data/)."""
    if version:
        return version
    return versioning.get_default_version()


def query_weapons(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search weapons (optionally within a rules version)."""
    ver = _resolve_version(version)
    if ver:
        data = versioning.load_version_data(ver, "weapons")
    else:
        data = _load("weapons.json")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]


def query_monsters(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search monsters (optionally within a rules version)."""
    ver = _resolve_version(version)
    if ver:
        data = versioning.load_version_data(ver, "monsters")
    else:
        data = _load("monsters.json")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]


def query_spells(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search spells (optionally within a rules version)."""
    ver = _resolve_version(version)
    if ver:
        data = versioning.load_version_data(ver, "spells")
    else:
        data = _load("spells.json")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]


def query_skills(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search skills (optionally within a rules version)."""
    ver = _resolve_version(version)
    if ver:
        data = versioning.load_version_data(ver, "skills")
    else:
        data = _load("skills.json")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]


def query_rules(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search rules (optionally within a rules version)."""
    ver = _resolve_version(version)
    if ver:
        data = versioning.load_version_data(ver, "rules")
    else:
        data = _load("rules.json")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]
