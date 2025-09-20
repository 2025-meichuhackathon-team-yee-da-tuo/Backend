
from fastapi import FastAPI
from core.db import register_db_events
from api.routes import router as api_router

app = FastAPI(title="交易系統 API", description="整合 MongoDB Atlas 的交易處理系統")

# 註冊資料庫啟動/關閉事件
register_db_events(app)

# 掛載 API 路由
app.include_router(api_router)

# 如果直接執行此檔案，啟動服務器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
