#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RuleWhisper Wiki — SPA 构建器。只生成 index.html + data.json。"""
import json, os, glob
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "data", "versions", "v1.0")
RULES_DIR = os.path.join(DATA, "rules")
OUT = HERE

PAGES = ["weapons", "monsters", "spells", "skills", "rules"]
LABELS = {"weapons": "武器", "monsters": "怪物", "spells": "法术",
          "skills": "技能", "rules": "规则"}

MODULE_KEY = {
    "创建调查员": "character_creation", "技能": "skills", "游戏系统": "game_system",
    "幕间成长": "interlude", "战斗": "combat", "追逐": "chase", "理智": "sanity",
    "魔法": "magic", "主持游戏": "keeper", "附录": "appendix",
}

def load_list(path):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except:
        return []

def data_mtime():
    latest = 0.0
    for b, _, fs in os.walk(DATA):
        for fn in fs:
            if fn.endswith(".json"):
                latest = max(latest, os.path.getmtime(os.path.join(b, fn)))
    return datetime.fromtimestamp(latest) if latest else datetime.now()

def main():
    updated = data_mtime().strftime("%Y-%m-%d %H:%M")

    # 收集数据
    weapons = load_list(os.path.join(DATA, "weapons.json"))
    monsters = load_list(os.path.join(DATA, "monsters.json"))
    spells = load_list(os.path.join(DATA, "spells.json"))
    skills = load_list(os.path.join(DATA, "skills.json"))
    rules_all = load_list(os.path.join(DATA, "rules.json"))

    # README 内容
    import markdown, re
    readme_html = ""
    readme_md = os.path.join(ROOT, "README.md")
    if os.path.exists(readme_md):
        with open(readme_md, encoding="utf-8") as f:
            md_text = f.read()
        md_text = md_text.replace("(docs/wiki/)", "(#wiki-data)")
        md_text = md_text.replace("(docs/PLAN.md)", "(https://github.com/AblazeGHR/RuleWhisper/blob/main/docs/PLAN.md)")
        readme_html = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'toc'])
        # 修复 markdown toc 对中文标题的 id 处理
        headings = re.findall(r'<h([2-4])([^>]*)>(.*?)</h\1>', readme_html)
        for level, attrs, content in headings:
            text = re.sub(r'<[^>]+>', '', content).strip()
            # 清理特殊字符用于 id
            clean_id = re.sub(r'[「」""''『』《》（）()？。，！\\s]', '', text)
            old_tag = f'<h{level}{attrs}>{content}</h{level}>'
            new_attrs = re.sub(r'id="[^"]*"', f'id="{clean_id}"', attrs)
            if 'id=' not in new_attrs:
                new_attrs = attrs + f' id="{clean_id}"'
            new_tag = f'<h{level}{new_attrs}>{content}</h{level}>'
            readme_html = readme_html.replace(old_tag, new_tag, 1)
            old_id = re.search(r'id="([^"]*)"', attrs)
            if old_id and old_id.group(1) != clean_id:
                readme_html = readme_html.replace(f'href="#{old_id.group(1)}"', f'href="#{clean_id}"', 1)
        # 同时清理 TOC 链接中的引号，确保与标题 id 匹配
        for m in re.finditer(r'href="#([^"]+)"', readme_html):
            old_href = m.group(1)
            clean_href = re.sub(r'[「」""''『』《》（）()？。，！\\s]', '', old_href)
            if old_href != clean_href:
                readme_html = readme_html.replace(f'href="#{old_href}"', f'href="#{clean_href}"', 1)
        # 为 Wiki 审查区块添加锚点（h3 不自动生成 id）
        readme_html = readme_html.replace('>Wiki 数据审查</a></h3>', '><span id="wiki-data"></span>Wiki 数据审查</a></h3>', 1)
        # 处理 NPC 条目的 id 不一致
        readme_html = readme_html.replace('id="NPC与场景生成"', 'id="npc-与场景生成"')

    rules_modules = {}
    for key, path in sorted((os.path.splitext(os.path.basename(p))[0], p)
                            for p in glob.glob(os.path.join(RULES_DIR, "*.json"))):
        items = load_list(path)
        if items:
            rules_modules[key] = items

    data = {
        "weapons": weapons, "monsters": monsters, "spells": spells,
        "skills": skills, "rules": rules_all, "rules_modules": rules_modules,
        "readme": readme_html, "updated": updated
    }

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    # SPA HTML — 纯前端渲染
    html = HTML_TEMPLATE.replace("{{UPDATED}}", updated)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"SPA built: weapons({len(weapons)}) monsters({len(monsters)}) spells({len(spells)}) skills({len(skills)}) rules({len(rules_all)})")

