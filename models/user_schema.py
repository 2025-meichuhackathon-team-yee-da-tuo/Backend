from pydantic import BaseModel, EmailStr, Field, model_validator

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    confirmPassword: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str
