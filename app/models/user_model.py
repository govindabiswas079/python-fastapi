from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class UserModel(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    dob: date
    password: str = Field(min_length=8, max_length=18)
    createdAt: int = int(datetime.timestamp(datetime.now()))
    updatedAt: int = int(datetime.timestamp(datetime.now()))

class VerifyRegisterOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class LoginRequest(BaseModel):
    identifier: str
    password: str


class ForgotPasswordRequest(BaseModel):
    identifier: str


class VerifyForgotPasswordOTPRequest(BaseModel):
    identifier: str
    otp: str = Field(min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    identifier: str
    new_password: str = Field(min_length=8, max_length=18)


class RefreshTokenRequest(BaseModel):
    refresh_token: str
