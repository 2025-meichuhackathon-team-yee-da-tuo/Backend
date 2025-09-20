#!/usr/bin/env python3

import asyncio
import time
import statistics
from datetime import datetime
from core.cache import cache
from core.redis_client import redis_client
from core.db import get_database

async def real_database_query(query_type: str, params: dict = None):
    """真實的資料庫查詢，包含實際的 MongoDB 操作"""
    from core.db import get_database
    
    db = await get_database()
    
    if query_type == "get-all-items":
        collections = await db.list_collection_names()
        item_collections = [col for col in collections if col not in ["Trade-History"] and not col.startswith("user_")]
        return {
            "query_type": query_type,
            "params": params,
            "data": item_collections,
            "total_items": len(item_collections),
            "timestamp": time.time()
        }
    
    elif query_type == "trade-history":
        user = params.get("user", "") if params else ""
        limit = params.get("limit", -1) if params else -1
        
        if user != "":
            trade_history_collection = db[user]
        else:
            trade_history_collection = db["Trade-History"]
        
        cursor = trade_history_collection.find().sort("timestamp", -1).limit(limit) if limit > 0 else trade_history_collection.find().sort("timestamp", -1)
        trades = []
        async for trade in cursor:
            trade["_id"] = str(trade["_id"])
            trades.append(trade)
        
        return {
            "query_type": query_type,
            "params": params,
            "data": trades,
            "count": len(trades),
            "timestamp": time.time()
        }
    
    elif query_type == "recent-items":
        user = params.get("user", "") if params else ""
        limit = params.get("limit", -1) if params else -1
        
        if not user:
            return {"error": "需要指定使用者"}
        
        user_collection = db[user]
        cursor = user_collection.find().sort("timestamp", -1).limit(limit) if limit > 0 else user_collection.find().sort("timestamp", -1)
        recent_items = []
        recent_items_set = set()
        async for trade in cursor:
            if trade["item_a"] not in recent_items_set:
                recent_items.append({"item": trade["item_a"]})
                recent_items_set.add(trade["item_a"])
        
        return {
            "query_type": query_type,
            "params": params,
            "data": recent_items,
            "count": len(recent_items),
            "timestamp": time.time()
        }
    
    elif query_type == "most-freq-trade":
        target = params.get("target", "") if params else ""
        limit = params.get("limit", -1) if params else -1
        
        if target:
            target_collection = db[target]
            pipeline = [
                {"$group": {"_id": {"$cond": [ {"$eq": ["$item_a", target]}, "$item_b", "$item_a"]}, "count": {"$sum": 1}}},
                {"$match": {"_id": {"$ne": None}}},
                {"$sort": {"count": -1}},
            ]
            if limit > 0:
                pipeline.append({"$limit": limit})
            cursor = target_collection.aggregate(pipeline)
            aggregation_results = await cursor.to_list(length=None)
            trade_pairs = []
            for result in aggregation_results:
                trade_pair = {
                    "trade_to": result["_id"],
                    "count": result["count"]
                }
                trade_pairs.append(trade_pair)
            return {
                "query_type": query_type,
                "params": params,
                "data": trade_pairs,
                "count": len(trade_pairs),
                "timestamp": time.time()
            }
        else:
            trade_history_collection = db["Trade-History"]
            pipeline = [
                {"$group": {"_id": "$item_a", "count": {"$sum": 1}}},
                {"$match": {"_id": {"$ne": None}}},
                {"$sort": {"count": -1}},
            ]
            if limit > 0:
                pipeline.append({"$limit": limit})
            cursor = trade_history_collection.aggregate(pipeline)
            aggregation_results = await cursor.to_list(length=None)
            trade_pairs = []
            for result in aggregation_results:
                trade_pair = {
                    "item": result["_id"],
                    "count": result["count"]
                }
                trade_pairs.append(trade_pair)
            return {
                "query_type": query_type,
                "params": params,
                "data": trade_pairs,
                "count": len(trade_pairs),
                "timestamp": time.time()
            }
    
    elif query_type == "fuzzy-search":
        from api.fuzzy_search import _fetch_all_item_names, _fuzzy_search_core
        
        q = params.get("q", "") if params else ""
        top_k = params.get("top_k", 10) if params else 10
        min_score = params.get("min_score", 0.20) if params else 0.20
        
        items = await _fetch_all_item_names()
        result_list = _fuzzy_search_core(q, items, top_k, min_score)
        
        return {
            "query_type": query_type,
            "params": params,
            "data": result_list,
            "count": len(result_list),
            "timestamp": time.time()
        }
    
    else:
        return {
            "query_type": query_type,
            "params": params,
            "data": f"未知的查詢類型: {query_type}",
            "timestamp": time.time()
        }

