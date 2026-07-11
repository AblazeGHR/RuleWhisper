"""Weapon table extractor — era-based splitting approach."""
import re, json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent.parent / "data"
ERA_RE = r"(?:1920s[，,]?现代|1920s|现代|稀有|二战|古代|中世纪)"

# Page ranges for each category (approximate, based on appendix structure)
CATEGORY_SECTIONS = [
    (0,   30,  "近战武器"),      # First ~30 weapons on page 372
    (30,  58,  "手枪"),          # Next section
    (58,  82,  "步枪"),          # Rifles
    (82,  95,  "霰弹枪"),        # Shotguns  
    (95,  110, "突击步枪"),      # Assault rifles
    (110, 125, "冲锋枪/突击步枪"),# SMGs
    (125, 135, "机枪"),          # Machine guns
    (135, 145, "爆炸物"),        # Explosives
    (145, 150, "重武器"),        # Heavy weapons
]


def extract_weapons() -> list[dict]:
    txt_path = DATA / "守秘人规则书.txt"
    with open(txt_path, encoding="utf-8") as f:
        data = f.read()

    idx372 = data.find("===== 第 372 页 =====")
    idx379 = data.find("===== 第 379 页 =====")
    section = data[idx372:idx379].replace("\n", " ")

    # Split into weapon rows by era markers
    rows = _split_rows(section)

    # Parse each row
    weapons = []
    for i, row in enumerate(rows):
        # Clean multi-word spacing from line breaks
        row = re.sub(r"\s{2,}", " ", row)
        w = _parse_row(row)
        if w:
            # Assign category by position
            for start, end, cat in CATEGORY_SECTIONS:
                if start <= i < end:
                    w["类别"] = cat
                    break
            else:
                w["类别"] = "其他"

            # Refine by skill for shotgun/misc categories
            skill = w.get("技能", "")
            name = w.get("名称", "")
            if "霰弹" in skill:
                w["类别"] = "霰弹枪"
            if "弓" in skill:
                w["类别"] = "远程武器"
            if "投掷" in skill:
                w["类别"] = "投掷武器"
            if "格斗" in skill or "链锯" in skill or "斗殴" in skill:
                if w["类别"] in ("手枪", "步枪", "霰弹枪", "突击步枪", "冲锋枪/突击步枪"):
                    w["类别"] = "近战武器"
            if "爆破" in skill or "电气" in skill:
                w["类别"] = "爆炸物"
            if "炮术" in skill:
                w["类别"] = "重武器"
            if "榴弹" in name and "霰弹" not in name:
                w["类别"] = "重武器"
            if "信号枪" in name:
                w["类别"] = "其他"

            weapons.append(w)

    return weapons


def _split_rows(section: str) -> list[str]:
    """Split packed text into individual weapon rows by era boundaries."""
    rows = []
    prev_end = 0
    for m in re.finditer(ERA_RE, section):
        end = m.end()
        row = section[prev_end:end].strip()
        prev_end = end
        if re.search(r"\d+D\d+", row) and len(row) > 15:
            # Clean header artifacts (minimal — don't strip content)
            row = re.sub(r'故障值\s*时代', '', row)
            row = re.sub(r'价格\s*20s/现代', '', row)
            row = re.sub(r'20s/现代\s*故障值', '', row)
            row = re.sub(r'名称\s+技能\s+伤害', '', row)
            row = re.sub(r'常规武器', '', row)
            row = re.sub(r'\s{2,}', ' ', row).strip()
            rows.append(row)
    return rows


def _parse_row(row: str) -> dict | None:
    """Parse a single weapon row string."""
    parts = row.split()
    if len(parts) < 3:
        return None

    weapon = {}
    idx = 0

    # Name: collect tokens until skill pattern or damage pattern
    name_parts = []
    while idx < len(parts):
        p = parts[idx]
        if re.match(r"^(射击|格斗|投掷|炮术|火焰|爆破|电气)", p):
            break
        if re.match(r"^\d+D\d+", p):
            break
        name_parts.append(p)
        idx += 1

    name = " ".join(name_parts).strip()
    # Only clean leading spaces, not leading digits
    name = name.strip()
    if not name or len(name) < 2:
        return None
    weapon["名称"] = name

    # Skill
    if idx < len(parts) and re.match(r"^(射击|格斗|投掷|炮术|火焰|爆破|电气)", parts[idx]):
        weapon["技能"] = parts[idx]
        idx += 1

    # Damage (can be multi-part like 2D6/1D6/1D3)
    dmg_parts = []
    while idx < len(parts):
        p = parts[idx]
        if re.match(r"^\d+D\d+", p):
            dmg_parts.append(p)
            idx += 1
        elif dmg_parts and re.match(r"^/\d+D\d+", p):
            dmg_parts.append(p)
            idx += 1
        elif dmg_parts and p.endswith("/") and idx + 1 < len(parts):
            # Split damage like "16号双管霰弹枪 射击(霰弹枪) 2D6+2/1D6+1/1D  4"
            # where "1D" got split: check next part
            next_p = parts[idx + 1]
            if re.match(r"^\d+$", next_p) and len(next_p) <= 2:
                dmg_parts.append(p + next_p.replace(" ", ""))
                idx += 2
                continue
            break
        else:
            break

    if dmg_parts:
        weapon["伤害"] = "".join(dmg_parts)
    else:
        return None

    # Check for 贯穿
    if idx < len(parts) and parts[idx] == "贯穿":
        weapon["贯穿"] = True
        idx += 1

    # Remaining fields
    _fill_fields(weapon, parts[idx:])

    return weapon if weapon.get("技能") and weapon.get("伤害") else None


def _fill_fields(weapon: dict, parts: list[str]):
    """Parse optional fields."""
    for part in parts:
        if not part:
            continue
        if "基础射程" not in weapon and re.search(r"码|STR|触|英尺|米|油", part):
            weapon["基础射程"] = part
        elif "每轮" not in weapon and re.match(r"^[1\d/\(\)全半单一或]+$", part) and not re.match(r"^\d{2,4}$", part):
            weapon["每轮"] = part
        elif "装弹量" not in weapon and re.match(r"^\d+$|^一次性|^弹[链带]|^\(", part) and len(part) <= 4:
            weapon["装弹量"] = part
        elif "价格" not in weapon and re.match(r"^\$|^N/A|^-/", part):
            weapon["价格"] = part
        elif "故障值" not in weapon and re.match(r"^\d{2,3}$", part):
            weapon["故障值"] = part
        elif "时代" not in weapon and re.search(ERA_RE, part):
            weapon["时代"] = part


if __name__ == "__main__":
    weapons = extract_weapons()

    # Dedup
    seen = set()
    unique = []
    for w in weapons:
        name = w.get("名称", "")
        if name and name not in seen:
            seen.add(name)
            unique.append(w)

    print(f"Extracted {len(weapons)}, unique {len(unique)}")

    cats = {}
    for w in unique:
        c = w.get("类别", "?")
        cats[c] = cats.get(c, 0) + 1
    for c, n in sorted(cats.items()):
        print(f"  {c}: {n}")

    out = DATA / "weapons.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f"Saved {out.stat().st_size/1024:.0f} KB")

    print("\nShotguns:")
    for w in unique:
        if w.get("类别") == "霰弹枪":
            print(f"  {w['名称']}: {w.get('伤害','?')}")
