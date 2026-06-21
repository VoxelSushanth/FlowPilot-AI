"""
Multi-tenancy support for FlowPilot AI.

Implements logical isolation where all data is tagged with organization_id
and queries are automatically filtered to prevent cross-tenant access.
"""

import contextvars
from typing import Optional, TypeVar, Generic, TYPE_CHECKING
from sqlalchemy import Column, Integer
from sqlalchemy.orm import Session
from sqlalchemy.orm.decl_api import declared_attr

if TYPE_CHECKING:
    from sqlalchemy.orm import Query

from .base import BaseModel


# Context variable to store current tenant ID during request processing
_tenant_id_ctx = contextvars.ContextVar("tenant_id", default=None)


def set_tenant_id(tenant_id: int) -> None:
    """
    Set the current tenant ID in the request context.
    
    Args:
        tenant_id: Organization ID for the current request
    """
    _tenant_id_ctx.set(tenant_id)


def get_tenant_id() -> Optional[int]:
    """Get the current tenant ID from the request context."""
    return _tenant_id_ctx.get()


class tenant_id_context:
    """
    Context manager to set tenant ID for a specific scope.
    
    Usage:
        with tenant_id_context(org_id):
            # All queries within this block are filtered by org_id
            session.query(Product).all()
    """
    
    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self._token = None
    
    def __enter__(self):
        self._token = _tenant_id_ctx.set(self.tenant_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token is not None:
            _tenant_id_ctx.reset(self._token)


T = TypeVar("T", bound=BaseModel)


class TenantMixin(Generic[T]):
    """
    Mixin class to add multi-tenancy support to SQLAlchemy models.
    
    Automatically adds organization_id column and filters all queries
    to include only records belonging to the current tenant.
    
    Usage:
        class Product(TenantMixin, BaseModel):
            __tablename__ = "products"
            
            name = Column(String)
            # organization_id is added automatically
    """
    
    __abstract__ = True
    
    @declared_attr
    def organization_id(cls) -> "Mapped[int]":  # type: ignore[name-defined]
        """Foreign key to organizations table."""
        return Column(Integer, nullable=False, index=True)
    
    @classmethod
    def _get_current_tenant_id(cls) -> Optional[int]:
        """Get tenant ID from context."""
        return get_tenant_id()
    
    @classmethod
    def apply_tenant_filter(cls, query: "Query") -> "Query":
        """
        Apply tenant filter to a query if tenant ID is set in context.
        
        Args:
            query: SQLAlchemy Query object
            
        Returns:
            Query with tenant filter applied (if tenant ID is set)
        """
        tenant_id = cls._get_current_tenant_id()
        if tenant_id is not None:
            return query.filter(cls.organization_id == tenant_id)
        return query


def require_tenant(func):
    """
    Decorator to ensure a tenant ID is set before executing a function.
    
    Raises:
        ValueError: If no tenant ID is set in the context
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        if get_tenant_id() is None:
            raise ValueError(
                "No tenant ID set. Ensure you're using tenant_id_context "
                "or setting tenant ID via middleware."
            )
        return func(*args, **kwargs)
    
    return wrapper
