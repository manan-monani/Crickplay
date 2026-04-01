"""
SQLAlchemy Base model and declarative base
All ORM models inherit from this base
"""

from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import MetaData
from datetime import datetime
from typing import Any


# Naming convention for constraints
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""

    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically from class name"""
        return cls.__name__.lower()

    def dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary"""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
