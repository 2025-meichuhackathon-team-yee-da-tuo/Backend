import os
import bcrypt
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from beanie import init_beanie, Document
from pydantic import BaseModel, EmailStr, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class User(Document):
    email: EmailStr
    password: str

    class Settings:
        name = "users"

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


@app.on_event("startup")
async def app_init():
    db_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    await init_beanie(
        database=db_client.get_default_database(), 
        document_models=[User]
    )


@app.post("/api/auth/register")
async def register_user(body: RegisterSchema):
    if len(body.password) < 8:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 2})

    if body.password != body.confirmPassword:
         return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 3})

    existing_user = await User.find_one(User.email == body.email)
    if existing_user:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 1})

    hashed_password = bcrypt.hashpw(body.password.encode('utf-8'), bcrypt.gensalt())

    new_user = User(email=body.email, password=hashed_password.decode('utf-8'))
    await new_user.create()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 0})


@app.post("/api/auth/login")
async def login_user(body: LoginSchema):
    user = await User.find_one(User.email == body.email)
    
    if not user or not bcrypt.checkpw(body.password.encode('utf-8'), user.password.encode('utf-8')):
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 1})

    return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 0})
