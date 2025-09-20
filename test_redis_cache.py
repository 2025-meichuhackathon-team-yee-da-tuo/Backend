#!/usr/bin/env python3
"""
Redis 快取系統測試腳本
執行此腳本來測試 Redis 快取功能是否正常運作
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.redis_client import redis_client
from core.cache import cache, CacheManager

async def test_basic_redis_operations():
    """測試基本 Redis 操作"""
    print("🔧 測試基本 Redis 操作...")
    
    try:
        # 連線到 Redis
        await redis_client.connect()
        print("✅ Redis 連線成功!")
        
        # 測試字串操作
        await redis_client.set("test_string", "Hello Redis!", expire=60)
        value = await redis_client.get("test_string")
        assert value == "Hello Redis!", f"字串值不正確: {value}"
        print("✅ 字串操作測試通過")
        
        # 測試 JSON 資料
        test_data = {"name": "測試", "value": 123, "items": [1, 2, 3]}
        await redis_client.set("test_json", test_data, expire=60)
        json_value = await redis_client.get("test_json")
        assert json_value == test_data, f"JSON 資料不正確: {json_value}"
        print("✅ JSON 資料操作測試通過")
        
        # 測試雜湊表操作
        await redis_client.hset("test_hash", {"field1": "value1", "field2": "value2"})
        hash_value = await redis_client.hget("test_hash", "field1")
        assert hash_value == "value1", f"雜湊表值不正確: {hash_value}"
        print("✅ 雜湊表操作測試通過")
        
        # 測試鍵存在檢查
        exists = await redis_client.exists("test_string")
        assert exists, "鍵存在檢查失敗"
        print("✅ 鍵存在檢查測試通過")
        
        # 測試鍵列表
        keys = await redis_client.keys("test_*")
        assert len(keys) >= 3, f"鍵列表不正確: {keys}"
        print("✅ 鍵列表測試通過")
        
        # 清理測試資料
        await redis_client.delete("test_string")
        await redis_client.delete("test_json")
        await redis_client.delete("test_hash")
        print("✅ 測試資料清理完成")
        
    except Exception as e:
        print(f"❌ 基本 Redis 操作測試失敗: {e}")
        raise
    finally:
        await redis_client.disconnect()

async def test_cache_decorator():
    """測試快取裝飾器"""
    print("\n🔧 測試快取裝飾器...")
    
    try:
        await redis_client.connect()
        
        # 定義測試函數
        call_count = 0
        
        @cache(ttl=60, key_prefix="test:decorator")
        async def expensive_operation(param1: str, param2: int = 10):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 模擬耗時操作
            return {
                "param1": param1,
                "param2": param2,
                "call_count": call_count,
                "result": f"處理 {param1} 和 {param2}"
            }
        
        # 第一次呼叫（應該執行函數）
        result1 = await expensive_operation("test", 20)
        assert result1["call_count"] == 1, "第一次呼叫應該執行函數"
        print("✅ 第一次函數呼叫測試通過")
        
        # 第二次呼叫（應該從快取取得）
        result2 = await expensive_operation("test", 20)
        assert result2["call_count"] == 1, "第二次呼叫應該從快取取得"
        assert result1 == result2, "快取結果應該相同"
        print("✅ 快取命中測試通過")
        
        # 不同參數的呼叫（應該執行函數）
        result3 = await expensive_operation("different", 30)
        assert result3["call_count"] == 2, "不同參數應該執行函數"
        print("✅ 不同參數快取測試通過")
        
        # 清理快取
        await CacheManager.clear_pattern("test:*")
        print("✅ 快取清理完成")
        
    except Exception as e:
        print(f"❌ 快取裝飾器測試失敗: {e}")
        raise
    finally:
        await redis_client.disconnect()

async def test_cache_manager():
    """測試快取管理器"""
    print("\n🔧 測試快取管理器...")
    
    try:
        await redis_client.connect()
        
        # 設定一些測試資料
        await redis_client.set("manager:test1", "value1", expire=60)
        await redis_client.set("manager:test2", "value2", expire=60)
        await redis_client.set("other:test3", "value3", expire=60)
        
        # 測試取得快取資訊
        info = await CacheManager.get_cache_info()
        assert info["total_keys"] >= 3, f"快取鍵數量不正確: {info['total_keys']}"
        print("✅ 快取資訊取得測試通過")
        
        # 測試清除特定模式的快取
        await CacheManager.clear_pattern("manager:*")
        remaining_keys = await redis_client.keys("manager:*")
        assert len(remaining_keys) == 0, "模式清除失敗"
        print("✅ 模式清除測試通過")
        
        # 確認其他鍵仍然存在
        other_keys = await redis_client.keys("other:*")
        assert len(other_keys) == 1, "其他鍵被誤刪"
        print("✅ 其他鍵保護測試通過")
        
        # 清理剩餘測試資料
        await CacheManager.clear_all()
        all_keys = await redis_client.keys("*")
        assert len(all_keys) == 0, "全部清除失敗"
        print("✅ 全部清除測試通過")
        
    except Exception as e:
        print(f"❌ 快取管理器測試失敗: {e}")
        raise
    finally:
        await redis_client.disconnect()

async def test_performance():
    """測試效能"""
    print("\n🔧 測試快取效能...")
    
    try:
        await redis_client.connect()
        
        # 測試大量資料寫入
        start_time = asyncio.get_event_loop().time()
        
        for i in range(100):
            await redis_client.set(f"perf:test_{i}", f"value_{i}", expire=60)
        
        write_time = asyncio.get_event_loop().time() - start_time
        print(f"✅ 100 筆資料寫入耗時: {write_time:.3f} 秒")
        
        # 測試大量資料讀取
        start_time = asyncio.get_event_loop().time()
        
        for i in range(100):
            value = await redis_client.get(f"perf:test_{i}")
            assert value == f"value_{i}", f"讀取值不正確: {value}"
        
        read_time = asyncio.get_event_loop().time() - start_time
        print(f"✅ 100 筆資料讀取耗時: {read_time:.3f} 秒")
        
        # 清理效能測試資料
        await CacheManager.clear_pattern("perf:*")
        print("✅ 效能測試資料清理完成")
        
    except Exception as e:
        print(f"❌ 效能測試失敗: {e}")
        raise
    finally:
        await redis_client.disconnect()

async def main():
    """主測試函數"""
    print("🚀 開始 Redis 快取系統測試\n")
    
    # 檢查環境變數
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    print(f"📋 Redis URL: {redis_url}")
    
    try:
        # 執行所有測試
        await test_basic_redis_operations()
        await test_cache_decorator()
        await test_cache_manager()
        await test_performance()
        
        print("\n🎉 所有測試通過！Redis 快取系統運作正常！")
        
    except Exception as e:
        print(f"\n💥 測試失敗: {e}")
        print("\n🔍 故障排除建議:")
        print("1. 確認 Redis 服務正在運行")
        print("2. 檢查 REDIS_URL 環境變數設定")
        print("3. 確認網路連線正常")
        print("4. 檢查 Redis 記憶體使用情況")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
