# api/fuzzy_search.py
import os
import time
import asyncio
import inspect
from typing import List, Dict, Any

import numpy as np
from fastapi import APIRouter, Query, HTTPException
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

router = APIRouter()
EMBED_MODEL = os.getenv("SEARCH_EMBED_MODEL", "text-embedding-3-small")  # 1536 維
EMBED_DIM = 1536 if EMBED_MODEL.endswith("small") else 3072
CACHE_TTL = int(os.getenv("SEARCH_EMBED_TTL", "300"))  # 預設 5 分鐘
BATCH_SIZE = int(os.getenv("SEARCH_EMBED_BATCH", "128"))

# ---- OpenAI client (sync) ---------------------------------------------------
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError("OPENAI_API_KEY not set")
client = OpenAI(api_key=_api_key)

# ---- In-memory cache for item embeddings ------------------------------------
_item_cache = {
    "items": None,            # List[str]
    "embeddings": None,       # np.ndarray (N, D)
    "ts": 0.0,                # unix timestamp
}

# ---- Embedding helpers -------------------------------------------------------
def _embed_texts(texts: List[str]) -> np.ndarray:
    """Return shape=(N, D) float32 numpy array."""
    if not texts:
        return np.zeros((0, EMBED_DIM), dtype=np.float32)

    vecs: List[List[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        chunk = texts[i : i + BATCH_SIZE]
        resp = client.embeddings.create(model=EMBED_MODEL, input=chunk)
        for d in resp.data:
            vecs.append(d.embedding)
    return np.asarray(vecs, dtype=np.float32)

def _cosine_sim(q: np.ndarray, M: np.ndarray) -> np.ndarray:
    """q: (D,), M: (N, D) -> sims: (N,)"""
    qn = q / (np.linalg.norm(q) + 1e-8)
    Mn = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-8)
    return Mn @ qn

def _need_refresh(items: List[str]) -> bool:
    if _item_cache["items"] is None or _item_cache["embeddings"] is None:
        return True
    if time.time() - _item_cache["ts"] > CACHE_TTL:
        return True
    # 如果物品清單內容有變，則重算
    return items != _item_cache["items"]

def _get_item_embeddings(items: List[str]) -> np.ndarray:
    if _need_refresh(items):
        emb = _embed_texts(items)
        _item_cache["items"] = items
        _item_cache["embeddings"] = emb
        _item_cache["ts"] = time.time()
    return _item_cache["embeddings"]

# ---- Data source: api.trade.get_all_items -----------------------------------
async def _fetch_all_item_names() -> List[str]:
    """
    呼叫 api.trade.get_all_items() 取得所有 collection 名稱，
    並以字串清單形式回傳。
    """
    from api.trade import get_all_items  # 延遲 import，避免循環依賴
    res = None
    if inspect.iscoroutinefunction(get_all_items):
        res = await get_all_items()
    else:
        res = get_all_items()
        if inspect.isawaitable(res):
            res = await res

    items = []
    if isinstance(res, dict):
        raw = res.get("items", [])
        items = [str(x) for x in raw]
    return items

# ---- Local core (sync) ------------------------------------------------------
def _fuzzy_search_core(query: str, items: List[str], top_k: int, min_score: float) -> List[str]:
    if not items:
        return []

    item_vecs = _get_item_embeddings(items)    # (N, D)
    q_vec = _embed_texts([query])[0]           # (D,)
    sims = _cosine_sim(q_vec, item_vecs)       # (N,)

    order = np.argsort(-sims)
    results: List[str] = []
    for idx in order:
        if len(results) >= top_k:
            break
        if float(sims[idx]) < min_score:
            continue
        results.append(items[idx])
    return results

# ---- API route (GET) --------------------------------------------------------
@router.get("/fuzzy-search")
async def fuzzy_search(
    q: str = Query(..., description="使用者查詢字串（語意模糊搜尋）"),
    top_k: int = Query(10, ge=1, le=100, description="取前 K 筆"),
    min_score: float = Query(0.20, ge=0.0, le=1.0, description="相似度門檻（0~1）"),
) -> List[str]:
    try:
        items = await _fetch_all_item_names()

        # 將同步的 OpenAI 呼叫丟到 ThreadPool，避免阻塞事件圈
        loop = asyncio.get_event_loop()
        result_list: List[str] = await loop.run_in_executor(
            None, lambda: _fuzzy_search_core(q, items, top_k, min_score)
        )
        return result_list
    except Exception as e:
        # 出錯時回 500；若你想改成回空清單，也可把這行改成：return []
        raise HTTPException(status_code=500, detail={"error": "fuzzy_search_failed", "message": str(e)})