import os
import bcrypt
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from beanie import init_beanie, Document
from pydantic import BaseModel, EmailStr, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

from core.db import init_db
from api.auth import router as auth_router

app = FastAPI(
    title="Account DataBase",
    description="Account DataBase for login and register",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    await init_db()

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
