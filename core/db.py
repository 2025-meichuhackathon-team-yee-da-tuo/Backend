import os
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from models.user_model import User

load_dotenv()
mongodb_client = None
database = None

async def init_db():
    db_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))

    await init_beanie(
        database=db_client.get_default_database(),
        document_models=[
            User,
        ]
    )
    
    global database
    database = await get_database()

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

from fastapi import FastAPI

def register_db_events(app: FastAPI):
    @app.on_event("startup")
    async def startup_db_client():
        db = await get_database()
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
