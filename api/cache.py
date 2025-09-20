from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel

from core.redis_client import redis_client
from core.cache import CacheManager

router = APIRouter()

class CacheKeyRequest(BaseModel):
    key: str

class CacheValueRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = 300

class CachePatternRequest(BaseModel):
    pattern: str

class CacheInfoResponse(BaseModel):
    total_keys: int
    keys: list
    status: str

@router.get("/info", response_model=CacheInfoResponse)
async def get_cache_info():
    try:
        info = await CacheManager.get_cache_info()
        return CacheInfoResponse(
            total_keys=info["total_keys"],
            keys=info["keys"],
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得快取資訊失敗: {str(e)}")

@router.get("/get/{key}")
async def get_cache_value(key: str):
    try:
        value = await redis_client.get(key)
        if value is None:
            raise HTTPException(status_code=404, detail="快取鍵不存在")
        return {"key": key, "value": value, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得快取值失敗: {str(e)}")

@router.post("/set")
async def set_cache_value(request: CacheValueRequest):
    try:
        success = await redis_client.set(request.key, request.value, expire=request.ttl)
        if success:
            return {"key": request.key, "status": "success", "message": "快取值設定成功"}
        else:
            raise HTTPException(status_code=500, detail="快取值設定失敗")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"設定快取值失敗: {str(e)}")

@router.delete("/delete/{key}")
async def delete_cache_value(key: str):
    try:
        success = await redis_client.delete(key)
        if success:
            return {"key": key, "status": "success", "message": "快取值刪除成功"}
        else:
            raise HTTPException(status_code=404, detail="快取鍵不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除快取值失敗: {str(e)}")

@router.post("/clear-pattern")
async def clear_cache_pattern(request: CachePatternRequest):
    try:
        await CacheManager.clear_pattern(request.pattern)
        return {"pattern": request.pattern, "status": "success", "message": "快取模式清空成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空快取模式失敗: {str(e)}")

@router.delete("/clear-all")
async def clear_all_cache():
    try:
        await CacheManager.clear_all()
        return {"status": "success", "message": "所有快取已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空所有快取失敗: {str(e)}")

@router.get("/keys")
async def get_cache_keys(pattern: str = "*"):
    try:
        keys = await redis_client.keys(pattern)
        return {"keys": keys, "count": len(keys), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得快取鍵列表失敗: {str(e)}")

@router.get("/health")
async def cache_health_check():
    try:
        await redis_client.redis.ping()
        return {"status": "healthy", "message": "Redis 連線正常"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis 連線異常: {str(e)}")
