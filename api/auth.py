import bcrypt
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

# 匯入 Models
from models.user_model import User
from models.user_schema import RegisterSchema, LoginSchema

router = APIRouter()

@router.post("/register")
async def register_user(body: RegisterSchema):
    """處理使用者註冊"""
    # 檢查密碼長度 (Pydantic Field 已自動處理)
    if len(body.password) < 8:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 2})

    # 檢查兩次密碼是否相符 (Pydantic validator 已自動處理)
    if body.password != body.confirmPassword:
         return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 3})

    # 檢查信箱是否已被註冊
    existing_user = await User.find_one(User.email == body.email)
    if existing_user:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 1})

    # 密碼雜湊
    hashed_password = bcrypt.hashpw(body.password.encode('utf-8'), bcrypt.gensalt())

    # 建立新使用者
    new_user = User(email=body.email, password=hashed_password.decode('utf-8'))
    await new_user.create()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 0})


@router.post("/login")
async def login_user(body: LoginSchema):
    """處理使用者登入"""
    user = await User.find_one(User.email == body.email)
    
    # 檢查使用者是否存在，以及密碼是否正確
    if not user or not bcrypt.checkpw(body.password.encode('utf-8'), user.password.encode('utf-8')):
        return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 1})

    return JSONResponse(status_code=status.HTTP_200_OK, content={"code": 0})
