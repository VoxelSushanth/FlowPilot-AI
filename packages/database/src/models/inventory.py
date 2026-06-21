"""
Inventory management models: Warehouses, Stock, Batches, Movements.
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, Integer, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ..core.base import BaseModel


class MovementType(enum.Enum):
    """Types of inventory movements."""
    RECEIPT = "receipt"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    DAMAGE = "damage"
    EXPIRY = "expiry"


class Warehouse(BaseModel):
    """
    Physical or logical warehouse location.
    
    Supports multi-warehouse distributors with bin/shelf tracking.
    """
    __tablename__ = "warehouses"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    # Type
    warehouse_type: Mapped[str] = mapped_column(String(50), default="main", nullable=False)
    
    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Contact
    manager_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_negative_stock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="warehouses")
    stock_items = relationship("StockItem", back_populates="warehouse", lazy="select")
    movements = relationship("StockMovement", back_populates="warehouse", lazy="select")


class Batch(BaseModel):
    """
    Batch/lot tracking for expiry and traceability.
    
    Critical for FMCG, pharma, and perishable goods.
    """
    __tablename__ = "batches"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    manufacturer_batch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Dates
    manufacturing_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    best_before_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Receipt info
    received_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    purchase_order_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_quarantined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    product = relationship("Product")
    stock_items = relationship("StockItem", back_populates="batch", lazy="select")
    
    @property
    def is_expired(self) -> bool:
        """Check if batch is expired."""
        if self.expiry_date is None:
            return False
        return datetime.utcnow() > self.expiry_date
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get days remaining until expiry."""
        if self.expiry_date is None:
            return None
        delta = self.expiry_date - datetime.utcnow()
        return max(0, delta.days)


class StockItem(BaseModel):
    """
    Current stock level for a product in a warehouse (optionally by batch).
    
    Represents the materialized view of inventory position.
    """
    __tablename__ = "stock_items"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id"), nullable=False, index=True
    )
    
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    
    batch_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("batches.id"), nullable=True, index=True
    )
    
    # Location within warehouse
    bin_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shelf: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Quantities
    quantity_available: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_damaged: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Valuation
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    
    # Last updated
    last_counted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_movement_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    warehouse = relationship("Warehouse", back_populates="stock_items")
    product = relationship("Product", back_populates="stock_items")
    batch = relationship("Batch", back_populates="stock_items")
    movements = relationship("StockMovement", back_populates="stock_item", lazy="select")
    
    @property
    def quantity_total(self) -> int:
        """Total physical quantity (available + reserved + damaged)."""
        return self.quantity_available + self.quantity_reserved + self.quantity_damaged
    
    def can_fulfill(self, quantity: int) -> bool:
        """Check if requested quantity can be fulfilled."""
        return self.quantity_available >= quantity
    
    def reserve(self, quantity: int) -> None:
        """Reserve stock for an order."""
        if not self.can_fulfill(quantity):
            raise ValueError("Insufficient available stock")
        self.quantity_available -= quantity
        self.quantity_reserved += quantity
    
    def release_reservation(self, quantity: int) -> None:
        """Release reserved stock."""
        if self.quantity_reserved < quantity:
            raise ValueError("Insufficient reserved stock")
        self.quantity_reserved -= quantity
        self.quantity_available += quantity


class StockMovement(BaseModel):
    """
    Audit log of all inventory changes.
    
    Every stock change must create a movement record for traceability.
    """
    __tablename__ = "stock_movements"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id"), nullable=False, index=True
    )
    
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    
    stock_item_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("stock_items.id"), nullable=True, index=True
    )
    
    batch_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("batches.id"), nullable=True, index=True
    )
    
    # Movement details
    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_before: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Reference documents
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "sales_order"
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Context
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Actor
    performed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    warehouse = relationship("Warehouse", back_populates="movements")
    product = relationship("Product")
    stock_item = relationship("StockItem", back_populates="movements")
    batch = relationship("Batch")
    user = relationship("User")
