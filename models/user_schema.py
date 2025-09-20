from pydantic import BaseModel, EmailStr, Field, model_validator

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirmPassword: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str
