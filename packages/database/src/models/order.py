"""
Order management models: Sales Orders, Purchase Orders, Returns.
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, Integer, Boolean, DateTime, Text, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ..core.base import BaseModel


class OrderStatus(enum.Enum):
    """Sales order lifecycle statuses."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    CONFIRMED = "confirmed"
    ALLOCATED = "allocated"
    PICKING = "picking"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentStatus(enum.Enum):
    """Payment tracking."""
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    WRITTEN_OFF = "written_off"


class SalesOrder(BaseModel):
    """
    Customer sales order.
    
    Core entity for order management with full lifecycle tracking.
    """
    __tablename__ = "sales_orders"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    # Identification
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    external_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # From marketplace
    
    # Customer
    retailer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("retailers.id"), nullable=False, index=True
    )
    
    # Warehouse fulfillment
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id"), nullable=False, index=True
    )
    
    # Status tracking
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.DRAFT, nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False)
    
    # Dates
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipped_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Pricing
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    
    # Payment terms
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Shipping address (snapshot at order time)
    shipping_name: Mapped[str] = mapped_column(String(255), nullable=False)
    shipping_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)
    shipping_city: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_state: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Notes
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)  # manual, mobile_app, api, marketplace
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Audit
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    retailer = relationship("Retailer")
    warehouse = relationship("Warehouse")
    items = relationship("OrderItem", back_populates="order", lazy="select", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    
    @property
    def item_count(self) -> int:
        """Total number of line items."""
        return len(self.items)
    
    @property
    def total_quantity(self) -> int:
        """Total quantity across all items."""
        return sum(item.quantity for item in self.items)
    
    def can_cancel(self) -> bool:
        """Check if order can be cancelled."""
        return self.status not in [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.COMPLETED, OrderStatus.CANCELLED]


class OrderItem(BaseModel):
    """
    Line item within a sales order.
    """
    __tablename__ = "order_items"
    
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id"), nullable=False, index=True
    )
    
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    
    # Product snapshot (in case product changes later)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Quantity
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_allocated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_shipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_returned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=18, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Batch allocation (for FEFO - First Expired First Out)
    allocated_batch_ids: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    
    # Fulfillment
    bin_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    picking_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product")
    
    @property
    def quantity_pending(self) -> int:
        """Quantity yet to be shipped."""
        return self.quantity_ordered - self.quantity_shipped - self.quantity_returned


class PurchaseOrder(BaseModel):
    """
    Purchase order to suppliers.
    """
    __tablename__ = "purchase_orders"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    # Identification
    po_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    # Supplier (using retailer table or separate supplier table)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    
    # Dates
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    received_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Pricing
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    
    # Warehouse receiving
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id"), nullable=False, index=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)


class ReturnOrder(BaseModel):
    """
    Sales return / reverse logistics.
    """
    __tablename__ = "return_orders"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    # Reference
    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id"), nullable=False, index=True
    )
    
    # Identification
    return_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    
    # Reason
    return_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    return_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Amounts
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Dates
    return_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    processed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Audit
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    sales_order = relationship("SalesOrder")
