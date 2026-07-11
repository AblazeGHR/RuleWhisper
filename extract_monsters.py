# -*- coding: utf-8 -*-
"""Extract monster data from data/ch14_raw.txt into data/monsters.json.

Handles two stat-block formats:
  * table format  : "属性 平均 掷骰"  (14.1 / 14.3 / 14.4)
  * inline format : "STR.. CON.. SIZ.. DEX.."  (14.2 gods)

Monsters are segmented by "name lines" (intro names + stat-block headers) so
that one monster's text never bleeds into the next.
"""
import re
import json
from pypinyin import lazy_pinyin

SRC = "data/ch14_raw.txt"
OUT = "data/monsters.json"
DEBUG = "extract_debug.txt"

SECTIONS = [
    (661,  "神话生物"),
    (5391, "神话神灵"),
    (9097, "经典妖魔"),
    (9711, "野兽"),
    (10571, "可选规则"),
]


def category_of(lineno):
    cat = "神话生物"
    for start, name in SECTIONS:
        if lineno >= start:
            cat = name
    return cat


def pinyin_id(name, alias=""):
    toks = lazy_pinyin(name)
    s = "".join(toks).lower()
    if alias:
        s += "_" + "".join(lazy_pinyin(alias)).lower()
    s = re.sub(r"[^a-z0-9_]+", "", s)
    return s


lines = open(SRC, encoding="utf-8").read().split("\n")

# ---------------------------------------------------------------------------
# Anchor detection
# ---------------------------------------------------------------------------
anchors = []  # (lineno, fmt)
for i, l in enumerate(lines):
    s = l.strip()
    if s in ("属性 平均 掷骰", "属性 平均值 掷骰"):
        anchors.append((i, "table"))
    elif re.match(r"^STR[\dN]", s):
        anchors.append((i, "god"))

anchor_set = set(a for a, _ in anchors)
is_stat_header = set(a - 1 for a, _ in anchors)  # the line right before an anchor

# ---------------------------------------------------------------------------
# Name-line detection (intro names + stat headers)
# ---------------------------------------------------------------------------
EXCLUDE = {
    "特殊能力", "教团", "其他特性", "术语", "攻击", "神话", "化身", "简介",
    "描述", "历史", "背景", "注意", "备注", "参见", "译注", "弱点", "祭祀",
    "眷族", "教团与祭祀", "旧日支配者", "外神", "蕃神", "邪神", "属性",
    "平均", "掷骰", "伤害加值", "体格", "魔法值", "移动", "每回合", "战斗方式",
    "格斗", "闪避", "躲避", "护甲", "技能", "理智", "法术", "HP", "神话生物",
    "神话诸神", "经典妖魔", "野兽", "可选规则",
}
FIELD_LABELS = [
    "平均伤害加值", "伤害加值", "平均体格", "体格", "平均魔法值", "魔法值",
    "移动", "每回合攻击", "战斗方式", "格斗", "闪避", "躲避", "护甲",
    "技能", "理智损失", "法术",
]


def is_prose(s):
    s = s.strip()
    if len(s) > 15:
        return True
    if s.endswith("。") or "——" in s or "《" in s or "“" in s or '"' in s:
        return True
    return False


def detect_intro_names():
    res = []
    for i, l in enumerate(lines):
        s = l.strip()
        if not s:
            continue
        if i < 661 or i >= 10571:
            continue
        if i in is_stat_header:
            res.append(i)
            continue
        if len(s) < 2 or len(s) > 16:
            continue
        if not re.search(r"[一-鿿]", s):
            continue
        if s[-1] in "。，：:、）)":
            continue
        if "：" in s or ":" in s:
            continue
        if any(ch.isdigit() for ch in s):
            continue
        if s in EXCLUDE or any(t in s for t in EXCLUDE):
            continue
        if any(t in s for t in ("第", "页", "版", "呼唤")):
            continue
        # followed (after blanks) by prose
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines) and is_prose(lines[j]):
            res.append(i)
    return res


intro_names = detect_intro_names()
name_lines = sorted(set(intro_names) | is_stat_header)

