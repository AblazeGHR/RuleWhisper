"""Extract weapon tables from the rulebook txt."""
import re, json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent
DATA = PROJECT / "data"


def extract_weapons() -> list[dict]:
    txt_path = DATA / "守秘人规则书.txt"
    with open(txt_path, encoding="utf-8") as f:
        data = f.read()

    # Locate weapon appendix: txt pages 372-378
    idx_start = data.find("===== 第 372 页 =====") 
    idx_end = data.find("===== 第 379 页 =====")
    if idx_start < 0 or idx_end < 0:
        print("Weapon section not found")
        return []

    text = data[idx_start:idx_end]

    # Find weapon categories and their data
    weapons = []
    # Categories in order: 近战武器, 手枪, 步枪, 霰弹枪, 冲锋枪/突击步枪, 机枪, 爆炸物
    category_map = [
        ("常规武器", "近战武器"),
        ("手枪（贯穿）*", "手枪"),
        ("步枪（贯穿）*", "步枪"),
        ("霰弹枪*", "霰弹枪"),
        ("冲锋枪", "冲锋枪/突击步枪"),
        ("突击步枪", "冲锋枪/突击步枪"),
        ("机枪", "机枪"),
        ("爆炸物", "爆炸物"),
        ("重武器", "重武器"),
        ("火焰喷射器", "火焰喷射器"),
    ]

    # Split into categories
    for marker, category in category_map:
        idx = text.find(marker)
        if idx < 0:
            continue

        # Extract until next marker or end
        rest = text[idx + len(marker):]
        for m2, _ in category_map:
            if m2 != marker and m2 in rest[:500]:
                # Find earliest next marker
                break

        # Parse weapons from this section
        weapons.extend(_parse_section(rest, category, marker))

    return weapons


def _parse_section(text: str, category: str, _marker: str) -> list[dict]:
    """Parse a single weapon category section."""
    weapons = []
    lines = text.split("\n")

    # Find the first weapon data line after header
    for line in lines:
        line = line.strip()
        if not line or len(line) < 20:
            continue
        if "价格" in line[:30] or "名称" in line[:10] or "20s" in line[:20]:
            continue

        # This is a weapon data line - contains damage dice
        if not re.search(r"\d+D\d+", line):
            continue

        # Parse individual weapons from this line
        weapons.extend(_parse_weapon_line(line, category))

    return weapons


def _parse_weapon_line(text: str, category: str) -> list[dict]:
    """Parse a packed line of weapon data into individual weapon records."""
    weapons = []
    remaining = text.strip()

    while remaining:
        # Skip leading spaces
        remaining = remaining.strip()
        if not remaining or not re.search(r"\d+D\d+", remaining):
            break

        weapon, remaining = _extract_one_weapon(remaining, category)
        if weapon:
            weapons.append(weapon)
        else:
            # Can't parse, skip ahead
            break

    return weapons


def _extract_one_weapon(text: str, category: str) -> tuple[dict | None, str]:
    """Extract a single weapon from the start of text. Returns (weapon, remaining_text)."""
    parts = text.strip().split()
    if len(parts) < 5:
        return None, ""

    weapon = {"类别": category}
    idx = 0

    # Find the weapon name: everything before the first skill or damage pattern
    name_end = len(parts)
    for i, p in enumerate(parts):
        if _is_skill(p) or _is_damage(p):
            name_end = i
            break

    name = " ".join(parts[:name_end])
    # Clean trailing punctuation
    name = re.sub(r"[,;,:]$", "", name).strip()
    if not name or len(name) < 2 or re.match(r"^\d|^\$", name):
        return None, " " .join(parts[name_end:]) if name_end < len(parts) else ""

    weapon["名称"] = name
    idx = name_end

    # Next: skill
    if idx < len(parts) and _is_skill(parts[idx]):
        weapon["技能"] = parts[idx]
        idx += 1

    # Next: damage
    if idx < len(parts) and _is_damage(parts[idx]):
        weapon["伤害"] = parts[idx]
        idx += 1

    # Check for 贯穿 flag
    if idx < len(parts) and parts[idx] == "贯穿":
        weapon["贯穿"] = True
        idx += 1

    # Remaining fields
    remaining_parts = parts[idx:]
    _fill_fields(weapon, remaining_parts)

    return weapon, ""


def _fill_fields(weapon: dict, parts: list[str]):
    """Fill optional fields from remaining parts."""
    era_seen = False
    for part in parts:
        if not part:
            continue
        # Range
        if "基础射程" not in weapon and re.search(r"码|STR|触|英尺|米", part):
            weapon["基础射程"] = part
        # ROF
        elif "每轮" not in weapon and re.match(r"^[1\d/\(\)全半单一或]*$", part) and not re.match(r"^\d{2,3}$", part):
            weapon["每轮"] = part
        # Capacity
        elif "装弹量" not in weapon and re.match(r"^\d+$|^一次性|^弹[链带]|^\(", part) and len(part) <= 4:
            weapon["装弹量"] = part
        # Price
        elif "价格" not in weapon and re.match(r"^\$|^N/A|^-/", part):
            weapon["价格"] = part
        # Malfunction
        elif "故障值" not in weapon and re.match(r"^\d{2,3}$", part):
            weapon["故障值"] = part
        # Era (last non-price field)
        elif not era_seen and re.search(r"1920|现[代在]|稀[有少]|二战|古代|中世", part):
            weapon["时代"] = part
            era_seen = True


def _is_skill(part: str) -> bool:
    return bool(re.match(r"^(射击|格斗|投掷|炮术|火焰)", part))


def _is_damage(part: str) -> bool:
    return bool(re.match(r"^\d+D\d+", part))


if __name__ == "__main__":
    weapons = extract_weapons()
    print(f"Extracted {len(weapons)} weapons\n")

    cats = {}
    for w in weapons:
        c = w.get("类别", "?")
        cats[c] = cats.get(c, 0) + 1
    for c, n in sorted(cats.items()):
        print(f"  {c}: {n}")

    out = DATA / "weapons.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(weapons, f, ensure_ascii=False, indent=2)
    print(f"\nSaved ({out.stat().st_size/1024:.0f} KB)")

    for w in weapons[:5]:
        print(f"  [{w.get('类别','?')}] {w.get('名称','?')}: {w.get('伤害','?')}")
