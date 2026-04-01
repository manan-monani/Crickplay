"""
JWT Authentication Service
Token generation, validation, and refresh logic
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from uuid import UUID

from app.config import get_settings
from app.schemas.auth import TokenPayload

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        user_id: UUID,
        email: str,
        tenant_id: UUID,
        role: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create JWT access token

        Args:
            user_id: User's UUID
            email: User's email
            tenant_id: User's tenant UUID
            role: User's role (fan, professional, enterprise, admin)
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode = {
            "sub": str(user_id),
            "email": email,
            "tenant_id": str(tenant_id),
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        user_id: UUID,
        email: str,
        tenant_id: UUID,
        role: str,
    ) -> str:
        """
        Create JWT refresh token

        Args:
            user_id: User's UUID
            email: User's email
            tenant_id: User's tenant UUID
            role: User's role

        Returns:
            Encoded JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": str(user_id),
            "email": email,
            "tenant_id": str(tenant_id),
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[TokenPayload]:
        """
        Decode and validate JWT token

        Args:
            token: JWT token string

        Returns:
            TokenPayload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)

            # Verify expiration
            if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
                return None

            return token_data

        except JWTError:
            return None

    @staticmethod
    def create_tokens(
        user_id: UUID, email: str, tenant_id: UUID, role: str
    ) -> Dict[str, Any]:
        """
        Create both access and refresh tokens

        Returns:
            Dictionary with access_token, refresh_token, token_type, expires_in
        """
        access_token = AuthService.create_access_token(
            user_id=user_id, email=email, tenant_id=tenant_id, role=role
        )

        refresh_token = AuthService.create_refresh_token(
            user_id=user_id, email=email, tenant_id=tenant_id, role=role
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        }


# Singleton instance
auth_service = AuthService()
