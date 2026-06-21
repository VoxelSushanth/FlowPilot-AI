"""Authentication routes for FlowPilot AI."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Any

from src.services.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
)
from src.services.auth.services.auth_service import (
    login_user,
    refresh_access_token,
    change_password,
    decode_token,
)
from src.core.dependencies import get_current_user
from src.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    Login user and return JWT tokens.
    
    Uses OAuth2 password flow for compatibility with standard clients.
    """
    access_token, refresh_token, expires_in = await login_user(
        email=form_data.username,
        password=form_data.password
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest) -> Any:
    """
    Refresh access token using refresh token.
    """
    access_token, refresh_token, expires_in = await refresh_access_token(
        request.refresh_token
    )
    
    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )


@router.post("/change-password")
async def change_password_endpoint(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Change user password.
    
    Requires authentication.
    """
    success = await change_password(
        user_id=str(current_user.id),
        current_password=request.current_password,
        new_password=request.new_password
    )
    
    if success:
        return {"message": "Password changed successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to change password"
    )


@router.post("/password-reset/request")
async def request_password_reset(request: PasswordResetRequest) -> Any:
    """
    Request a password reset email.
    
    If the email exists in our system, a reset link will be sent.
    Always returns success to prevent email enumeration.
    """
    # TODO: Implement email sending logic
    # For now, just return success to avoid revealing if email exists
    
    return {
        "message": "If the email exists in our system, a password reset link has been sent."
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirm) -> Any:
    """
    Confirm password reset with token.
    
    TODO: Implement token validation and password reset logic.
    """
    # TODO: Validate token and reset password
    
    return {"message": "Password reset successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current authenticated user information.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "organization_id": str(current_user.organization_id),
        "roles": [role.name for role in current_user.roles],
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat(),
    }