HTML_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RuleWhisper Wiki</title>
<style>
:root{--bg:#f7f7f4;--fg:#1f2328;--muted:#6b7280;--line:#e3e3df;
--accent:#7c2d12;--accent2:#92400e;--card:#fff;--tag:#eef2f7;--tagfg:#334155}
*{box-sizing:border-box}
body{margin:0;font:14px/1.6 -apple-system,Segoe UI,Roboto,"Microsoft YaHei",sans-serif;background:var(--bg);color:var(--fg)}
header{background:var(--accent);color:#fff;padding:14px 22px}
header h1{margin:0;font-size:18px}
header .sub{opacity:.85;font-size:12px;margin-top:2px}
nav{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:4px;padding:8px 22px}
nav a{text-decoration:none;color:var(--fg);padding:5px 12px;border-radius:6px;font-size:13px;cursor:pointer}
nav a:hover{background:var(--tag)}
nav a.active{background:var(--accent);color:#fff}
main{padding:18px 22px;max-width:1180px;margin:0 auto}
h2{font-size:16px;margin:22px 0 10px;color:var(--accent2)}
table{border-collapse:collapse;width:100%;background:var(--card);margin:8px 0 18px;font-size:13px}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:#f0efe9;font-weight:600;white-space:nowrap}
tr:nth-child(even) td{background:#fafaf8}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
details{border:1px solid var(--line);border-radius:8px;background:var(--card);margin:10px 0;overflow:hidden}
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
.tag{display:inline-block;background:var(--tag);color:var(--tagfg);border-radius:4px;padding:1px 7px;font-size:11.5px;margin:1px}
.search{position:sticky;top:46px;z-index:4;background:var(--bg);padding:8px 0 12px}
.search input{width:100%;max-width:420px;padding:7px 11px;border:1px solid var(--line);border-radius:7px;font-size:13px}
.note{color:var(--muted);font-size:12px;margin:4px 0 14px}
.scroll{overflow-x:auto}
.empty{color:var(--muted);padding:30px;text-align:center}
footer{color:var(--muted);font-size:12px;padding:14px 22px;border-top:1px solid var(--line)}
.mini{border:1px solid var(--line);margin:4px 0;font-size:12px;width:auto}
.mini th,.mini td{border:1px solid var(--line);padding:2px 6px}
.mini th{background:#f0efe9;font-weight:600}
blockquote{border-left:3px solid var(--line);margin:6px 0;padding:4px 12px;color:var(--muted)}
</style>
</head>
<body>
<header><h1>RuleWhisper 数据 Wiki</h1><div class="sub">结构化数据审查 · 更新 {{UPDATED}}</div></header>
<nav id="nav"></nav>
<main id="content"><div class="empty">加载中…</div></main>
<footer>由 docs/wiki/build.py 构建 · SPA 纯前端渲染</footer>
<script>
var PAGE = location.hash.slice(1)||'index';
var LABELS = {weapons:'武器',monsters:'怪物',spells:'法术',skills:'技能',rules:'规则'};
var PAGES = ['weapons','monsters','spells','skills','rules'];

function h(t){return String(t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}

function setActive(page){
  document.querySelectorAll('nav a').forEach(function(a){a.classList.toggle('active',a.getAttribute('data-page')===page)})
  history.replaceState(null,'','#'+page);
}

function render(){var c=document.getElementById('content');var fn=renderers[PAGE];c.innerHTML=fn?fn():(renderers.index?renderers.index():'')}

window.onhashchange=function(){
  var h=location.hash.slice(1);
  if(renderers[h]){PAGE=h;setActive(PAGE);render()}
  else{var el=document.getElementById(h);if(el)el.scrollIntoView({behavior:'smooth'})}
}

// 搜索框
function searchBox(id){return'<div class="search"><input placeholder="按关键词过滤…" oninput="var q=this.value.toLowerCase();document.querySelectorAll(\'#content [data-q]\').forEach(function(r){r.style.display=(!q||(r.getAttribute(\'data-q\')||\'\').indexOf(q)>=0)?\'\':\'none\'})"></div>'}

// 导航
function buildNav(){
  var s=PAGES.map(function(p){return'<a data-page="'+p+'" href="#'+p+'">'+LABELS[p]+'</a>'}).join('');
  s+='<a data-page="readme" href="#readme">README</a>';
  s+='<a href="https://github.com/AblazeGHR/RuleWhisper" target="_blank" style="font-weight:700;background:#e8f0fe;color:#1a73e8">⭐ GitHub</a>';
  document.getElementById('nav').innerHTML=s;
  setActive(PAGE);
}

var DATA=null;
function loadData(){if(DATA)return;var x=new XMLHttpRequest();x.open('GET','data.json',false);x.send();DATA=JSON.parse(x.responseText)}

var renderers={
  index:function(){
    loadData();
    var cards=PAGES.map(function(p){
      var count=DATA[p]?DATA[p].length:0;
      return'<div class="card" style="grid-column:span 1"><h3><a href="#'+p+'">'+LABELS[p]+'</a></h3><div class="aka">'+count+' 条</div></div>'
    }).join('');
    var rc=Object.keys(DATA.rules_modules||{}).map(function(k){
      var n=DATA.rules_modules[k].length;
      return'<div class="card" style="grid-column:span 1"><h3><a href="#rules">规则·'+k+'</a></h3><div class="aka">'+n+' 条</div></div>'
    }).join('');
    return'<h2>数据更新时间 '+DATA.updated+'</h2><div class="note">点击进入各数据审查页。</div><h2>总览</h2><div class="cards">'+cards+rc+'</div>'
  },

  weapons:function(){
    loadData();
    var groups={};DATA.weapons.forEach(function(r){var c=r.类别||'未分类';(groups[c]=groups[c]||[]).push(r)});
    var cols=[['名称','名称'],['技能','技能'],['伤���','伤害'],['基础射程','射程'],['每轮','每轮'],['装弹量','装弹量'],['价格','价格'],['故障值','故障值'],['贯穿','贯穿'],['时代','时代']];
    var s='<h2>武器总览 ('+DATA.weapons.length+' 件)</h2><div class="note">按类别折叠，点击展开/收起。</div>';
    Object.keys(groups).sort().forEach(function(cat){
      var items=groups[cat];
      s+='<details open><summary>'+h(cat)+'<span class="cnt">'+items.length+' 件</span></summary>';
      s+='<table class="mono"><thead><tr>'+cols.map(function(x){return'<th>'+h(x[1])+'</th>'}).join('')+'</tr></thead><tbody>';
      items.forEach(function(r){
        var q=cols.map(function(x){return h(r[x[0]]||'')}).join(' ');
        s+='<tr data-q="'+q+'">'+cols.map(function(x){return'<td>'+h(r[x[0]]||'')+'</td>'}).join('')+'</tr>';
      });
      s+='</tbody></table></details>';
    });
    return searchBox('w')+s;
  },

  monsters:function(){
    loadData();
    var groups={};DATA.monsters.forEach(function(r){var c=r.分类||'未分类';(groups[c]=groups[c]||[]).push(r)});
    var s='<h2>怪物卡 ('+DATA.monsters.length+' 只)</h2><div class="note">按分类折叠，顶部可过滤。</div>';
    Object.keys(groups).sort().forEach(function(cat){
      var items=groups[cat];
      s+='<details open><summary>'+h(cat)+'<span class="cnt">'+items.length+' 只</span></summary><div class="cards">';
      items.forEach(function(r){
        var name=h(r.名称||''),aka=h(r.别名||''),attrs=r.属性||{},dice=r.掷骰||{};
        var q=(r.名称||'')+' '+(r.别名||'')+' '+(r.分类||'')+' '+(r.技能||'')+' '+(r.战斗方式||'')+' '+(r.法术||'')+' '+(r.理智损失||'')+' '+(r.id||'');
        r.特殊能力&&Array.isArray(r.特殊能力)&&(q+=' '+r.特殊能力.join(' '));
        Object.values(attrs).forEach(function(v){q+=' '+v});
        var kv='STR CON SIZ DEX INT POW'.split(' ').map(function(k){return'<span><b>'+k+'</b> '+h(attrs[k]||'—')+(dice[k]?' <i>('+h(dice[k])+')</i>':'')+'</span>'}).join('');
        kv+='HP 魔法值 伤害加值 体格 移动 每回合攻击'.split(' ').map(function(k){return'<span><b>'+k+'</b> '+h(r[k]||'—')+'</span>'}).join('');
        var card='<div class="card" data-q="'+q+'"><h3>'+name+'</h3>';
        if(aka)card+='<div class="aka">别名：'+aka+'</div>';
        card+='<div class="tag" style="margin-bottom:6px">'+h(r.分类||'')+'</div>';
        card+='<div class="kv">'+kv+'</div>';
        if(r.格斗!=null)card+='<div class="row"><span><b>格斗</b> '+h(r.格斗)+'%</span><span><b>伤害</b> '+h(r.格斗_伤害||'')+'</span></div>';
        if(r.闪避!=null)card+='<div class="row"><span><b>闪避</b> '+h(r.闪避)+'%</span></div>';
        card+='<div class="row"><span><b>护甲</b> '+h(r.护甲||'')+'</span></div>';
        ['技能','战斗方式','法术','理智损失'].forEach(function(f){
          var v=r[f];if(typeof v==='object'&&v&&v.length)card+='<div class="row"><span><b>'+f+'</b> '+h(v.join('，'))+'</span></div>';
          else if(v&&v!=='无。')card+='<div class="row"><span><b>'+f+'</b> '+h(v)+'</span></div>';
        });
        var sc=r.特殊能力;if(sc&&Array.isArray(sc)&&sc.length)card+='<div class="row"><b>特殊能力</b></div><div class="row"><ol style="margin:2px 0;padding-left:18px">'+sc.map(function(x){return'<li>'+h(x)+'</li>'}).join('')+'</ol></div>';
        if(r.来源章节)card+='<div class="row"><span class="tag">'+h(r.来源章节)+'</span><span class="tag">'+h(r.id||'')+'</span></div>';
        card+='</div>';
        s+=card;
      });
      s+='</div></details>';
    });
    return searchBox('m')+s;
  },

  spells:function(){
    loadData();
    var s='<h2>法术列表 ('+DATA.spells.length+' 个)</h2><table class="mono"><thead><tr><th>名称</th><th>消耗</th><th>施法用时</th></tr></thead><tbody>';
    DATA.spells.forEach(function(r){
      var q=(r.名称||'')+' '+(r.消耗||'')+' '+(r.施法用时||'');
      s+='<tr data-q="'+q+'"><td>'+h(r.名称||'')+'</td><td>'+h(r.消耗||'')+'</td><td>'+h(r.施法用时||'')+'</td></tr>';
    });
    s+='</tbody></table>';
    return searchBox('s')+s;
  },

  skills:function(){
    loadData();
    var s='<h2>技能表 ('+DATA.skills.length+' 个)</h2><table class="mono"><thead><tr><th>名称</th><th>基础值</th></tr></thead><tbody>';
    DATA.skills.forEach(function(r){
      var q=(r.名称||'')+' '+(r.基础值||'');
      s+='<tr data-q="'+q+'"><td>'+h(r.名称||'')+'</td><td>'+h(r.基础值||'')+'%</td></tr>';
    });
    s+='</tbody></table>';
    return searchBox('sk')+s;
  },

  rules:function(){
    loadData();
    var groups={};DATA.rules.forEach(function(r){var m=r.模块||'未分类';(groups[m]=groups[m]||[]).push(r)});
    var s='<div class="note">点击模块名展开详情。共 '+DATA.rules.length+' 条规则。</div>';
    Object.keys(groups).sort().forEach(function(mod){
      var items=groups[mod];
      var head='<tr><th>id</th><th>标签</th><th>触发条件</th><th>机制效果</th><th>相关检定</th><th>判定流程</th><th>页</th></tr>';
      s+='<details><summary>'+h(mod)+'<span class="cnt">'+items.length+' 条</span></summary>';
      s+='<div class="scroll"><table class="mono"><thead>'+head+'</thead><tbody>';
      items.forEach(function(r){
        var tags=(r.标签||[]).map(function(t){return'<span class="tag">'+h(t)+'</span>'}).join('');
        var flow=r.判定流程;if(Array.isArray(flow))flow='<ol style="margin:0;padding-left:18px">'+flow.map(function(x){return'<li>'+h(x)+'</li>'}).join('')+'</ol>';else flow=h(flow||'');
        var mech=h(r.机制效果||'');
        if(r.特殊规则)mech+=' <br><i>特殊：'+h(r.特殊规则)+'</i>';
        if(r.说明)mech+=' <br><i>说明：'+h(r.说明)+'</i>';
        if(r.原文引用)mech+=' <br><blockquote>「'+h(r.原文引用)+'」</blockquote>';
        var q=(r.id||'')+' '+(r.触发条件||'')+' '+(r.机制效果||'')+' '+(r.原文引用||'')+' '+(r.标签||[]).join(' ')+' '+(r.相关检定||[]).join(' ');
        s+='<tr data-q="'+q+'"><td class="mono">'+h(r.id||'')+'</td><td>'+tags+'</td><td>'+h(r.触发条件||'')+'</td><td>'+mech+'</td><td>'+h((r.相关检定||[]).join('、'))+'</td><td>'+flow+'</td><td class="mono">'+h(r.页码||'')+'</td></tr>';
      });
      s+='</tbody></table></div></details>';
    });
    return searchBox('r')+s;
  },

  readme:function(){
    return DATA.readme||'<div class="empty">README 内容加载失败</div>';
  }
};

buildNav();

buildNav();
loadData();
render();
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
