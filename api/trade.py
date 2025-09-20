from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import datetime
from core.db import get_database
import core.graph_manager as graph_manager
from core.cache import cache, invalidate_cache

router = APIRouter()

@router.post("/new_trade")
@invalidate_cache(pattern="trade:*")
async def new_trade(
    user_a: str,
    item_a: str,
    quantity_a: int,
    item_b: str,
    quantity_b: int
) -> Dict[str, Any]:
    # ...existing code from main.py new_trade endpoint...
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
    try:
        db = await get_database()
        trade_history_collection = db["Trade-History"]
        history_result = await trade_history_collection.insert_one(trade_data.copy())
        item_a_collection = db[item_a]
        item_a_result = await item_a_collection.insert_one(trade_data.copy())
        user_a_collection = db[user_a]
        user_a_result = await user_a_collection.insert_one(trade_data.copy())
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
        
        graph_manager.update_graph_from_trade(trade_data)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 1})
        # return {
        #     "message": "交易建立成功，已完成三個資料庫操作",
        #     "trade_details": trade_data,
        #     "operations_completed": {
        #         "trade_history_id": str(history_result.inserted_id),
        #         "item_a_collection_id": str(item_a_result.inserted_id),
        #         "user_a_collection_id": str(user_a_result.inserted_id),
        #         "swapped_data_id": str(swapped_result.inserted_id),
        #         "user_b_collection_id": str(user_b_result.inserted_id)
        #     },
        #     "database_info": {
        #         "database": "2025-MeiChu",
        #         "collections_used": [
        #             "Trade-History",
        #             item_a
        #         ]
        #     }
        # }
    except Exception as e:
        # return {
        #     "error": "資料庫操作失敗",
        #     "details": str(e),
        #     "trade_details": trade_data
        # }
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 0})

@router.get("/")
async def root():
    return {
        "message": "交易系統 API 正在運行",
        "database_status": "已連接到 MongoDB Atlas",
        "database_name": "2025-MeiChu"
    }

@router.get("/collections")
@cache(ttl=600, key_prefix="trade:collections")
async def get_collections():
    try:
        db = await get_database()
        collections = await db.list_collection_names()
        return {
            "database": "2025-MeiChu",
            "collections": collections,
            "total_collections": len(collections)
        }
    except Exception as e:
        return {"error": "無法取得集合清單", "details": str(e)}

@router.get("/trade-history")
@cache(ttl=300, key_prefix="trade:history")
async def get_trade_history(target: str = "", user: str = "", limit: int = -1):
    try:
        db = await get_database()
        if target != "":
            trade_history_collection = db[target]
        elif user != "":
            trade_history_collection = db[user]
        else:
            trade_history_collection = db["Trade-History"]
        cursor = trade_history_collection.find().sort("timestamp", -1).limit(limit) if limit > 0 else trade_history_collection.find().sort("timestamp", -1)
        trades = []
        async for trade in cursor:
            trade["_id"] = str(trade["_id"])
            trades.append(trade)
        return {
            "trade_history": trades,
            "count": len(trades)
        }
    except Exception as e:
        return {"error": "無法取得交易歷史", "details": str(e)}

@router.get("/recent-items")
@cache(ttl=300, key_prefix="trade:recent_items")
async def get_recent_items(user: str, limit: int = -1):
    try:
        db = await get_database()
        user_collection = db[user]
        cursor = user_collection.find().sort("timestamp", -1).limit(limit) if limit > 0 else user_collection.find().sort("timestamp", -1)
        recent_items = []
        recent_items_set = set()
        async for trade in cursor:
            if trade["item_a"] not in recent_items_set:
                recent_items.append({"item": trade["item_a"]})
                recent_items_set.add(trade["item_a"])
        return {
            "user": user,
            "recent_items": recent_items,
            "count": len(recent_items)
        }
    except Exception as e:
        return {"error": f"無法取得使用者 '{user}' 的最近交易物品", "details": str(e)}

