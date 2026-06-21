"""
Product catalog models: Products, Categories, Pricing.
"""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, Integer, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.base import BaseModel


class ProductCategory(BaseModel):
    """
    Hierarchical product categories.
    
    Supports unlimited nesting for complex catalog structures.
    """
    __tablename__ = "product_categories"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Hierarchy
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("product_categories.id"), nullable=True, index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=True)  # Materialized path
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    parent = relationship("ProductCategory", remote_side="ProductCategory.id")
    children = relationship("ProductCategory", backref="parent", lazy="select")
    products = relationship("Product", back_populates="category", lazy="select")


class Product(BaseModel):
    """
    Product definition with variants and packaging.
    
    Supports:
    - Multiple units of measure (UOM)
    - Hierarchical packaging (piece -> pack -> case -> pallet)
    - GST/tax configuration
    - Barcode/HSN codes for Indian compliance
    """
    __tablename__ = "products"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("product_categories.id"), nullable=True, index=True
    )
    
    # Identification
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    hsn_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Indian tax code
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Pricing
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    mrp: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)  # Max Retail Price
    
    # Tax
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=18.00, nullable=False)
    cess_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Units
    primary_uom: Mapped[str] = mapped_column(String(50), default="PCS", nullable=False)
    secondary_uom: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    conversion_factor: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=1.0, nullable=False)
    
    # Packaging hierarchy (JSON for flexibility)
    # Example: {"pack": 12, "case": 10, "pallet": 50}
    packaging_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Inventory tracking
    track_inventory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_backorder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_stock_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_stock_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reorder_point: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Images (URLs stored in JSON array)
    images: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Attributes (flexible key-value pairs)
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    pricing_tiers = relationship("PricingTier", back_populates="product", lazy="select")
    stock_items = relationship("StockItem", back_populates="product", lazy="select")
    
    def get_effective_price(self, quantity: int = 1) -> Decimal:
        """Calculate effective price considering packaging."""
        return self.base_price * quantity
    
    def has_low_stock(self, current_stock: int) -> bool:
        """Check if stock is below reorder point."""
        if self.reorder_point is None:
            return False
        return current_stock <= self.reorder_point


class PricingTier(BaseModel):
    """
    Volume-based or customer-type-based pricing.
    
    Allows different prices for different quantities or customer segments.
    """
    __tablename__ = "pricing_tiers"
    
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    
    # Tier identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Pricing rules
    min_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Customer type restriction (optional)
    customer_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Validity
    valid_from: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ISO date
    valid_until: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="pricing_tiers")
