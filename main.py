import os
import bcrypt
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from beanie import init_beanie, Document
from pydantic import BaseModel, EmailStr, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# 匯入自訂模組
from core.db import init_db
from api.auth import router as auth_router

# 讀取 .env 環境變數
load_dotenv()

# --- FastAPI 應用程式實例 ---
app = FastAPI()

# --- 資料庫模型 (Beanie ODM) ---
class User(Document):
    email: EmailStr
    password: str

    class Settings:
        name = "users" # MongoDB collection 的名稱

# --- API 請求的資料模型 (Pydantic) ---
class RegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirmPassword: str

    @validator('confirmPassword')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v

class LoginSchema(BaseModel):
    email: EmailStr
    password: str


# --- 資料庫連線 ---
@app.on_event("startup")
async def startup_event():
    """在應用程式啟動時，初始化資料庫連線"""
    await init_db()

# --- 路由掛載 ---
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