@router.get("/get-all-items")
@cache(ttl=600, key_prefix="trade:all_items")
async def get_all_items():
    try:
        db = await get_database()
        collections = await db.list_collection_names()
        item_collections = [col for col in collections if col not in ["Trade-History"] and not col.startswith("user_")]
        return {
            "total_items": len(item_collections),
            "items": item_collections
        }
    except Exception as e:
        return {"error": "無法取得所有物品清單", "details": str(e)}

@router.get("/most-freq-trade")
@cache(ttl=300, key_prefix="trade:freq_trade")
async def get_most_frequent_trades(target: str = "", limit: int = -1):
    try:
        db = await get_database()
        if target:
            # 指定 target，統計該物品
            if target not in graph_manager.graph:
                return {
                    "error": f"物品 '{target}' 不存在於交易圖中",
                    "target_item": target,
                    "trade_pairs": []
                }
            target_collection = db[target]
            pipeline = [
                {"$group": {"_id": {"$cond": [ {"$eq": ["$item_a", target]}, "$item_b", "$item_a"]}, "count": {"$sum": 1}, "rates": {"$push": {"$cond": [ {"$eq": ["$item_a", target]}, {"$divide": ["$quantity_b", "$quantity_a"]}, {"$divide": ["$quantity_a", "$quantity_b"]} ]}, }, "timestamps": {"$push": "$timestamp"} }},
                {"$match": {"_id": {"$ne": None}}},
                {"$sort": {"count": -1}},
            ]
            if limit > 0:
                pipeline.append({"$limit": limit})
            cursor = target_collection.aggregate(pipeline)
            aggregation_results = await cursor.to_list(length=None)
            trade_pairs = []
            for result in aggregation_results:
                trade_to = result["_id"]
                count = result["count"]
                paths = graph_manager.find_trade_path(target, trade_to, max_depth=3)
                recommended_rate = 0.0
                if paths:
                    recommended_rate = graph_manager.calculate_recommand_rate(paths)
                historical_rates = result.get("rates", [])
                historical_avg = sum(historical_rates) / len(historical_rates) if historical_rates else 0.0
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
        else:
            # 不指定 target，統計所有物品
            trade_history_collection = db["Trade-History"]
            pipeline = [
                {"$group": {
                    "_id": "$item_a",
                    "count": {"$sum": 1},
                    "rates": {"$push": {"$divide": ["$quantity_b", "$quantity_a"]}},
                    "timestamps": {"$push": "$timestamp"}
                }},
                {"$match": {"_id": {"$ne": None}}},
                {"$sort": {"count": -1}},
            ]
            if limit > 0:
                pipeline.append({"$limit": limit})
            cursor = trade_history_collection.aggregate(pipeline)
            aggregation_results = await cursor.to_list(length=None)
            trade_pairs = []
            for result in aggregation_results:
                item = result["_id"]
                count = result["count"]
                historical_rates = result.get("rates", [])
                historical_avg = sum(historical_rates) / len(historical_rates) if historical_rates else 0.0
                rate_stats = {
                    "historical_average": historical_avg,
                    "historical_min": min(historical_rates) if historical_rates else 0.0,
                    "historical_max": max(historical_rates) if historical_rates else 0.0
                }
                trade_pair = {
                    "item": item,
                    "count": count,
                    "rate_statistics": rate_stats
                }
                trade_pairs.append(trade_pair)
            return {
                "total_items": len(trade_pairs),
                "trade_pairs": trade_pairs
            }
    except Exception as e:
        return {
            "error": "無法取得最頻繁交易資料", 
            "details": str(e),
            "target_item": target,
            "trade_pairs": []
        }

@router.get("/graph/path/{start_item}/{target_item}")
@cache(ttl=600, key_prefix="trade:graph_path")
async def find_trade_path(start_item: str, target_item: str, max_depth: int = 5):
    paths = graph_manager.find_trade_path(start_item, target_item, max_depth)
    recommand_rate = graph_manager.calculate_recommand_rate(paths)
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
