from beanie import Document
from pydantic import EmailStr

class User(Document):
    email: EmailStr
    password: str

    class Settings:
        name = "users" # MongoDB collection 的名稱
