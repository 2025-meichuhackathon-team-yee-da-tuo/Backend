import os
import json
import asyncio
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta, datetime
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

class DateTimeEncoder(json.JSONEncoder):
    """自定義 JSON 編碼器，處理 datetime 物件"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

class RedisClient:
    """Redis 客戶端管理類別"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
    async def connect(self):
        """建立 Redis 連線"""
        try:
            self.redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            # 測試連線
            await self.redis.ping()
            print("✅ 成功連接到 Redis!")
        except Exception as e:
            print(f"❌ Redis 連線失敗: {e}")
            raise
    
    async def disconnect(self):
        """關閉 Redis 連線"""
        if self.redis:
            await self.redis.close()
            print("🔌 已斷開 Redis 連線")
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """設定快取值"""
        if not self.redis:
            await self.connect()
        
        try:
            # 將值序列化為 JSON
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False, cls=DateTimeEncoder)
            else:
                serialized_value = str(value)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                return await self.redis.setex(key, expire, serialized_value)
            else:
                return await self.redis.set(key, serialized_value)
        except Exception as e:
            print(f"Redis SET 錯誤: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """取得快取值"""
        if not self.redis:
            await self.connect()
        
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # 嘗試反序列化 JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            print(f"Redis GET 錯誤: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """刪除快取"""
        if not self.redis:
            await self.connect()
        
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            print(f"Redis DELETE 錯誤: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        if not self.redis:
            await self.connect()
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            print(f"Redis EXISTS 錯誤: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """設定過期時間"""
        if not self.redis:
            await self.connect()
        
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            print(f"Redis EXPIRE 錯誤: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """取得符合模式的鍵列表"""
        if not self.redis:
            await self.connect()
        
        try:
            return await self.redis.keys(pattern)
        except Exception as e:
            print(f"Redis KEYS 錯誤: {e}")
            return []
    
    async def flushdb(self) -> bool:
        """清空當前資料庫"""
        if not self.redis:
            await self.connect()
        
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            print(f"Redis FLUSHDB 錯誤: {e}")
            return False
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """設定雜湊表"""
        if not self.redis:
            await self.connect()
        
        try:
            # 序列化值
            serialized_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serialized_mapping[k] = json.dumps(v, ensure_ascii=False, cls=DateTimeEncoder)
                else:
                    serialized_mapping[k] = str(v)
            
            return await self.redis.hset(name, mapping=serialized_mapping)
        except Exception as e:
            print(f"Redis HSET 錯誤: {e}")
            return 0
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """取得雜湊表值"""
        if not self.redis:
            await self.connect()
        
        try:
            value = await self.redis.hget(name, key)
            if value is None:
                return None
            
            # 嘗試反序列化 JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            print(f"Redis HGET 錯誤: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """取得所有雜湊表值"""
        if not self.redis:
            await self.connect()
        
        try:
            data = await self.redis.hgetall(name)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            return result
        except Exception as e:
            print(f"Redis HGETALL 錯誤: {e}")
            return {}

# 全域 Redis 實例
redis_client = RedisClient()
