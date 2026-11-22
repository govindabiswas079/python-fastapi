from fastapi import APIRouter, status

from app.models.user_model import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    UserModel,
    VerifyForgotPasswordOTPRequest,
    VerifyRegisterOTPRequest,
)
from app.service.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================== REGISTER ====================

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(request: UserModel):
    return await auth_service.register(request)


# ==================== VERIFY REGISTER OTP ====================

@router.post("/verify-register-otp")
async def verify_register_otp(request: VerifyRegisterOTPRequest):
    return await auth_service.verify_register_otp(
        email=request.email,
        otp=request.otp,
    )


# ==================== LOGIN ====================

@router.post("/login")
async def login(request: LoginRequest):
    return await auth_service.login(
        identifier=request.identifier,
        password=request.password,
    )


@router.post("/refresh")
async def refresh_tokens(request: RefreshTokenRequest):
    return await auth_service.refresh(request.refresh_token)


# ==================== FORGOT PASSWORD ====================

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    return await auth_service.forgot_password(
        identifier=request.identifier,
    )


# ==================== VERIFY FORGOT PASSWORD OTP ====================

@router.post("/verify-forgot-password-otp")
async def verify_forgot_password_otp(
    request: VerifyForgotPasswordOTPRequest,
):
    return await auth_service.verify_forgot_password_otp(
        identifier=request.identifier,
        otp=request.otp,
    )


# ==================== RESET PASSWORD ====================

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    return await auth_service.reset_password(
        identifier=request.identifier,
        new_password=request.new_password,
    )
