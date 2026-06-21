"""
Base model classes for SQLAlchemy ORM with common fields and utilities.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides:
    - Common metadata configuration
    - Utility methods for serialization
    """
    
    __abstract__ = True
    
    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Args:
            exclude: Set of column names to exclude from output
            
        Returns:
            Dictionary representation of the model
        """
        exclude = exclude or set()
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude
        }
    
    def update(self, **kwargs: Any) -> None:
        """
        Update model attributes from keyword arguments.
        
        Args:
            **kwargs: Attribute names and values to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class BaseModel(Base):
    """
    Abstract base model with common fields for all entities.
    
    Fields:
    - id: Primary key (auto-increment)
    - created_at: Timestamp of record creation
    - updated_at: Timestamp of last update
    - deleted_at: Soft delete timestamp (NULL if active)
    """
    
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft-deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Mark the record as deleted without removing from database."""
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
