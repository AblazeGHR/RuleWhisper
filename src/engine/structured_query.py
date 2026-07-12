"""Structured query engine for weapons, monsters, spells, skills."""
from typing import Optional
import jieba

from . import versioning


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


def _resolve_version(version: Optional[str]) -> str:
    """Resolve version parameter: explicit > default > v1.0."""
    if version:
        return version
    return versioning.get_default_version() or "v1.0"


def query_weapons(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search weapons within a rules version (defaults to v1.0)."""
    ver = _resolve_version(version)
    data = versioning.load_version_data(ver, "weapons")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]


def query_monsters(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search monsters within a rules version (defaults to v1.0)."""
    ver = _resolve_version(version)
    data = versioning.load_version_data(ver, "monsters")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]


def query_spells(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search spells within a rules version (defaults to v1.0)."""
    ver = _resolve_version(version)
    data = versioning.load_version_data(ver, "spells")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]


def query_skills(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search skills within a rules version (defaults to v1.0)."""
    ver = _resolve_version(version)
    data = versioning.load_version_data(ver, "skills")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]


def query_rules(query: str, top_k: int = 10, version: Optional[str] = None) -> list[dict]:
    """Search rules within a rules version (defaults to v1.0)."""
    ver = _resolve_version(version)
    data = versioning.load_version_data(ver, "rules")
    scored = [(e, _match_score(query, e)) for e in data]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored if s > 0][:top_k]
