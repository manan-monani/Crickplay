"""
Authentication Router
Endpoints for user registration, login, token refresh
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.subscription import Subscription
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    UserWithTenant,
)
from app.services.auth_service import auth_service
from app.dependencies.auth import get_current_user

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user

    Creates a new tenant if tenant_name is provided, otherwise user must join existing tenant
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create or get tenant
    if user_data.tenant_name:
        # Create new tenant
        tenant = Tenant(
            id=uuid4(),
            name=user_data.tenant_name,
            subscription_tier="fan",  # Default to fan tier
            is_active=True,
        )
        db.add(tenant)
        await db.flush()  # Get tenant ID

        # Create subscription for tenant
        subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant.id,
            tier="fan",
            rate_limit=100,  # Fan tier limit
            is_active=True,
        )
        db.add(subscription)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_name is required for new registrations",
        )

    # Create user
    hashed_password = auth_service.get_password_hash(user_data.password)
    user = User(
        id=uuid4(),
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        tenant_id=tenant.id,
        role="fan",  # Default role matches tenant tier
        is_active=True,
        is_superuser=False,
    )
    db.add(user)

    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Email may already be in use.",
        )

    # Generate tokens
    tokens = auth_service.create_tokens(
        user_id=user.id, email=user.email, tenant_id=user.tenant_id, role=user.role
    )

    return tokens


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login user and return JWT tokens

    Returns access token (15min) and refresh token (7 days)
    """
    # Fetch user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not auth_service.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Generate tokens
    tokens = auth_service.create_tokens(
        user_id=user.id, email=user.email, tenant_id=user.tenant_id, role=user.role
    )

    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token

    Returns new access token and refresh token
    """
    # Decode refresh token
    token_data = auth_service.decode_token(refresh_data.refresh_token)

    if not token_data or token_data.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user
    from uuid import UUID

    user_id = UUID(token_data.sub)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new tokens
    tokens = auth_service.create_tokens(
        user_id=user.id, email=user.email, tenant_id=user.tenant_id, role=user.role
    )

    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information

    Requires valid access token
    """
    return current_user


@router.get("/me/detailed", response_model=UserWithTenant)
async def get_current_user_detailed(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get current user information with tenant details

    Requires valid access token
    """
    # Eager load tenant relationship
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()

    # Fetch tenant
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == user.tenant_id)
    )
    tenant = tenant_result.scalar_one()
    
    # Pydantic v2 from_attributes handles ORM conversion
    return UserWithTenant.model_validate(user)
