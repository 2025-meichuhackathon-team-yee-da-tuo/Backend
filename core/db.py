import os
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from models.user_model import User

load_dotenv()

async def init_db():
    db_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))

    await init_beanie(
        database=db_client.get_default_database(),
        document_models=[
            User,
        ]
    )
