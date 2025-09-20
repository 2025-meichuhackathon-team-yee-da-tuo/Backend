import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

mongodb_client = None
database = None

async def get_database():
    global mongodb_client
    if mongodb_client is None:
        username = os.getenv("MONGODB_USERNAME")
        password = os.getenv("MONGODB_PASSWORD")
        cluster = os.getenv("MONGODB_CLUSTER")
        if not all([username, password, cluster]):
            raise ValueError("請確認環境變數 MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_CLUSTER 已正確設定")
        connection_string = f"mongodb+srv://{username}:{password}@{cluster}"
        mongodb_client = AsyncIOMotorClient(connection_string)
    return mongodb_client["2025-MeiChu"]

# FastAPI lifespan event for startup/shutdown
from fastapi import FastAPI

def register_db_events(app: FastAPI):
    @app.on_event("startup")
    async def startup_db_client():
        db = await get_database()
        await init_database()
        # 可在這裡做初始化，例如載入 graph_manager
        import core.graph_manager as graph_manager
        await graph_manager.load_trades_from_db(db)
        print(database)
        print("✅ 成功連接到 MongoDB Atlas!")
    @app.on_event("shutdown")
    async def shutdown_db_client():
        global mongodb_client
        if mongodb_client:
            mongodb_client.close()
            print("🔌 已斷開 MongoDB Atlas 連線")
async def init_database():
    global database
    database = await get_database()
