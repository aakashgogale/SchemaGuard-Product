"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Schema for authentication response."""

    access_token: str
    user_id: str
    email: str
    username: str | None = None
    is_admin: bool = False


class ChangeEmailRequest(BaseModel):
    """Schema for updating the current user's email."""

    email: EmailStr


class ChangeUsernameRequest(BaseModel):
    """Schema for updating the current user's display username."""

    username: str = Field(min_length=2, max_length=100)


class ChangePasswordRequest(BaseModel):
    """Schema for changing the current user's password."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset."""

    email: EmailStr


class UserProfileResponse(BaseModel):
    """Schema for the current user's profile."""

    id: str
    email: str
    username: str | None = None
    created_at: str
    is_admin: bool = False
