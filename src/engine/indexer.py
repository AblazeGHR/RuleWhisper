"""Build inverted index from COC 7th rulebook text."""
import os
import re
import json
from pathlib import Path
import jieba
from dataclasses import dataclass, field, asdict
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = _PROJECT_ROOT / "data"
RULEBOOK_FILE = str(DATA_DIR / "守秘人规则书.txt")
INDEX_FILE = str(DATA_DIR / "index.json")

# Chapter title → starting page number in our text (1-indexed)
CHAPTERS = [
    (8,   "第一章 介绍"),
    (16,  "第二章 爱手艺与克苏鲁神话"),
    (24,  "第三章 创建调查员"),
    (44,  "第四章 技能"),
    (72,  "第五章 游戏系统"),
    (86,  "第六章 战斗"),
    (112, "第七章 追逐"),
    (130, "第八章 理智"),
    (144, "第九章 魔法"),
    (154, "第十章 主持游戏"),
    (190, "第十一章 可怖传说书籍"),
    (206, "第十二章 法术"),
    (232, "第十三章 外星科技及其造物"),
    (240, "第十四章 怪物、野兽和神话诸神"),
    (314, "第十五章 模组"),
    (356, "第十六章 附录"),
]


@dataclass
class Paragraph:
    page: int
    chapter: str
    text: str
    lineno: int


@dataclass
class IndexEntry:
    """A single search result entry."""
    page: int
    chapter: str
    text: str
    lineno: int
    score: float = 0.0


