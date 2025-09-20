import bcrypt
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from models.user_model import User
from models.user_schema import RegisterSchema, LoginSchema

router = APIRouter()

@router.post("/register")
async def register_user(body: RegisterSchema):
    existing_user = await User.find_one(User.email == body.email)
    if existing_user:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 1})

    if len(body.password) < 8:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 2})

    if body.password != body.confirmPassword:
         return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 3})

    hashed_password = bcrypt.hashpw(body.password.encode('utf-8'), bcrypt.gensalt())

    new_user = User(email=body.email, password=hashed_password.decode('utf-8'))
    await new_user.create()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 0})


@router.post("/login")
async def login_user(body: LoginSchema):
    user = await User.find_one(User.email == body.email)
    
    if not user or not bcrypt.checkpw(body.password.encode('utf-8'), user.password.encode('utf-8')):
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 1})

    return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 0})
