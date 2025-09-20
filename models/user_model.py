from beanie import Document
from pydantic import EmailStr

class User(Document):
    email: EmailStr
    password: str

    class Settings:
        name = "users"