@cache(ttl=300, key_prefix="perf_test")
async def cached_database_query(query_type: str, params: dict = None):
    """有快取的資料庫查詢"""
    return await real_database_query(query_type, params)

async def uncached_database_query(query_type: str, params: dict = None):
    """無快取的資料庫查詢"""
    return await real_database_query(query_type, params)

async def test_single_query_performance():
    print("🔍 單次查詢效能測試")
    print("=" * 50)
    
    query_type = "get-all-items"
    params = {"limit": 100}
    
    print("📝 測試無快取查詢...")
    start_time = time.time()
    result1 = await uncached_database_query(query_type, params)
    uncached_time = (time.time() - start_time) * 1000
    print(f"無快取查詢時間: {uncached_time:.2f}ms")
    
    print("\n📝 測試有快取查詢（第一次，快取未命中）...")
    start_time = time.time()
    result2 = await cached_database_query(query_type, params)
    cached_first_time = (time.time() - start_time) * 1000
    print(f"有快取查詢時間（第一次）: {cached_first_time:.2f}ms")
    
    print("\n📝 測試有快取查詢（第二次，快取命中）...")
    start_time = time.time()
    result3 = await cached_database_query(query_type, params)
    cached_second_time = (time.time() - start_time) * 1000
    print(f"有快取查詢時間（第二次）: {cached_second_time:.2f}ms")
    
    # 計算效能提升
    speedup = uncached_time / cached_second_time
    print(f"\n⚡ 效能提升: {speedup:.1f} 倍")
    print(f"時間節省: {uncached_time - cached_second_time:.2f}ms")
    
    return {
        "uncached": uncached_time,
        "cached_first": cached_first_time,
        "cached_second": cached_second_time,
        "speedup": speedup
    }

async def test_batch_query_performance():
    print("\n🔄 批量查詢效能測試")
    print("=" * 50)
    
    queries = [
        ("get-all-items", {"limit": 100}),
        ("trade-history", {"user": "test_user"}),
        ("recent-items", {"user": "test_user", "limit": 50}),
        ("most-freq-trade", {"target": "gold"}),
        ("fuzzy-search", {"q": "藍色籃子", "top_k": 10}),
    ]
    
    print("📝 測試無快取批量查詢...")
    start_time = time.time()
    uncached_results = []
    for query_type, params in queries:
        result = await uncached_database_query(query_type, params)
        uncached_results.append(result)
    uncached_batch_time = (time.time() - start_time) * 1000
    print(f"無快取批量查詢時間: {uncached_batch_time:.2f}ms")
    
    print("\n📝 測試有快取批量查詢（第一次，全部快取未命中）...")
    start_time = time.time()
    cached_first_results = []
    for query_type, params in queries:
        result = await cached_database_query(query_type, params)
        cached_first_results.append(result)
    cached_first_batch_time = (time.time() - start_time) * 1000
    print(f"有快取批量查詢時間（第一次）: {cached_first_batch_time:.2f}ms")
    
    print("\n📝 測試有快取批量查詢（第二次，全部快取命中）...")
    start_time = time.time()
    cached_second_results = []
    for query_type, params in queries:
        result = await cached_database_query(query_type, params)
        cached_second_results.append(result)
    cached_second_batch_time = (time.time() - start_time) * 1000
    print(f"有快取批量查詢時間（第二次）: {cached_second_batch_time:.2f}ms")
    
    # 計算效能提升
    batch_speedup = uncached_batch_time / cached_second_batch_time
    print(f"\n⚡ 批量查詢效能提升: {batch_speedup:.1f} 倍")
    print(f"批量查詢時間節省: {uncached_batch_time - cached_second_batch_time:.2f}ms")
    
    return {
        "uncached_batch": uncached_batch_time,
        "cached_first_batch": cached_first_batch_time,
        "cached_second_batch": cached_second_batch_time,
        "batch_speedup": batch_speedup
    }

