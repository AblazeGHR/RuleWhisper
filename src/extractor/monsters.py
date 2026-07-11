"""Extract monster stats from Chapter 14 of the rulebook txt."""
import re, json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent
DATA = PROJECT / "data"


def extract_monsters():
    txt_path = DATA / "守秘人规则书.txt"
    with open(txt_path, encoding="utf-8") as f:
        data = f.read()

    # Find Chapter 14
    ch14_start = data.find("第十四章 怪物、野兽和神话诸神")
    ch15_start = data.find("第十五章 模组", ch14_start)
    if ch14_start < 0:
        print("Chapter 14 not found")
        return []
    
    chapter = data[ch14_start:ch15_start]

    # Split into blocks between stat tables
    # Each monster has a stat block with 属性 平均 掷骰
    blocks = _split_into_monster_blocks(chapter)
    print(f"Found {len(blocks)} potential monster blocks")

    monsters = []
    seen_names = set()

    for block in blocks:
        m = _parse_monster_block(block)
        if m and _is_valid_monster(m):
            name = m.get("名称", "")
            if name and name not in seen_names:
                seen_names.add(name)
                monsters.append(m)

    print(f"After dedup + validation: {len(monsters)} valid monsters")
    return monsters


def _split_into_monster_blocks(text: str) -> list[str]:
    """Split chapter text into individual monster blocks."""
    # Strategy: find each "属性 平均 掷骰" occurrence and work backwards
    # to find the monster name, creating blocks from name to end of stat data
    
    stat_markers = list(re.finditer(r"属性\s+平均\s+掷骰", text))
    if not stat_markers:
        return []

    blocks = []
    for i, marker in enumerate(stat_markers):
        # Find the monster name before this stat block
        before = text[:marker.start()]
        
        # Find the end of this monster's section
        if i + 1 < len(stat_markers):
            end = stat_markers[i + 1].start()
        else:
            end = len(text)
        
        # Extract a generous window before the stats
        # Monster name is typically 500-2000 chars before the stat table
        window_start = max(0, marker.start() - 4000)
        window = text[window_start:end]

        # Find the monster name within this window
        # Look backwards from "属性" for a recognizable monster name
        name = _find_monster_name(text, marker.start())
        if name:
            common, formal = name
            blocks.append({
                "name": common,
                "formal": formal,
                "text": text[max(0, marker.start() - 500):end + 500]
            })

    return blocks


def _find_monster_name(text: str, stat_pos: int) -> tuple[str, str] | None:
    """Find the monster name by looking backwards from the stat block.
    Returns (common_name, formal_name) or None."""
    before = text[max(0, stat_pos - 5000):stat_pos]
    lines = before.split("\n")

    # Look backwards for the monster name line (pattern: "Name，Title")
    for line in lines[::-1]:
        line = line.strip()
        if not line or len(line) > 60 or len(line) < 3:
            continue

        # Skip obvious non-names
        skip_patterns = [
            r"H[．.]P[．.]", r"洛夫克拉夫特", r"译注:", r"特殊能力",
            r"STR|CON|SIZ|DEX|INT|POW|HP", r"属性\s+平均", r"法术[：:]",
            r"技能[：:]", r"护甲[：:]", r"理智损失", r"每回合攻击",
            r"克苏鲁的呼唤", r"第十四章", r"第十五章",
        ]
        if any(re.search(p, line) for p in skip_patterns):
            continue

        # Pattern 1: "Name，Title" (Chinese comma separator)
        if re.search(r"[\u4e00-\u9fff\w·]+，[\u4e00-\u9fff]", line):
            parts = line.split("，", 1)
            common = parts[0].strip()
            formal = parts[1].strip() if len(parts) > 1 else ""
            if 2 <= len(common) <= 20:
                return common, formal

        # Pattern 2: "EnglishName，ChineseName"
        if re.search(r"[A-Za-z]+，[\u4e00-\u9fff]", line):
            parts = line.split("，", 1)
            common = parts[0].strip()
            formal = parts[1].strip() if len(parts) > 1 else ""
            if 2 <= len(common) <= 25:
                return common, formal

    return None


