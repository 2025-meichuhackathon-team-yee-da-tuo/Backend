from pydantic import BaseModel, EmailStr, Field, validator

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
