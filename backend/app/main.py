"""
Crickplay FastAPI Application
T20 Cricket Match Outcome Prediction SaaS Platform
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.db.session import close_db, init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting Crickplay API...")
    await init_db()
    print("Database initialized.")
    yield
    # Shutdown
    await close_db()
    print("Shutting down Crickplay API...")


app = FastAPI(
    title="Crickplay API",
    description="T20 Cricket Match Outcome Prediction SaaS Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Crickplay API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
from app.routers import auth, matches, players, venues, ai_chat

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(matches.router, prefix="/matches", tags=["Matches"])
app.include_router(players.router, prefix="/players", tags=["Players"])
app.include_router(venues.router, prefix="/venues", tags=["Venues"])
app.include_router(ai_chat.router, prefix="/ai", tags=["AI Chat"])
