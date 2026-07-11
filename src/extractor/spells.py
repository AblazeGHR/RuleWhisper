"""Extract spell entries from Chapter 12 of the rulebook txt."""
import re, json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent
DATA = PROJECT / "data"


def extract_spells():
    txt_path = DATA / "守秘人规则书.txt"
    with open(txt_path, encoding="utf-8") as f:
        data = f.read()

    idx_start = data.find("===== 第 206 页 =====")
    idx_end = data.find("===== 第 232 页 =====")
    if idx_start < 0 or idx_end < 0:
        print("Spell chapter not found")
        return []

    chapter = data[idx_start:idx_end]

    # Find spell entries by name pattern: "X术:", "X法:", etc.
    # Chinese spell names typically end with 术, 法, 咒, 波, or specific patterns
    name_pattern = re.compile(
        r"([\u4e00-\u9fff\w·\-]{2,25}(?:术|法|咒|波|触|附魔|召唤|联络|请神|送神|通道|守卫|创造|祝福|诅咒|变形|保护|屏障|武器|附魔|反魔))[：:]",
        re.MULTILINE
    )

    spells = []
    seen_names = set()

    for m in name_pattern.finditer(chapter):
        name = m.group(1).strip()

        # Skip non-spell names (found in narrative/example text)
        if name in seen_names:
            continue
        if "克苏鲁" in name and "请神" not in name and "联络" not in name:
            continue

        # Get context: 300 chars after the name
        after = chapter[m.end():m.end() + 400]

        # Extract cost
        cost = _extract_field(after, r"消耗[：:]\s*(.+?)(?:\n|$)")
        # For spells where cost is inline after name
        if not cost:
            inline = after[:100].strip()
            if re.match(r"^\s*\d+", inline):
                cost = inline.split("\n")[0].strip()

        # Extract casting time
        cast_time = _extract_field(after, r"施法用时[：:]\s*(.+?)(?:\n|$)")

        spell = {
            "名称": name,
            "消耗": cost or "",
            "施法用时": cast_time or "",
        }

        # Only include spells with valid cost
        if cost and len(cost) > 0:
            seen_names.add(name)
            spells.append(spell)

    return spells


def _extract_field(text: str, pattern: str) -> str:
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


if __name__ == "__main__":
    spells = extract_spells()
    print(f"Extracted {len(spells)} spells\n")

    out = DATA / "spells.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(spells, f, ensure_ascii=False, indent=2)
    print(f"Saved to {out} ({out.stat().st_size/1024:.0f} KB)")

    for s in spells[:15]:
        print(f"  {s['名称']}: {s['消耗'][:50]}")