# ---------------------------------------------------------------------------
# Build monster spans (merge intro-name segment into following stat-header)
# ---------------------------------------------------------------------------
spans = []  # (start, end, name_text, has_anchor_region)
n = len(name_lines)
i = 0
while i < n:
    start = name_lines[i]
    nxt = name_lines[i + 1] if i + 1 < n else len(lines)
    if (i + 1 < n) and (name_lines[i + 1] in is_stat_header):
        # merge intro name into the stat-block monster
        end = name_lines[i + 2] if i + 2 < n else len(lines)
        name = lines[name_lines[i + 1]].strip()
        spans.append((start, end, name))
        i = i + 2
    else:
        spans.append((start, nxt, lines[start].strip()))
        i += 1

# ---------------------------------------------------------------------------
# Field extraction
# ---------------------------------------------------------------------------
def extract_attr_table(start):
    attrs, dice = {}, {}
    i = start + 1
    pat = re.compile(r"^(STR|CON|SIZ|DEX|INT|POW)\s+([0-9]+|[一-鿿]+|N/A)\s*(.*)$")
    while i < len(lines):
        s = lines[i].strip()
        m = pat.match(s)
        if m:
            key = m.group(1)
            val = m.group(2)
            d = m.group(3).strip().strip("（）()").strip()
            try:
                attrs[key] = int(val)
            except ValueError:
                attrs[key] = val
            if d and d != val and d != "0":
                dice[key] = d
            i += 1
            continue
        if s == "":
            i += 1
            continue
        break  # non-attribute line => end of table
    return attrs, dice


def extract_attr_god(start):
    attrs, dice = {}, {}
    line1 = lines[start].strip()
    line2 = lines[start + 1].strip() if start + 1 < len(lines) else ""
    for kw in ("STR", "CON", "SIZ", "DEX"):
        m = re.search(kw + r"([\dN/A变变化]+)", line1)
        if m:
            v = m.group(1)
            attrs[kw] = int(v) if v.isdigit() else v
    for kw in ("INT", "POW", "HP"):
        m = re.search(kw + r"([\dN/A变变化]+)", line2)
        if m:
            v = m.group(1)
            attrs[kw] = int(v) if v.isdigit() else v
    return attrs, dice


def build_field_index(text):
    idx = {}
    for lab in FIELD_LABELS:
        p = text.find(lab)
        if p != -1:
            idx[lab] = p
    return idx


def capture_field(text, label, idx):
    if label not in idx:
        return None
    start = idx[label] + len(label)
    end = len(text)
    for lab, pos in idx.items():
        if lab == label:
            continue
        if pos > idx[label]:
            end = min(end, pos)
    return text[start:end].strip(" ：:，,\n").strip()


def extract_fields(text):
    idx = build_field_index(text)
    out = {}
    dmg = capture_field(text, "伤害加值", idx) or capture_field(text, "平均伤害加值", idx)
    if dmg:
        out["伤害加值"] = dmg
    build_ = capture_field(text, "体格", idx) or capture_field(text, "平均体格", idx)
    if build_:
        out["体格"] = build_
    mp = capture_field(text, "魔法值", idx) or capture_field(text, "平均魔法值", idx)
    if mp:
        out["魔法值"] = mp
    move = capture_field(text, "移动", idx)
    if move:
        out["移动"] = move
    pr = capture_field(text, "每回合攻击", idx)
    if pr:
        out["每回合攻击"] = pr
    combat = capture_field(text, "战斗方式", idx)
    if combat:
        out["战斗方式"] = combat
    armor = capture_field(text, "护甲", idx)
    if armor:
        out["护甲"] = armor
    skills = capture_field(text, "技能", idx)
    if skills:
        out["技能"] = skills
    sanity = capture_field(text, "理智损失", idx)
    if sanity:
        out["理智损失"] = sanity
    spells = capture_field(text, "法术", idx)
    if spells:
        out["法术"] = spells
    # 格斗
    fm = re.search(r"格斗\s*(\d+)%", text)
    if fm:
        out["格斗"] = int(fm.group(1))
        fstart = fm.end()
        rest = text[fstart:]
        cut = len(rest)
        for lab, pos in idx.items():
            if pos > fm.start() and pos - fm.start() < cut:
                cut = pos - fm.start()
        rest = rest[:cut]
        dm = re.search(r"伤害(.+)$", rest)
        if dm:
            out["格斗_伤害"] = dm.group(1).strip(" ，,（）()")
    # 闪避 / 躲避
    dm = re.search(r"(闪避|躲避)\s*(\d+)%", text)
    if dm:
        out["闪避"] = int(dm.group(2))
    return out


