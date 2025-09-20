import os
from fastapi import FastAPI, Body
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import Dict, Any
import datetime

import graph_manager

# 載入環境變數
load_dotenv()

# 建立 FastAPI 應用程式
app = FastAPI(title="交易系統 API", description="整合 MongoDB Atlas 的交易處理系統")

# MongoDB 連線變數
mongodb_client = None
database = None

@app.on_event("startup")
async def startup_db_client():
    """程式啟動時自動連接 MongoDB Atlas"""
    global mongodb_client, database
    
    # 從環境變數取得連線資訊
    username = os.getenv("MONGODB_USERNAME")
    password = os.getenv("MONGODB_PASSWORD")
    cluster = os.getenv("MONGODB_CLUSTER")
    
    if not all([username, password, cluster]):
        raise ValueError("請確認環境變數 MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_CLUSTER 已正確設定")
    
    # 建立 MongoDB Atlas 連線字串
    connection_string = f"mongodb+srv://{username}:{password}@{cluster}"
    print(connection_string)
    
    try:
        # 建立 MongoDB 客戶端連線
        mongodb_client = AsyncIOMotorClient(connection_string)
        
        # 測試連線
        mongodb_client.admin.command('ping')
        
        # 連接到指定的資料庫
        database = mongodb_client["2025-MeiChu"]
        
        print("✅ 成功連接到 MongoDB Atlas!")
        print(f"✅ 已連接到資料庫: 2025-MeiChu")
        await graph_manager.load_trades_from_db(database)
        
    except Exception as e:
        print(f"❌ MongoDB Atlas 連線失敗: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    """程式關閉時斷開 MongoDB 連線"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("🔌 已斷開 MongoDB Atlas 連線")

@app.post("/new_trade")
async def new_trade(
    user_a: str,
    item_a: str,
    quantity_a: int,
    user_b: str,
    item_b: str,
    quantity_b: int
) -> Dict[str, Any]:
    """
    建立新的交易並執行三個資料庫操作：
    1. 存入 Trade-History 集合
    2. 存入以 item_a 命名的集合
    3. 交換 item_a 和 item_b 後存入以原 item_a 命名的集合
    """
    
    # 建立交易資料
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
    
    print("trade_data:", trade_data)
    
    try:
        # 操作 1: 存入 Trade-History 集合
        trade_history_collection = database["Trade-History"]
        history_result = await trade_history_collection.insert_one(trade_data.copy())
        
        # 操作 2: 存入以 item_a 命名的集合
        item_a_collection = database[item_a]
        item_a_result = await item_a_collection.insert_one(trade_data.copy())
        
        user_a_collection = database[user_a]
        user_a_result = await user_a_collection.insert_one(trade_data.copy())
        
        # 操作 3: 交換 item_a 和 item_b，然後存入以原 item_a 命名的集合
        item_b_collection = database[item_b]
        swapped_trade_data = trade_data.copy()
        swapped_trade_data.update({
            "item_a": item_b,      # 原本的 item_b 變成 item_a
            "quantity_a": quantity_b,  # 原本的 quantity_b 變成 quantity_a
            "item_b": item_a,      # 原本的 item_a 變成 item_b
            "quantity_b": quantity_a,  # 原本的 quantity_a 變成 quantity_b
            "rate": quantity_a / quantity_b if quantity_b != 0 else None,  # 更新交換率
            "is_swapped": True,    # 標記為交換過的資料
            "original_trade_id": trade_data["trade_id"]  # 記錄原始交易ID
        })
        
        swapped_result = await item_b_collection.insert_one(swapped_trade_data)
        
        user_b_collection = database[user_b]
        user_b_result = await user_b_collection.insert_one(swapped_trade_data)
        
        graph_manager.update_graph_from_trade(trade_data)
        
        return {
            "message": "交易建立成功，已完成三個資料庫操作",
            "trade_details": trade_data,
            "operations_completed": {
                "trade_history_id": str(history_result.inserted_id),
                "item_a_collection_id": str(item_a_result.inserted_id),
                "user_a_collection_id": str(user_a_result.inserted_id),
                "swapped_data_id": str(swapped_result.inserted_id),
                "user_b_collection_id": str(user_b_result.inserted_id)
            },
            "database_info": {
                "database": "2025-MeiChu",
                "collections_used": [
                    "Trade-History",
                    item_a
                ]
            }
        }
        
    except Exception as e:
        return {
            "error": "資料庫操作失敗",
            "details": str(e),
            "trade_details": trade_data
        }

@app.get("/")
async def root():
    """健康檢查端點"""
    return {
        "message": "交易系統 API 正在運行",
        "database_status": "已連接到 MongoDB Atlas",
        "database_name": "2025-MeiChu"
    }

@app.get("/collections")
async def get_collections():
    """取得資料庫中的所有集合清單"""
    try:
        collections = await database.list_collection_names()
        return {
            "database": "2025-MeiChu",
            "collections": collections,
            "total_collections": len(collections)
        }
    except Exception as e:
        return {"error": "無法取得集合清單", "details": str(e)}

@app.get("/trade-history")
async def get_trade_history(target: str = "", user: str = "", limit: int = 10):
    """取得交易歷史記錄"""
    try:
        if target == "":
            trade_history_collection = database["Trade-History"]
        elif user != "":
            trade_history_collection = database[user]
        else:
            trade_history_collection = database[target]
        cursor = trade_history_collection.find().sort("timestamp", -1).limit(limit)
        
        trades = []
        async for trade in cursor:
            trade["_id"] = str(trade["_id"])  # 轉換 ObjectId 為字串
            trades.append(trade)
        
        return {
            "trade_history": trades,
            "count": len(trades)
        }
    except Exception as e:
        return {"error": "無法取得交易歷史", "details": str(e)}
    
@app.get("/recent-items")
async def get_recent_items(user: str, limit: int = 10):
    """取得指定使用者最近交易的物品清單"""
    try:
        user_collection = database[user]
        cursor = user_collection.find().sort("timestamp", -1).limit(limit)
        
        recent_items = []
        recent_items_set = set()  # 用於避免重複物品
        async for trade in cursor:
            if trade["item_a"] not in recent_items_set:
                recent_items.append({
                    "item": trade["item_a"],
                })
        
        return {
            "user": user,
            "recent_items": recent_items,
            "count": len(recent_items)
        }
    except Exception as e:
        return {"error": f"無法取得使用者 '{user}' 的最近交易物品", "details": str(e)}
    
@app.get("/most-freq-trade")
async def get_most_frequent_trades(target: str, limit: int = 10):
    """
    取得指定物品的最頻繁交易對象，依交易次數排序並包含推薦倍率
    
    Args:
        target: 目標物品名稱
        limit: 回傳結果數量限制
        
    Returns:
        按交易次數排序的交易對象列表，包含推薦倍率
    """
    try:
        # Check if target exists in graph
        if target not in graph_manager.graph:
            return {
                "error": f"物品 '{target}' 不存在於交易圖中",
                "target_item": target,
                "trade_pairs": []
            }
        
        # Get trade history collection for the target item
        target_collection = database[target]
        
        # Use MongoDB aggregation to count trades by trading partner
        pipeline = [
            {
                "$group": {
                    "_id": {
                        # Group by the other item (not the target)
                        "$cond": [
                            {"$eq": ["$item_a", target]}, 
                            "$item_b", 
                            "$item_a"
                        ]
                    },
                    "count": {"$sum": 1},
                    # Also collect all rates for this trading pair for analysis
                    "rates": {
                        "$push": {
                            "$cond": [
                                {"$eq": ["$item_a", target]},
                                {"$divide": ["$quantity_b", "$quantity_a"]},
                                {"$divide": ["$quantity_a", "$quantity_b"]}
                            ]
                        }
                    },
                    # Collect timestamps for weight calculation
                    "timestamps": {"$push": "$timestamp"}
                }
            },
            {
                "$match": {
                    "_id": {"$ne": None}  # Remove null trading partners
                }
            },
            {
                "$sort": {"count": -1}  # Sort by count descending
            },
            {
                "$limit": limit
            }
        ]
        
        # Execute aggregation
        cursor = target_collection.aggregate(pipeline)
        aggregation_results = await cursor.to_list(length=None)
        
        # Process results and add recommended rates from graph path finding
        trade_pairs = []
        
        for result in aggregation_results:
            trade_to = result["_id"]
            count = result["count"]
            
            # Calculate recommended rate using find_trade_path
            paths = graph_manager.find_trade_path(target, trade_to, max_depth=3)
            
            # Calculate weighted average rate from paths
            recommended_rate = 0.0
            if paths:
                recommended_rate = graph_manager.calculate_recommand_rate(paths)
            
            # Calculate historical average rate from database
            historical_rates = result.get("rates", [])
            historical_avg = sum(historical_rates) / len(historical_rates) if historical_rates else 0.0
            
            # Calculate rate statistics
            rate_stats = {
                "recommended_rate": recommended_rate,
                "historical_average": historical_avg,
                "historical_min": min(historical_rates) if historical_rates else 0.0,
                "historical_max": max(historical_rates) if historical_rates else 0.0,
                "path_count": len(paths)
            }
            
            trade_pair = {
                "trade_to": trade_to,
                "count": count,
                "recommend_rate": recommended_rate,
                "rate_statistics": rate_stats
            }
            
            trade_pairs.append(trade_pair)
        
        return {
            "target_item": target,
            "total_trading_pairs": len(trade_pairs),
            "trade_pairs": trade_pairs
        }
        
    except Exception as e:
        return {
            "error": "無法取得最頻繁交易資料", 
            "details": str(e),
            "target_item": target,
            "trade_pairs": []
        }
    
    
@app.get("/graph/path/{start_item}/{target_item}")
async def find_trade_path(start_item: str, target_item: str, max_depth: int = 5):
    """Find all trading paths between two items with exchange rates"""
    paths = graph_manager.find_trade_path(start_item, target_item, max_depth)
    recommand_rate = graph_manager.calculate_recommand_rate(paths)
    print("paths:", paths)
    
    if paths:
        return {
            "start_item": start_item,
            "target_item": target_item,
            "paths_found": len(paths),
            "paths": paths,
            "max_depth": max_depth,
            "recommand_rate": recommand_rate
        }
    else:
        return {
            "start_item": start_item,
            "target_item": target_item,
            "paths_found": 0,
            "paths": [],
            "message": f"No trading paths found from {start_item} to {target_item} within depth {max_depth}"
        }

# 如果直接執行此檔案，啟動服務器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
