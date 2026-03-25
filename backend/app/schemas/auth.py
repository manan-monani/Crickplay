"""
Authentication Pydantic Schemas
Request/response models for auth endpoints
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# === Request Schemas ===

class UserRegister(BaseModel):
    """Registration request."""
    email: str = Field(..., max_length=255, description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    full_name: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    """Login request."""
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=128)


class TokenRefresh(BaseModel):
    """Token refresh request."""
    refresh_token: str


# === Response Schemas ===

class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token TTL in seconds")


class UserResponse(BaseModel):
    """Public user profile response."""
    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str] = None
    role: str
    tenant_id: Optional[uuid.UUID] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserWithSubscription(UserResponse):
    """User profile with subscription details."""
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
