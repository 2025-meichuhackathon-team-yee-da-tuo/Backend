#!/usr/bin/env python3
"""
診斷新增交易 API 問題
"""

import asyncio
import datetime
from core.db import get_database
import core.graph_manager as graph_manager

async def debug_new_trade():
    """診斷新增交易問題"""
    print("🔍 診斷新增交易 API 問題")
    print("=" * 50)
    
    # 測試參數
    user_a = "2@t.com"
    item_a = "iPhone"
    quantity_a = 1
    item_b = "CoffeeBean"
    quantity_b = 1000
    
    print(f"測試參數:")
    print(f"  user_a: {user_a}")
    print(f"  item_a: {item_a}")
    print(f"  quantity_a: {quantity_a}")
    print(f"  item_b: {item_b}")
    print(f"  quantity_b: {quantity_b}")
    print()
    
    try:
        # 1. 測試資料庫連線
        print("1. 測試資料庫連線...")
        db = await get_database()
        print("✅ 資料庫連線成功")
        
        # 2. 測試集合是否存在
        print("\n2. 檢查集合...")
        collections = await db.list_collection_names()
        print(f"現有集合: {collections}")
        
        # 3. 測試交易資料建立
        print("\n3. 建立交易資料...")
        user_b = "guess"
        trade_data = {
            "user_a": user_a,
            "item_a": item_a,
            "quantity_a": quantity_a,
            "user_b": user_b,
            "item_b": item_b,
            "quantity_b": quantity_b,
            "rate": quantity_b / quantity_a if quantity_a != 0 else None,
            "timestamp": datetime.datetime.utcnow(),
            "trade_id": f"TRADE_{abs(hash(f'{item_a}{quantity_a}{item_b}{quantity_b}'))}"[:20]
        }
        print(f"交易資料: {trade_data}")
        
        # 4. 測試插入 Trade-History
        print("\n4. 測試插入 Trade-History...")
        trade_history_collection = db["Trade-History"]
        history_result = await trade_history_collection.insert_one(trade_data.copy())
        print(f"✅ Trade-History 插入成功: {history_result.inserted_id}")
        
        # 5. 測試插入 item_a 集合
        print(f"\n5. 測試插入 {item_a} 集合...")
        item_a_collection = db[item_a]
        item_a_result = await item_a_collection.insert_one(trade_data.copy())
        print(f"✅ {item_a} 集合插入成功: {item_a_result.inserted_id}")
        
        # 6. 測試插入 user_a 集合
        print(f"\n6. 測試插入 {user_a} 集合...")
        user_a_collection = db[user_a]
        user_a_result = await user_a_collection.insert_one(trade_data.copy())
        print(f"✅ {user_a} 集合插入成功: {user_a_result.inserted_id}")
        
        # 7. 測試插入 item_b 集合
        print(f"\n7. 測試插入 {item_b} 集合...")
        item_b_collection = db[item_b]
        swapped_trade_data = trade_data.copy()
        swapped_trade_data.update({
            "item_a": item_b,
            "quantity_a": quantity_b,
            "item_b": item_a,
            "quantity_b": quantity_a,
            "rate": quantity_a / quantity_b if quantity_b != 0 else None,
            "is_swapped": True,
            "original_trade_id": trade_data["trade_id"]
        })
        item_b_result = await item_b_collection.insert_one(swapped_trade_data)
        print(f"✅ {item_b} 集合插入成功: {item_b_result.inserted_id}")
        
        # 8. 測試圖形管理器
        print("\n8. 測試圖形管理器...")
        graph_manager.update_graph_from_trade(trade_data)
        print("✅ 圖形管理器更新成功")
        
        print("\n🎉 所有測試通過！新增交易應該可以正常工作")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        print(f"錯誤類型: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_new_trade())
