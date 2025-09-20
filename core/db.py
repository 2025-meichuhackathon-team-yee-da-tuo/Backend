import os
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

# 匯入所有 Beanie Models
from models.user_model import User

async def init_db():
    """初始化資料庫連線"""
    db_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))

    await init_beanie(
        database=db_client.get_default_database(),
        document_models=[
            User,
            # 如果未來有更多 Model，請在此處加入
        ]
    )