async def test_concurrent_performance():
    print("\n🚀 併發查詢效能測試")
    print("=" * 50)
    
    concurrent_queries = 10
    query_type = "get-all-items"
    params = {"limit": 100}
    
    print(f"📝 測試無快取併發查詢（{concurrent_queries} 個）...")
    start_time = time.time()
    uncached_tasks = [uncached_database_query(query_type, params) for _ in range(concurrent_queries)]
    uncached_results = await asyncio.gather(*uncached_tasks)
    uncached_concurrent_time = (time.time() - start_time) * 1000
    print(f"無快取併發查詢時間: {uncached_concurrent_time:.2f}ms")
    
    print(f"\n📝 測試有快取併發查詢（第一次，{concurrent_queries} 個）...")
    start_time = time.time()
    cached_first_tasks = [cached_database_query(query_type, params) for _ in range(concurrent_queries)]
    cached_first_results = await asyncio.gather(*cached_first_tasks)
    cached_first_concurrent_time = (time.time() - start_time) * 1000
    print(f"有快取併發查詢時間（第一次）: {cached_first_concurrent_time:.2f}ms")
    
    print(f"\n📝 測試有快取併發查詢（第二次，{concurrent_queries} 個）...")
    start_time = time.time()
    cached_second_tasks = [cached_database_query(query_type, params) for _ in range(concurrent_queries)]
    cached_second_results = await asyncio.gather(*cached_second_tasks)
    cached_second_concurrent_time = (time.time() - start_time) * 1000
    print(f"有快取併發查詢時間（第二次）: {cached_second_concurrent_time:.2f}ms")
    
    # 計算效能提升
    concurrent_speedup = uncached_concurrent_time / cached_second_concurrent_time
    print(f"\n⚡ 併發查詢效能提升: {concurrent_speedup:.1f} 倍")
    print(f"併發查詢時間節省: {uncached_concurrent_time - cached_second_concurrent_time:.2f}ms")
    
    return {
        "uncached_concurrent": uncached_concurrent_time,
        "cached_first_concurrent": cached_first_concurrent_time,
        "cached_second_concurrent": cached_second_concurrent_time,
        "concurrent_speedup": concurrent_speedup
    }

async def test_real_api_performance():
    print("\n🌐 真實 API 效能測試")
    print("=" * 50)
    
    import httpx
    
    api_endpoints = [
        "http://localhost:8000/api/trade/get-all-items",
        "http://localhost:8000/api/trade/collections",
        "http://localhost:8000/api/cache/info",
    ]
    
    async with httpx.AsyncClient() as client:
        print("📝 測試第一次 API 呼叫（快取未命中）...")
        first_call_times = []
        for endpoint in api_endpoints:
            start_time = time.time()
            try:
                response = await client.get(endpoint)
                end_time = time.time()
                call_time = (end_time - start_time) * 1000
                first_call_times.append(call_time)
                print(f"  {endpoint}: {call_time:.2f}ms")
            except Exception as e:
                print(f"  {endpoint}: 連線失敗 - {e}")
        
        print("\n📝 測試第二次 API 呼叫（快取命中）...")
        second_call_times = []
        for endpoint in api_endpoints:
            start_time = time.time()
            try:
                response = await client.get(endpoint)
                end_time = time.time()
                call_time = (end_time - start_time) * 1000
                second_call_times.append(call_time)
                print(f"  {endpoint}: {call_time:.2f}ms")
            except Exception as e:
                print(f"  {endpoint}: 連線失敗 - {e}")
        
        if first_call_times and second_call_times:
            avg_first = statistics.mean(first_call_times)
            avg_second = statistics.mean(second_call_times)
            api_speedup = avg_first / avg_second
            print(f"\n⚡ API 平均效能提升: {api_speedup:.1f} 倍")
            print(f"API 平均時間節省: {avg_first - avg_second:.2f}ms")
            
            return {
                "first_call_avg": avg_first,
                "second_call_avg": avg_second,
                "api_speedup": api_speedup
            }
    
    return None

async def generate_performance_report(results):
    print("\n📋 效能測試報告")
    print("=" * 60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": results
    }
    
    import json
    with open("cache_performance_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("✅ 效能測試報告已儲存到 cache_performance_report.json")
    
    print("\n🎯 效能測試總結")
    print("-" * 40)
    if "single" in results:
        print(f"單次查詢效能提升: {results['single']['speedup']:.1f} 倍")
    if "batch" in results:
        print(f"批量查詢效能提升: {results['batch']['batch_speedup']:.1f} 倍")
    if "concurrent" in results:
        print(f"併發查詢效能提升: {results['concurrent']['concurrent_speedup']:.1f} 倍")
    if "api" in results and results["api"]:
        print(f"API 查詢效能提升: {results['api']['api_speedup']:.1f} 倍")

async def main():
    print("🚀 快取效能對比測試開始")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    try:
        results["single"] = await test_single_query_performance()
        results["batch"] = await test_batch_query_performance()
        results["concurrent"] = await test_concurrent_performance()
        
        try:
            api_results = await test_real_api_performance()
            if api_results:
                results["api"] = api_results
        except Exception as e:
            print(f"⚠️ 真實 API 測試跳過: {e}")
        
        await generate_performance_report(results)
        
        print("\n🎉 效能測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())
