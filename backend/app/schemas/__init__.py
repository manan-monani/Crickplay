"""Schemas package initialization."""

from app.schemas.auth import (
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserWithSubscription,
)
from app.schemas.match import (
    DeliveryResponse,
    MatchFilters,
    MatchSummaryResponse,
    WinProbabilityResponse,
)
from app.schemas.player import (
    FantasyProjectionResponse,
    PlayerResponse,
    PlayerStatsResponse,
)
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    NarrativeResponse,
)

__all__ = [
    # Auth
    "UserRegister",
    "UserLogin",
    "TokenRefresh",
    "TokenResponse",
    "UserResponse",
    "UserWithSubscription",
    # Match
    "MatchSummaryResponse",
    "WinProbabilityResponse",
    "DeliveryResponse",
    "MatchFilters",
    # Player
    "PlayerResponse",
    "PlayerStatsResponse",
    "FantasyProjectionResponse",
    # AI
    "ChatRequest",
    "ChatResponse",
    "NarrativeResponse",
]
