#!/usr/bin/env python3
"""RuleWhisper HTTP API 层 (P0，Pan 联动方案)。

薄封装现有引擎，不重写逻辑：
  - /api/query  → router.route_query  (自然语言 → 结构化/全文)
  - /api/dice   → dice.resolver.run   (COC7 骰令)
  - /api/weapon|monster|spell|skill/{name} → structured_query
  - /api/rule/{id} → 规则书按页检索
  - /api/health → 健康检查

启动：python -m src.server  (默认 http://127.0.0.1:9731)
端口/主机可用环境变量 RULEWHISPER_HOST / RULEWHISPER_PORT 覆盖。
"""
from __future__ import annotations

import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 确保项目根在 sys.path（无论从哪调用 `python -m src.server`）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dice import resolver as dice_resolver
from src.engine import router, rule_search, structured_query

app = FastAPI(title="RuleWhisper API", version="0.1.0")


# --------------------------------------------------------------------------- #
# 请求/响应模型
# --------------------------------------------------------------------------- #
class TextRequest(BaseModel):
    text: str
    top_k: Optional[int] = None


# --------------------------------------------------------------------------- #
# 序列化辅助
# --------------------------------------------------------------------------- #
def _serialize_route_result(result: dict) -> dict:
    """把 router.route_query 的返回统一成可 JSON 序列化的结构。

    - structured: results 已是 list[dict]
    - keyword_search: results 是 IndexEntry 列表，需转 dict
    """
    source = result.get("source")
    results = result.get("results", [])
    if source == "keyword_search":
        results = [asdict(e) for e in results]
    return {
        "source": source,
        "type": result.get("type"),
        "results": results,
    }


def _serialize_dice(result) -> dict:
    """把 DiceResult 转成可 JSON 序列化的 dict。"""
    return {
        "display": result.display,
        "dice_roll": result.dice_roll,
        "success_level": result.success_level,
        "extra_info": result.extra_info,
    }


# --------------------------------------------------------------------------- #
# 端点
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/query")
def query(req: TextRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(400, "text 不能为空")
    top_k = req.top_k or 10
    result = router.route_query(req.text, top_k=top_k)
    return _serialize_route_result(result)


@app.post("/api/dice")
def dice(req: TextRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(400, "text 不能为空")
    try:
        result = dice_resolver.run(req.text)
    except ValueError as e:
        raise HTTPException(400, f"无效的骰令: {e}")
    return {"text": req.text, **_serialize_dice(result)}


@app.get("/api/weapon/{name}")
def weapon(name: str, top_k: int = 5):
    return structured_query.query_weapons(name, top_k=top_k)


@app.get("/api/monster/{name}")
def monster(name: str, top_k: int = 5):
    return structured_query.query_monsters(name, top_k=top_k)


@app.get("/api/spell/{name}")
def spell(name: str, top_k: int = 5):
    return structured_query.query_spells(name, top_k=top_k)


@app.get("/api/skill/{name}")
def skill(name: str, top_k: int = 5):
    return structured_query.query_skills(name, top_k=top_k)


@app.get("/api/rule/{page}")
def rule(page: int, top_k: int = 5):
    """按规则书页号返回该页段落（page 对应规则书页码）。"""
    if page <= 0:
        raise HTTPException(400, "page 必须为正整数")
    idx = rule_search.get_index()
    paras = [asdict(p) for p in idx._paragraphs if p.page == page]
    if not paras:
        raise HTTPException(404, f"未找到第 {page} 页内容")
    return {"page": page, "paragraphs": paras[:top_k]}
