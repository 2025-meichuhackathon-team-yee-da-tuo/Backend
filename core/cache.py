import asyncio
import hashlib
import inspect
from functools import wraps
from typing import Any, Callable, Optional, Union, Dict, List
from datetime import timedelta, datetime
import json

from .redis_client import redis_client, DateTimeEncoder

class CacheConfig:
    """快取配置類別"""
    
    def __init__(
        self,
        ttl: int = 300, 
        key_prefix: str = "",
        include_args: bool = True,
        include_kwargs: bool = True,
        exclude_params: Optional[List[str]] = None,
        cache_condition: Optional[Callable] = None
    ):
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.include_args = include_args
        self.include_kwargs = include_kwargs
        self.exclude_params = exclude_params or []
        self.cache_condition = cache_condition

def generate_cache_key(
    func_name: str,
    args: tuple,
    kwargs: dict,
    config: CacheConfig
) -> str:
    """生成快取鍵"""
    key_parts = [config.key_prefix, func_name] if config.key_prefix else [func_name]
    
    
    if config.include_args and args:
       
        filtered_args = args[1:] if args and hasattr(args[0], '__dict__') else args
        if filtered_args:
            key_parts.append(str(hash(str(filtered_args))))
    
    if config.include_kwargs and kwargs:
       
        filtered_kwargs = {
            k: v for k, v in kwargs.items() 
            if k not in config.exclude_params
        }
        if filtered_kwargs:
            key_parts.append(str(hash(str(sorted(filtered_kwargs.items())))))
    
    return ":".join(key_parts)

def cache(
    ttl: int = 300,
    key_prefix: str = "",
    include_args: bool = True,
    include_kwargs: bool = True,
    exclude_params: Optional[List[str]] = None,
    cache_condition: Optional[Callable] = None
):
    """
    快取裝飾器
    
    Args:
        ttl: 快取存活時間（秒）
        key_prefix: 鍵前綴
        include_args: 是否包含位置參數
        include_kwargs: 是否包含關鍵字參數
        exclude_params: 排除的參數名稱列表
        cache_condition: 快取條件函數，返回 True 時才快取
    """
    def decorator(func: Callable) -> Callable:
        config = CacheConfig(
            ttl=ttl,
            key_prefix=key_prefix,
            include_args=include_args,
            include_kwargs=include_kwargs,
            exclude_params=exclude_params,
            cache_condition=cache_condition
        )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            
            if config.cache_condition and not config.cache_condition(*args, **kwargs):
                return await func(*args, **kwargs)
            
            
            cache_key = generate_cache_key(func.__name__, args, kwargs, config)
            
            
            cached_result = await redis_client.get(cache_key)
            if cached_result is not None:
                print(f"🎯 快取命中: {cache_key}")
                return cached_result
            
            
            print(f"💾 執行函數並快取: {cache_key}")
            result = await func(*args, **kwargs)
            
            await redis_client.set(cache_key, result, expire=config.ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            
            if config.cache_condition and not config.cache_condition(*args, **kwargs):
                return func(*args, **kwargs)
            
           
            cache_key = generate_cache_key(func.__name__, args, kwargs, config)
            
         
            try:
                import redis
                r = redis.Redis.from_url(redis_client.redis_url, decode_responses=True)
                cached_result = r.get(cache_key)
                if cached_result is not None:
                    print(f"🎯 快取命中: {cache_key}")
                    try:
                        return json.loads(cached_result)
                    except (json.JSONDecodeError, TypeError):
                        return cached_result
            except Exception as e:
                print(f"同步快取讀取錯誤: {e}")
            
           
            print(f"💾 執行函數並快取: {cache_key}")
            result = func(*args, **kwargs)
            
           
            try:
                import redis
                r = redis.Redis.from_url(redis_client.redis_url, decode_responses=True)
                if isinstance(result, (dict, list)):
                    r.setex(cache_key, config.ttl, json.dumps(result, ensure_ascii=False, cls=DateTimeEncoder))
                else:
                    r.setex(cache_key, config.ttl, str(result))
            except Exception as e:
                print(f"同步快取寫入錯誤: {e}")
            
            return result
        
     
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def invalidate_cache(pattern: str = None, key: str = None):
    """
    快取失效裝飾器
    
    Args:
        pattern: 要失效的快取鍵模式
        key: 要失效的具體快取鍵
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if key:
                await redis_client.delete(key)
                print(f"🗑️ 失效快取: {key}")
            elif pattern:
                keys = await redis_client.keys(pattern)
                for k in keys:
                    await redis_client.delete(k)
                print(f"🗑️ 失效快取模式: {pattern} ({len(keys)} 個鍵)")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
       
            try:
                import redis
                r = redis.Redis.from_url(redis_client.redis_url, decode_responses=True)
                if key:
                    r.delete(key)
                    print(f"🗑️ 失效快取: {key}")
                elif pattern:
                    keys = r.keys(pattern)
                    if keys:
                        r.delete(*keys)
                    print(f"🗑️ 失效快取模式: {pattern} ({len(keys)} 個鍵)")
            except Exception as e:
                print(f"同步快取失效錯誤: {e}")
            
            return result
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class CacheManager:
    """快取管理器"""
    
    @staticmethod
    async def clear_all():
        """清空所有快取"""
        await redis_client.flushdb()
        print("🧹 已清空所有快取")
    
    @staticmethod
    async def clear_pattern(pattern: str):
        """清空符合模式的快取"""
        keys = await redis_client.keys(pattern)
        for key in keys:
            await redis_client.delete(key)
        print(f"🧹 已清空快取模式: {pattern} ({len(keys)} 個鍵)")
    
    @staticmethod
    async def get_cache_info():
        """取得快取資訊"""
        keys = await redis_client.keys("*")
        return {
            "total_keys": len(keys),
            "keys": keys[:10] if len(keys) > 10 else keys 
        }
    
    @staticmethod
    async def warm_up_cache(cache_functions: List[Callable]):
        """預熱快取"""
        print("🔥 開始預熱快取...")
        for func in cache_functions:
            try:
                if inspect.iscoroutinefunction(func):
                    await func()
                else:
                    func()
                print(f"✅ 預熱完成: {func.__name__}")
            except Exception as e:
                print(f"❌ 預熱失敗: {func.__name__} - {e}")
        print("🔥 快取預熱完成")


async def get_cached_or_set(
    key: str, 
    fetch_func: Callable, 
    ttl: int = 300
) -> Any:
    """取得快取值，如果不存在則執行函數並快取"""
    cached_value = await redis_client.get(key)
    if cached_value is not None:
        return cached_value

    if inspect.iscoroutinefunction(fetch_func):
        value = await fetch_func()
    else:
        value = fetch_func()
    
    await redis_client.set(key, value, expire=ttl)
    return value