class RuleIndex:
    """Inverted index for rulebook text search."""

    def __init__(self):
        self._paragraphs: list[Paragraph] = []
        self._inverted: dict[str, list[int]] = {}  # word → [paragraph indices]
        self._built = False

    @staticmethod
    def _get_chapter(page_num: int) -> str:
        """Get the chapter name for a given page number."""
        current = ""
        for p, name in CHAPTERS:
            if page_num >= p:
                current = name
            else:
                break
        return current

    def build(self, filepath: str = RULEBOOK_FILE) -> "RuleIndex":
        """Build index from rulebook txt file."""
        with open(filepath, encoding="utf-8") as f:
            data = f.read()

        # Split into pages
        page_pattern = re.compile(r"===== 第 (\d+) 页 =====")
        pages = page_pattern.split(data)

        # pages[0] = text before first marker (empty)
        # pages[1] = page number, pages[2] = page content, ...
        para_idx = 0
        for i in range(1, len(pages), 2):
            page_num = int(pages[i])
            content = pages[i + 1].strip()
            chapter = self._get_chapter(page_num)

            # Split page content into paragraphs
            paras = [p.strip() for p in content.split("\n\n") if p.strip()]

            for text in paras:
                if len(text) < 4:  # skip very short fragments
                    continue
                self._paragraphs.append(Paragraph(
                    page=page_num,
                    chapter=chapter,
                    text=text,
                    lineno=para_idx,
                ))
                para_idx += 1

        # Build inverted index
        print(f"Indexing {len(self._paragraphs)} paragraphs...", flush=True)
        for pid, para in enumerate(self._paragraphs):
            words = jieba.lcut(para.text)
            seen = set()
            for w in words:
                w = w.strip().lower()
                if len(w) < 2 or w in STOP_WORDS:
                    continue
                if w in seen:
                    continue
                seen.add(w)
                self._inverted.setdefault(w, []).append(pid)

        self._built = True
        print(f"Built index: {len(self._inverted)} unique terms", flush=True)
        return self

    def search(self, query: str, top_k: int = 10) -> list[IndexEntry]:
        """Search the index with a query string. Returns top_k results."""
        if not self._built:
            self.build()

        query_words = [w.strip().lower() for w in jieba.lcut(query)
                       if len(w.strip()) >= 2 and w.strip() not in STOP_WORDS]

        # Expand synonyms: add canonical forms for variant terms
        expanded = []
        for w in query_words:
            expanded.append(w)
            if w in SYNONYM_MAP:
                expanded.extend(SYNONYM_MAP[w])

        query_words = list(set(expanded))  # deduplicate

        if not query_words:
            return []

        # Collect matching paragraph IDs with raw TF-IDF scores
        raw_scores: dict[int, float] = {}
        for w in query_words:
            matches = self._inverted.get(w, [])
            idf = max(1.0, len(self._paragraphs) / max(1, len(matches)))
            for pid in matches:
                tf = self._paragraphs[pid].text.lower().count(w)
                raw_scores[pid] = raw_scores.get(pid, 0) + tf * idf

        if not raw_scores:
            return []

        # Normalize scores to 0-100 scale
        max_raw = max(raw_scores.values())
        scores: dict[int, float] = {}
        for pid, raw in raw_scores.items():
            normalized = (raw / max_raw) * 100.0 if max_raw > 0 else 0
            scores[pid] = normalized

            # Bonus 1: structural data pages get +15
            page = self._paragraphs[pid].page
            if page in STRUCTURAL_DATA_PAGES:
                scores[pid] += 15

            # Bonus 2: query word appears in first 60 chars (likely title/lead) → +10
            text_head = self._paragraphs[pid].text[:60].lower()
            if any(w in text_head for w in query_words):
                scores[pid] += 10

        # Sort by adjusted score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        return [IndexEntry(
            page=self._paragraphs[pid].page,
            chapter=self._paragraphs[pid].chapter,
            text=self._paragraphs[pid].text,
            lineno=self._paragraphs[pid].lineno,
            score=round(score, 1),
        ) for pid, score in ranked]

    def save(self, filepath: str = INDEX_FILE):
        """Persist index to disk (paragraphs only, rebuild inverted on load)."""
        data = [asdict(p) for p in self._paragraphs]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved index paragraphs to {filepath}", flush=True)

    @classmethod
    def load(cls, filepath: str = INDEX_FILE) -> "RuleIndex":
        """Load index from disk."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        idx = cls.__new__(cls)
        idx._paragraphs = [Paragraph(**p) for p in data]
        idx._inverted = {}
        idx._built = False

        # Rebuild inverted index
        for pid, para in enumerate(idx._paragraphs):
            words = jieba.lcut(para.text)
            seen = set()
            for w in words:
                w = w.strip().lower()
                if len(w) < 2 or w in STOP_WORDS:
                    continue
                if w in seen:
                    continue
                seen.add(w)
                idx._inverted.setdefault(w, []).append(pid)

        idx._built = True
        print(f"Loaded index: {len(idx._paragraphs)} paragraphs, {len(idx._inverted)} terms", flush=True)
        return idx


# Synonym map: query variant → canonical term (expands query to match more content)
SYNONYM_MAP: dict[str, list[str]] = {
    "散弹枪": ["霰弹枪"],
    "hp": ["生命值"],
    "san": ["理智值", "理智"],
    "mp": ["魔法值"],
    "db": ["伤害加值"],
    "build": ["体格"],
    "mov": ["移动"],
    "kp": ["守秘人"],
    "pc": ["调查员"],
    "pl": ["玩家"],
    "npc": [],
    "6版": ["六版"],
    "7版": ["七版"],
    "跑团": [],
    "coc": [],
}

# Pages containing structured game data tables (weapons, monsters, spells, sanity)
# These get a ranking boost to appear before narrative mentions
STRUCTURAL_DATA_PAGES = set()
for p in range(372, 383): STRUCTURAL_DATA_PAGES.add(p)  # weapon tables
for p in range(240, 312): STRUCTURAL_DATA_PAGES.add(p)  # monster stats
for p in range(205, 230): STRUCTURAL_DATA_PAGES.add(p)  # spell lists
for p in range(130, 143): STRUCTURAL_DATA_PAGES.add(p)  # sanity rules
for p in range(387, 390): STRUCTURAL_DATA_PAGES.add(p)  # sanity tables

STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "自己", "这", "他", "她", "它", "们", "那", "些", "什么", "这个", "那个",
    "可以", "如果", "被", "把", "但", "而", "与", "或", "于", "之", "以", "及",
    "为", "所", "其", "中", "从", "对", "等", "能", "已经", "还", "只", "然后",
    "因为", "所以", "因此", "不过", "并且", "而且", "虽然", "但是",
    "每", "任何", "所有", "通过", "需要", "可能", "应该", "他们",
    "进行", "使用", "一个", "一种", "通常", "一般", "比较", "更加",
    "一次", "一样", "不同", "另外", "其他", "其中", "上述",
    "一个", "这里", "那里", "如何", "怎么", "哪个", "哪里",
    # Query prefix / utility words
    "查询", "查", "查找", "搜索", "找", "查下", "查一下",
    "规则", "告诉我", "请问", "帮我查", "告诉我一下",
    "一下", "问问", "啥是", "什么是", "是什么",
}
