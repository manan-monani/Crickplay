"""
Setup script for creating backend directory structure
"""

import os
from pathlib import Path

# Define directory structure
directories = [
    "backend/app/routers",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/dependencies",
    "backend/app/services",
    "backend/app/db",
    "backend/alembic",
    "backend/tests",
]

init_files = {
    "backend/__init__.py": '"""Backend package"""',
    "backend/app/__init__.py": '"""\nCrickplay Backend API Application\nFastAPI-based backend for Cricket Analytics SaaS platform\n"""\n\n__version__ = "0.1.0"',
    "backend/app/routers/__init__.py": '"""API route handlers"""',
    "backend/app/models/__init__.py": '"""SQLAlchemy ORM models"""',
    "backend/app/schemas/__init__.py": '"""Pydantic schemas for request/response validation"""',
    "backend/app/dependencies/__init__.py": '"""FastAPI dependencies for auth, tenant context, etc."""',
    "backend/app/services/__init__.py": '"""Business logic services"""',
    "backend/app/db/__init__.py": '"""Database configuration and session management"""',
    "backend/tests/__init__.py": '"""Test suite for backend API"""',
}


def setup_backend_structure():
    """Create backend directory structure"""
    base_dir = Path(__file__).parent

    # Create directories
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    # Create __init__.py files
    for file_path, content in init_files.items():
        full_path = base_dir / file_path
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        print(f"Created file: {file_path}")

    print("\n✅ Backend structure created successfully!")


if __name__ == "__main__":
    setup_backend_structure()