def extract_special(text):
    """Capture 特殊能力 text (from after label until 法术 or end)."""
    sp = text.rfind("特殊能力")
    if sp == -1:
        return None
    tail = text[sp + len("特殊能力"):]
    end = len(tail)
    fp = tail.find("法术")
    if fp != -1:
        end = fp
    val = tail[:end].strip(" ：:，,\n").strip()
    return val or None


def split_name_alias(header):
    header = header.strip()
    if "，" in header:
        name, alias = header.split("，", 1)
        return name.strip(), alias.strip()
    if "," in header:
        name, alias = header.split(",", 1)
        return name.strip(), alias.strip()
    return header, ""


# ---------------------------------------------------------------------------
# Process spans
# ---------------------------------------------------------------------------
results = []
for start, end, htext in spans:
    # anchors inside this span
    span_anchors = [(a, f) for (a, f) in anchors if start <= a < end]
    if not span_anchors:
        # stat-less monster (flavor only)
        flavor = "".join(lines[start:end])
        special = extract_special(flavor)
        sanity = capture_field(flavor, "理智损失", build_field_index(flavor)) if "理智损失" in flavor else None
        spells = capture_field(flavor, "法术", build_field_index(flavor)) if "法术" in flavor else None
        if not (special or sanity or spells):
            continue  # skip non-monster segments (subheaders etc.)
        name, alias = split_name_alias(htext)
        e = {"id": pinyin_id(name, alias), "名称": name, "分类": category_of(start),
             "来源章节": "第十四章 怪物、野兽和神话诸神"}
        if alias:
            e["别名"] = alias
        if special:
            e["特殊能力"] = special
        if sanity:
            e["理智损失"] = sanity
        if spells:
            e["法术"] = spells
        results.append(e)
        continue

    # take the (first) anchor of this span
    ai, fmt = span_anchors[0]
    name, alias = split_name_alias(htext)

    if fmt == "table":
        attrs, dice = extract_attr_table(ai)
    else:
        attrs, dice = extract_attr_god(ai)

    body = "".join(l.strip() for l in lines[ai + 1:end])
    fields = extract_fields(body)

    # 特殊能力 from flavor region [start:ai]
    flavor = "".join(lines[start:ai])
    special = extract_special(flavor)
    # 法术 may be in flavor rather than body
    if "法术" not in fields and "法术" in flavor:
        fidx = build_field_index(flavor)
        sp = capture_field(flavor, "法术", fidx)
        if sp:
            fields["法术"] = sp

    hp = attrs.get("HP")
    if hp is None:
        m = re.search(r"HP[：:]\s*(\d+)", body)
        if m:
            hp = int(m.group(1))

    e = {"id": pinyin_id(name, alias), "名称": name, "分类": category_of(start),
         "属性": attrs, "来源章节": "第十四章 怪物、野兽和神话诸神"}
    if fmt == "table" and dice:
        e["掷骰"] = dice
    if hp is not None:
        e["HP"] = hp
    e.update(fields)
    if special:
        e["特殊能力"] = special
    if alias:
        e["别名"] = alias
    results.append(e)

# de-dup ids
seen = {}
for e in results:
    base = e["id"]
    if base in seen:
        seen[base] += 1
        e["id"] = f"{base}_{seen[base]}"
    else:
        seen[base] = 0

json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

with open(DEBUG, "w", encoding="utf-8") as f:
    f.write(f"intro_names={len(intro_names)} name_lines={len(name_lines)} spans={len(spans)} results={len(results)}\n")
    for s, e, nm in spans:
        f.write(f"{s:5d}-{e:5d}  {nm}\n")

print(f"Extracted {len(results)} entries -> {OUT}")