def _is_valid_monster(m: dict) -> bool:
    """Filter out invalid monster entries (description got parsed as name)."""
    name = m.get("名称", "")
    # Reject names that look like description fragments
    if len(name) > 20:
        return False
    if "可以" in name or "任何" in name or "没有" in name or "并非" in name:
        return False
    if "能" in name and len(name) > 10:
        return False
    if re.search(r"[。！？，；：""'']", name):
        return False
    # Must have at least STR and HP
    if "STR" not in m or "HP" not in m:
        return False
    return True


def _parse_monster_block(block: dict) -> dict | None:
    """Parse a single monster block into structured data."""
    text = block["text"]
    monster = {"名称": block["name"]}
    if block.get("formal"):
        monster["别名"] = block["formal"]
    
    # Extract attributes: 属性 平均 掷骰
    attr_section = text.find("属性 平均 掷骰")
    if attr_section < 0:
        return None

    attr_text = text[attr_section:attr_section + 500]
    
    # Parse individual attributes
    for attr_name in ["STR", "CON", "SIZ", "DEX", "INT", "POW"]:
        m = re.search(rf"{attr_name}\s+(\d+)\s*[（(]?([^）)\n]*)", attr_text)
        if m:
            monster[attr_name] = int(m.group(1))
            monster[f"{attr_name}_dice"] = m.group(2).strip()

    # HP
    hp_m = re.search(r"HP[：:]\s*(\d+)", attr_text)
    if hp_m:
        monster["HP"] = int(hp_m.group(1))

    # Damage bonus
    db_m = re.search(r"(?:平均)?伤害加值[：:]\s*([+\-]?\d*D?\d*)", text)
    if db_m:
        monster["伤害加值"] = db_m.group(1).strip()

    # Build/体格
    build_m = re.search(r"(?:平均)?体格[：:]\s*(\d+)", text)
    if build_m:
        monster["体格"] = int(build_m.group(1))

    # Magic points
    mp_m = re.search(r"(?:平均)?魔法值[：:]\s*(\d+)", text)
    if mp_m:
        monster["魔法值"] = int(mp_m.group(1))

    # Movement
    mov_m = re.search(r"移动[：:]\s*(.+?)(?:\n|$)", text)
    if mov_m:
        monster["移动"] = mov_m.group(1).strip()

    # Attacks per round
    apr_m = re.search(r"每回合攻击[：:]\s*(\d+次)", text)
    if apr_m:
        monster["每回合攻击"] = apr_m.group(1).strip()

    # Combat skills
    fight_m = re.search(r"格斗\s+(\d+)%\s*[（(](\d+)/(\d+)[）)]\s*,?\s*(?:伤害)?\s*(.+)", text)
    if fight_m:
        monster["格斗"] = int(fight_m.group(1))
        monster["格斗_困难"] = int(fight_m.group(2))
        monster["格斗_极难"] = int(fight_m.group(3))
        monster["格斗_伤害"] = fight_m.group(4).strip()

    dodge_m = re.search(r"闪避\s+(\d+)%\s*[（(](\d+)/(\d+)[）)]", text)
    if dodge_m:
        monster["闪避"] = int(dodge_m.group(1))
        monster["闪避_困难"] = int(dodge_m.group(2))
        monster["闪避_极难"] = int(dodge_m.group(3))

    # Armor
    armor_m = re.search(r"护甲[：:]\s*(.+?)(?:\n|$)", text)
    if armor_m:
        monster["护甲"] = armor_m.group(1).strip()

    # Skills
    skills_m = re.search(r"技能[：:]\s*(.+?)(?:\n|$)", text)
    if skills_m:
        monster["技能"] = skills_m.group(1).strip()

    # Sanity loss
    san_m = re.search(r"理智损失[：:]\s*(.+?)(?:\n|$)", text)
    if san_m:
        monster["理智损失"] = san_m.group(1).strip()

    return monster if "STR" in monster else None


if __name__ == "__main__":
    monsters = extract_monsters()
    print(f"\nExtracted {len(monsters)} monsters\n")

    out = DATA / "monsters.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(monsters, f, ensure_ascii=False, indent=2)
    print(f"Saved to {out} ({out.stat().st_size/1024:.0f} KB)")

    for m in monsters[:5]:
        name = m.get("名称", "?")
        hp = m.get("HP", "?")
        db = m.get("伤害加值", "?")
        print(f"  {name}: STR={m.get('STR','?')} HP={hp} DB={db}")
