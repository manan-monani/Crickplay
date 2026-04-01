"""
Authentication Pydantic schemas
Request/response models for authentication endpoints
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# Base schemas
class TenantBase(BaseModel):
    """Base tenant schema"""

    name: str = Field(..., min_length=1, max_length=255)
    subscription_tier: str = Field(
        default="fan", pattern="^(fan|professional|enterprise)$"
    )


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)


# Request schemas
class UserCreate(UserBase):
    """Schema for user registration"""

    password: str = Field(..., min_length=8, max_length=100)
    tenant_name: Optional[str] = Field(
        None, description="Create new tenant with this name"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
                "full_name": "John Doe",
                "tenant_name": "John's Cricket Analytics",
            }
        }
    )


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "SecurePassword123!"}
        }
    )


class TokenRefresh(BaseModel):
    """Schema for refreshing access token"""

    refresh_token: str


# Response schemas
class Token(BaseModel):
    """JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }
    )


class UserResponse(UserBase):
    """Schema for user response"""

    id: UUID
    tenant_id: UUID
    role: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                "role": "professional",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2026-04-01T12:00:00",
                "last_login": "2026-04-01T12:00:00",
            }
        },
    )


class TenantResponse(TenantBase):
    """Schema for tenant response"""

    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "John's Cricket Analytics",
                "subscription_tier": "professional",
                "is_active": True,
                "created_at": "2026-04-01T12:00:00",
            }
        },
    )


class UserWithTenant(UserResponse):
    """Extended user response with tenant information"""

    tenant: TenantResponse

    model_config = ConfigDict(from_attributes=True)


# Token payload schemas (internal use)
class TokenPayload(BaseModel):
    """JWT token payload"""

    sub: str  # User ID
    email: str
    tenant_id: str
    role: str
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    type: str = "access"  # access or refresh
