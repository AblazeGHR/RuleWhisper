#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wiki 可视化数据审查工具。

读取 data/ 下的结构化 JSON（武器/怪物/法术/技能/规则及其分章文件），
生成零依赖、单文件自包含的静态 HTML 到 docs/wiki/，供人眼审查数据质量。

运行：python docs/wiki/build.py
"""
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # 项目根 = d:/.../ai_coc_wiki
DATA = os.path.join(ROOT, "data")
RULES_DIR = os.path.join(DATA, "rules")
OUT = HERE                                         # docs/wiki
OUT_RULES = os.path.join(OUT, "rules")

PAGES = ["weapons", "monsters", "spells", "skills", "rules"]


# ------------------------------------------------------------------ 工具
def h(text):
    """HTML 转义。"""
    if text is None:
        return ""
    s = str(text)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_list(path):
    d = load(path)
    return d if isinstance(d, list) else []


def data_mtime():
    """数据最新修改时间，用于在首页标注更新时间。"""
    latest = 0.0
    for base, _, files in os.walk(DATA):
        for fn in files:
            if fn.endswith(".json"):
                latest = max(latest, os.path.getmtime(os.path.join(base, fn)))
    return datetime.fromtimestamp(latest) if latest else datetime.now()


# ------------------------------------------------------------------ 模板
CSS = """
:root{--bg:#f7f7f4;--fg:#1f2328;--muted:#6b7280;--line:#e3e3df;
--accent:#7c2d12;--accent2:#92400e;--card:#fff;--tag:#eef2f7;--tagfg:#334155}
*{box-sizing:border-box}
body{margin:0;font:14px/1.6 -apple-system,Segoe UI,Roboto,"Microsoft YaHei",sans-serif;
background:var(--bg);color:var(--fg)}
header{background:var(--accent);color:#fff;padding:14px 22px}
header h1{margin:0;font-size:18px}
header .sub{opacity:.85;font-size:12px;margin-top:2px}
nav{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);
display:flex;flex-wrap:wrap;gap:4px;padding:8px 22px}
nav a{text-decoration:none;color:var(--fg);padding:5px 12px;border-radius:6px;font-size:13px}
nav a:hover{background:var(--tag)}
nav a.active{background:var(--accent);color:#fff}
main{padding:18px 22px;max-width:1180px;margin:0 auto}
h2{font-size:16px;margin:22px 0 10px;color:var(--accent2)}
table{border-collapse:collapse;width:100%;background:var(--card);margin:8px 0 18px;
font-size:13px}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:#f0efe9;font-weight:600;white-space:nowrap}
tr:nth-child(even) td{background:#fafaf8}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
details{border:1px solid var(--line);border-radius:8px;background:var(--card);
margin:10px 0;overflow:hidden}
summary{cursor:pointer;padding:10px 14px;font-weight:600;background:#f0efe9;list-style:none}
summary::-webkit-details-marker{display:none}
summary .cnt{color:var(--muted);font-weight:400;margin-left:6px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}
.card{border:1px solid var(--line);border-radius:10px;background:var(--card);padding:14px 16px}
.card h3{margin:0 0 2px;font-size:15px}
.card .aka{color:var(--muted);font-size:12px;margin-bottom:8px}
.kv{display:grid;grid-template-columns:repeat(2,1fr);gap:2px 14px;font-size:12.5px}
.kv b{color:var(--muted);font-weight:500}
.card .row{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 0;font-size:12.5px}
.tag{display:inline-block;background:var(--tag);color:var(--tagfg);border-radius:4px;
padding:1px 7px;font-size:11.5px;margin:1px}
.search{position:sticky;top:46px;z-index:4;background:var(--bg);padding:8px 0 12px}
.search input{width:100%;max-width:420px;padding:7px 11px;border:1px solid var(--line);
border-radius:7px;font-size:13px}
.note{color:var(--muted);font-size:12px;margin:4px 0 14px}
.empty{color:var(--muted);padding:30px;text-align:center}
footer{color:var(--muted);font-size:12px;padding:14px 22px;border-top:1px solid var(--line)}
"""

def page(title, body, active, updated):
    nav_items = "".join(
        f'<a class="{"active" if p == active else ""}" href="{p}.html">{labels[p]}</a>'
        for p in PAGES)
    nav_items += '<a href="README.html">README</a>' \
                 '<a href="https://github.com/AblazeGHR/RuleWhisper" target="_blank" style="font-weight:700;background:#e8f0fe;color:#1a73e8">⭐ GitHub</a>'
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{h(title)} · RuleWhisper Wiki</title><style>{CSS}</style></head>
<body><header><h1>RuleWhisper 数据 Wiki</h1>
<div class="sub">结构化数据审查 · 数据更新时间 {updated}</div></header>
<nav>{nav_items}</nav><main>{body}</main>
<footer>由 docs/wiki/build.py 自动生成 · 纯静态，无依赖</footer></body></html>"""

labels = {"weapons": "武器", "monsters": "怪物", "spells": "法术",
          "skills": "技能", "rules": "规则"}

JS_FILTER = """
<script>
function filterRows(input, scope){
  var q = input.value.trim().toLowerCase();
  var rows = document.querySelectorAll(scope+' tr[data-search]');
  rows.forEach(function(r){
    r.style.display = (!q || r.getAttribute('data-search').toLowerCase().indexOf(q)>=0) ? '' : 'none';
  });
}
</script>"""

def search_box(scope):
    return (f'<div class="search"><input placeholder="按关键词过滤（名称/标签/机制…）" '
            f'oninput="filterRows(this,\'{scope}\')"></div>')


# ------------------------------------------------------------------ 各页面
def weapons_page():
    rows = load_list(os.path.join(DATA, "weapons.json"))
    if not rows:
        return None, 0
    groups = {}
    for r in rows:
        groups.setdefault(r.get("类别", "未分类"), []).append(r)
    cols = [("名称", "名称"), ("技能", "技能"), ("伤害", "伤害"),
            ("基础射程", "射程"), ("每轮", "每轮"), ("装弹量", "装弹量"),
            ("价格", "价格"), ("故障值", "故障值"), ("时代", "时代")]
    body = "<h2>武器总览</h2><div class='note'>按「类别」折叠，点击分组标题展开/收起。</div>"
    for cat in sorted(groups):
        items = groups[cat]
        body += f"<details open><summary>{h(cat)}<span class='cnt'>{len(items)} 件</span></summary>"
        body += "<table class='mono'><thead><tr>" + "".join(
            f"<th>{h(c)}</th>" for _, c in cols) + "</tr></thead><tbody>"
        for r in items:
            body += "<tr>" + "".join(f"<td>{h(r.get(k,''))}</td>" for k, _ in cols) + "</tr>"
        body += "</tbody></table></details>"
    return body, len(rows)


def monsters_page():
    rows = load_list(os.path.join(DATA, "monsters.json"))
    if not rows:
        return None, 0
    body = "<h2>怪物卡</h2><div class='note'>属性卡片视图，便于核对数值与骰子。</div><div class='cards'>"
    for r in rows:
        name = h(r.get("名称", ""))
        aka = h(r.get("别名", ""))
        def attr(*ks):
            return "".join(f"<span><b>{h(k)}</b> {h(r.get(k,''))}</span>" for k in ks)
        card = f"<div class='card'><h3>{name}</h3>"
        if aka:
            card += f"<div class='aka'>别名：{aka}</div>"
        card += "<div class='kv'>" + attr("STR", "CON", "SIZ", "DEX", "INT", "POW",
                                          "HP", "魔法值", "伤害加值", "体格", "移动", "每回合攻击") + "</div>"
        card += (f"<div class='row'><span><b>格斗</b> {h(r.get('格斗',''))}% "
                 f"(困难 {h(r.get('格斗_困难',''))}/极难 {h(r.get('格斗_极难',''))})</span>"
                 f"<span><b>伤害</b> {h(r.get('格斗_伤害',''))}</span></div>")
        card += (f"<div class='row'><span><b>闪避</b> {h(r.get('闪避',''))}% "
                 f"(困难 {h(r.get('闪避_困难',''))}/极难 {h(r.get('闪避_极难',''))})</span></div>")
        card += f"<div class='row'><span><b>护甲</b> {h(r.get('护甲',''))}</span></div>"
        if r.get("技能"):
            card += f"<div class='row'><span><b>技能</b> {h(r.get('技能',''))}</span></div>"
        if r.get("理智损失"):
            card += f"<div class='row'><span><b>理智损失</b> {h(r.get('理智损失',''))}</span></div>"
        card += "</div>"
        body += card
    body += "</div>"
    return body, len(rows)


def spells_page():
    rows = load_list(os.path.join(DATA, "spells.json"))
    if not rows:
        return None, 0
    body = search_box(".spells") + "<h2>法术列表</h2><table class='spells mono'><thead><tr>" \
           "<th>名称</th><th>消耗</th><th>施法用时</th></tr></thead><tbody>"
    for r in rows:
        s = f"{r.get('名称','')} {r.get('消耗','')} {r.get('施法用时','')}"
        body += f"<tr data-search='{h(s)}'><td>{h(r.get('名称',''))}</td>" \
                f"<td>{h(r.get('消耗',''))}</td><td>{h(r.get('施法用时',''))}</td></tr>"
    body += "</tbody></table>" + JS_FILTER
    return body, len(rows)


def skills_page():
    rows = load_list(os.path.join(DATA, "skills.json"))
    if not rows:
        return None, 0
    body = search_box(".skills") + "<h2>技能表</h2><table class='skills mono'>" \
           "<thead><tr><th>名称</th><th>基础值</th></tr></thead><tbody>"
    for r in rows:
        s = f"{r.get('名称','')} {r.get('基础值','')}"
        body += f"<tr data-search='{h(s)}'><td>{h(r.get('名称',''))}</td>" \
                f"<td>{h(r.get('基础值',''))}</td></tr>"
    body += "</tbody></table>" + JS_FILTER
    return body, len(rows)


def rule_row(r):
    s = " ".join(str(r.get(k, "")) for k in
                 ("id", "标签", "触发条件", "机制效果", "相关检定", "原文引用"))
    tags = "".join(f"<span class='tag'>{h(t)}</span>" for t in r.get("标签", []))
    flow = r.get("判定流程")
    flow = "".join(f"<li>{h(x)}</li>" for x in flow) if isinstance(flow, list) else h(flow)
    cells = [
        f"<td class='mono'>{h(r.get('id',''))}</td>",
        f"<td>{tags or h(r.get('章节',''))}</td>",
        f"<td>{h(r.get('触发条件',''))}</td>",
        f"<td>{h(r.get('机制效果',''))}{(' <br><i>'+h(r.get('特殊规则',''))+'</i>') if r.get('特殊规则') else ''}</td>",
        f"<td>{h('、'.join(r.get('相关检定', [])))}</td>",
        f"<td><ol style='margin:0;padding-left:18px'>{flow}</ol></td>",
        f"<td>{h(r.get('数值','')) or ''}</td>",
        f"<td class='mono'>{h(r.get('页码',''))}</td>",
    ]
    return f"<tr data-search='{h(s)}'>" + "".join(cells) + "</tr>"


RULE_HEAD = ("<th>id</th><th>标签</th><th>触发条件</th><th>机制效果</th>"
             "<th>相关检定</th><th>判定流程</th><th>数值</th><th>页</th>")


def rules_module_page(key, items):
    body = search_box(f".mod-{key}") + f"<h2>{h(key)} 模块（{len(items)} 条）</h2>"
    body += f"<table class='mod-{key} mono'><thead><tr>{RULE_HEAD}</tr></thead><tbody>"
    for r in items:
        body += rule_row(r)
    body += "</tbody></table>" + JS_FILTER
    return body


def rules_index_page():
    rules = load_list(os.path.join(DATA, "rules.json"))
    if not rules:
        return None, 0
    groups = {}
    for r in rules:
        groups.setdefault(r.get("模块", "未分类"), []).append(r)
    body = "<h2>规则索引</h2><div class='note'>按模块分组，点击分组展开查看条目；"
    body += "右侧各模块页提供标签检索。</div>"
    for mod in sorted(groups):
        items = groups[mod]
        body += f"<details><summary>{h(mod)}<span class='cnt'>{len(items)} 条</span></summary>"
        body += "<table class='mono'><thead><tr><th>id</th><th>标签</th><th>触发条件 / 机制效果</th>"
        body += "<th>页</th></tr></thead><tbody>"
        kid = MODULE_KEY.get(mod)
        link = f"<a href='rules/{kid}.html'>详情 →</a>" if kid else "—"
        for r in items:
            s = f"{r.get('id','')} {' '.join(r.get('标签',[]))} {r.get('触发条件','')} {r.get('机制效果','')}"
            tagline = "".join(f"<span class='tag'>{h(t)}</span>" for t in r.get("标签", []))
            body += (f"<tr data-search='{h(s)}'><td class='mono'>{h(r.get('id',''))}</td>"
                     f"<td>{tagline}</td>"
                     f"<td>{h(r.get('触发条件',''))} → {h(r.get('机制效果',''))}</td>"
                     f"<td>{link}</td></tr>")
        body += "</tbody></table></details>"
    body += JS_FILTER
    body = search_box(".idx") + body  # 顶部搜索框作用于索引表
    return body, len(rules)


# 模块字段值 -> 文件名 key（与 data/rules/build.py 保持一致）
MODULE_KEY = {
    "创建调查员": "character_creation", "技能": "skills", "游戏系统": "game_system",
    "幕间成长": "interlude", "战斗": "combat", "追逐": "chase", "理智": "sanity",
    "魔法": "magic", "主持游戏": "keeper", "附录": "appendix",
}


# ------------------------------------------------------------------ 主流程
def main():
    os.makedirs(OUT_RULES, exist_ok=True)
    updated = data_mtime().strftime("%Y-%m-%d %H:%M")

    builders = {
        "weapons": weapons_page, "monsters": monsters_page,
        "spells": spells_page, "skills": skills_page, "rules": rules_index_page,
    }
    built = []
    for name, fn in builders.items():
        body, n = fn()
        if body is None:
            print(f"skip {name}.html (无数据)")
            continue
        html = page(labels[name], body, name, updated)
        with open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        built.append((name, n))
        print(f"build {name}.html  ({n} 条)")

    # 分章规则页：data/rules/<key>.json -> rules/<key>.html
    import glob

    # README.html
    import markdown
    readme_md = os.path.join(ROOT, "README.md")
    if os.path.exists(readme_md):
        with open(readme_md, encoding="utf-8") as f:
            md_text = f.read()
        md_text = md_text.replace("(docs/wiki/)", "(index.html)")
        md_text = md_text.replace("(docs/PLAN.md)", "(https://github.com/AblazeGHR/RuleWhisper/blob/main/docs/PLAN.md)")
        html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
        readme_html = page("README", html_body, "README", updated)
        with open(os.path.join(OUT, "README.html"), "w", encoding="utf-8") as f:
            f.write(readme_html)
        print("build README.html")
    seen = set()
    for path in sorted(glob.glob(os.path.join(RULES_DIR, "*.json"))):
        key = os.path.splitext(os.path.basename(path))[0]
        if key in seen:
            continue
        seen.add(key)
        items = load_list(path)
        if not items:
            continue
        body = rules_module_page(key, items)
        html = page(f"规则·{key}", body, "rules", updated)
        with open(os.path.join(OUT_RULES, f"{key}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        built.append((f"rules/{key}", len(items)))
        print(f"build rules/{key}.html  ({len(items)} 条)")

    # 首页
    cards = "".join(
        f"<div class='card' style='grid-column:span 1'><h3><a href='{n}.html'>{labels[n]}</a></h3>"
        f"<div class='aka'>{n}.html · {c} 条</div></div>" for n, c in built if "/" not in n)
    mod_cards = "".join(
        f"<div class='card' style='grid-column:span 1'><h3><a href='rules/{n.split('/')[1]}.html'>{n.split('/')[1]}</a></h3>"
        f"<div class='aka'>rules/{n.split('/')[1]}.html · {c} 条</div></div>"
        for n, c in built if n.startswith("rules/"))
    idx_body = (f"<h2>数据更新时间 {updated}</h2>"
                "<div class='note'>点击进入各数据审查页。</div>"
                "<h2>总览</h2><div class='cards'>" + cards + mod_cards + "</div>")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page("首页", idx_body, None, updated))
    print("build index.html")
    print("done.")


if __name__ == "__main__":
    main()
