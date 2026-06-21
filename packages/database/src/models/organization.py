"""
Organization, User, and Role models for multi-tenancy and access control.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Enum, DateTime, ForeignKey, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ..core.base import BaseModel
from ..core.tenancy import TenantMixin


class OrganizationStatus(enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class UserRoleEnum(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    SALES = "sales"
    WAREHOUSE = "warehouse"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


class Organization(BaseModel):
    """
    Top-level tenant entity.
    
    All other models reference this via organization_id for data isolation.
    """
    __tablename__ = "organizations"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus), 
        default=OrganizationStatus.TRIAL,
        nullable=False
    )
    
    # Business details
    gst_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    pan_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Subscription
    subscription_tier: Mapped[str] = mapped_column(String(50), default="starter")
    subscription_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    subscription_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="organization", lazy="select")
    warehouses = relationship("Warehouse", back_populates="organization", lazy="select")
    
    def is_active(self) -> bool:
        return self.status == OrganizationStatus.ACTIVE
    
    def is_trial(self) -> bool:
        return self.status == OrganizationStatus.TRIAL


class User(BaseModel):
    """
    User account within an organization.
    
    Users belong to exactly one organization and have a specific role.
    """
    __tablename__ = "users"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Access control
    role: Mapped[UserRoleEnum] = mapped_column(Enum(UserRoleEnum), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Last activity
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    
    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    def can_access_organization(self, org_id: int) -> bool:
        """Check if user can access a specific organization."""
        return self.organization_id == org_id or self.is_super_admin


class Role(BaseModel):
    """
    Custom role definition for fine-grained permissions.
    
    Organizations can create custom roles beyond the built-in UserRoleEnum.
    """
    __tablename__ = "roles"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Permissions stored as JSONB in production
    permissions: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    organization = relationship("Organization")
    users = relationship("User", back_populates="organization")  # Simplified


# Association table for many-to-many user-role relationship (if needed)
user_roles = Table(
    "user_roles",
    BaseModel.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class UserRole(BaseModel):
    """
    Junction table for assigning multiple roles to users.
    
    Used when a user needs more than one role in an organization.
    """
    __tablename__ = "user_role_assignments"
    
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False, index=True
    )
    
    assigned_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="NOW()", nullable=False
    )
