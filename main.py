import os
import bcrypt
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from beanie import init_beanie, Document
from pydantic import BaseModel, EmailStr, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

load_dotenv()

from core.db import init_db
from core.limiter import limiter # 匯入 limiter
from api.auth import router as auth_router
from core.db import register_db_events
from api.trade import router as api_router
from api.fuzzy_search import router as fuzzy_search_router

app = FastAPI(
    title="Account DataBase",
    description="Account DataBase for login and register",
    version="1.0.0"
)

# 將 limiter 實例掛載到 app.state
app.state.limiter = limiter
# 新增速率限制異常處理
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def startup_event():
    await init_db()

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
# 註冊資料庫啟動/關閉事件
register_db_events(app)

# 掛載 API 路由
app.include_router(api_router, prefix="/api/trade", tags=["Trading API"])
app.include_router(fuzzy_search_router, prefix="/api/search", tags=["Search API"])

# 如果直接執行此檔案，啟動服務器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
