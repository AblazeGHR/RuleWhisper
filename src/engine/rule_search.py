"""Rule search engine for COC 7th rulebook."""
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure src is on path (for `python src/cli.py` from project root)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.indexer import RuleIndex, IndexEntry

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_index: Optional[RuleIndex] = None


def get_index(force_rebuild: bool = False) -> RuleIndex:
    """Get or build the search index (singleton)."""
    global _index
    if _index is not None and not force_rebuild:
        return _index

    idx_path = str(_DATA_DIR / "index.json")
    rulebook_path = str(_DATA_DIR / "守秘人规则书.txt")

    if os.path.exists(idx_path) and not force_rebuild:
        print("Loading index from cache...", flush=True)
        _index = RuleIndex.load(idx_path)
        return _index

    print("Building index (this may take a few seconds)...", flush=True)
    _index = RuleIndex().build(rulebook_path)
    _index.save(idx_path)
    return _index


def search(query: str, top_k: int = 10) -> list[IndexEntry]:
    """Search the rulebook."""
    idx = get_index()
    return idx.search(query, top_k=top_k)


def format_results(results: list[IndexEntry]) -> str:
    """Format search results for display."""
    if not results:
        return "未找到匹配结果。"

    lines = []
    seen_pages = set()

    for i, entry in enumerate(results, 1):
        # Deduplicate: if same page already shown, skip
        # (keep first occurrence since it has higher score)
        if entry.page in seen_pages:
            continue
        seen_pages.add(entry.page)

        # Truncate long text for readability
        text = entry.text
        if len(text) > 200:
            text = text[:200] + "…"

        lines.append(
            f"#{i} [{entry.chapter}] 第 {entry.page} 页  (相关性: {entry.score:.1f})\n"
            f"   {text}\n"
        )

        if len(seen_pages) >= 5:
            break

    return "\n".join(lines)
