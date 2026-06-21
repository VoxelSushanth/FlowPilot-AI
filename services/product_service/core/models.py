"""Product Service - Core Business Logic and Database Models."""

from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any

from .__init__ import Base


# ============== ENUM-LIKE CONSTANTS ==============

PRODUCT_TYPES = ["physical", "service", "bundle"]
GST_CATEGORIES = {
    "exempt": 0.0,
    "essential": 3.0,
    "standard_12": 12.0,
    "standard_18": 18.0,
    "luxury": 28.0,
    "special": None  # Custom rate
}


# ============== MODELS ==============

class Category(Base):
    """Product category with hierarchical support."""
    
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Hierarchy
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # Basic info
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    image_url = Column(String(500))
    
    # Ordering & status
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(datetime, default=datetime.utcnow, nullable=False)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_category_org_parent', 'organization_id', 'parent_id'),
        Index('idx_category_active', 'is_active', 'organization_id'),
    )
    
    def get_gst_rate(self) -> float:
        """Get GST rate for this category if set in metadata."""
        return self.metadata.get('gst_rate') if self.metadata else None
    
    def get_full_path(self) -> str:
        """Get full category path (e.g., 'Electronics > Mobile > Accessories')."""
        path = [self.name]
        current = self.parent
        while current:
            path.append(current.name)
            current = current.parent
        return ' > '.join(reversed(path))


class Product(Base):
    """Master product catalog entry."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Identification
    sku = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Categorization
    category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    brand = Column(String(100), index=True)
    product_type = Column(String(20), default="physical")  # physical, service, bundle
    
    # Pricing
    base_price = Column(Numeric(12, 2), nullable=False)
    purchase_price = Column(Numeric(12, 2))
    mrp = Column(Numeric(12, 2))
    
    # Tax & Compliance (India-specific)
    hsn_code = Column(String(8), nullable=False, index=True)
    gst_category = Column(String(20), default="standard_18")
    cess_rate = Column(Numeric(5, 2))
    
    # Regulatory licenses
    fssai_license = Column(String(50))  # Food Safety license
    drug_license = Column(String(50))   # Drug license for pharma
    is_hazardous = Column(Boolean, default=False)
    
    # Packaging
    primary_unit = Column(String(20), default="piece")
    packaging_details = Column(JSONB)  # {box: 12, carton: 10}
    
    # Flexible attributes
    attributes = Column(JSONB, default=dict)  # {color: red, size: L}
    barcodes = Column(JSONB, default=list)  # [ean13, upc, etc.]
    
    # Inventory control flags
    track_inventory = Column(Boolean, default=True)
    allow_backorder = Column(Boolean, default=False)
    min_stock_level = Column(Integer)
    max_stock_level = Column(Integer)
    
    # Metadata
    tags = Column(JSONB, default=list)
    images = Column(JSONB, default=list)  # URLs
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(datetime, default=datetime.utcnow, nullable=False)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Soft delete
    deleted_at = Column(datetime, nullable=True, index=True)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    inventory_items = relationship("InventoryItem", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    price_history = relationship("ProductPriceHistory", back_populates="product", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_product_org_sku', 'organization_id', 'sku', unique=True),
        Index('idx_product_org_active', 'organization_id', 'is_active'),
        Index('idx_product_org_category', 'organization_id', 'category_id'),
        Index('idx_product_org_brand', 'organization_id', 'brand'),
        Index('idx_product_org_hsn', 'organization_id', 'hsn_code'),
        Index('idx_product_barcode', 'barcodes', postgresql_using='gin'),
    )
    
    @property
    def margin_percent(self) -> Optional[float]:
        """Calculate profit margin percentage."""
        if self.purchase_price and self.base_price:
            margin = float(self.base_price - self.purchase_price)
            return round((margin / float(self.base_price)) * 100, 2)
        return None
    
    @property
    def gst_rate(self) -> float:
        """Get GST rate as percentage."""
        return GST_CATEGORIES.get(self.gst_category, 18.0) or 18.0
    
    @property
    def total_tax_rate(self) -> float:
        """Get total tax rate (GST + Cess)."""
        cess = float(self.cess_rate) if self.cess_rate else 0.0
        return self.gst_rate + cess
    
    @property
    def price_with_tax(self) -> Decimal:
        """Get price including all taxes."""
        tax_amount = float(self.base_price) * (self.total_tax_rate / 100)
        return self.base_price + Decimal(str(tax_amount))
    
    def has_compliance_issue(self) -> bool:
        """Check if product has missing required compliance info."""
        if self.fssai_license is None and self.hsn_code.startswith(('1', '2')):
            # Food products need FSSAI
            return True
        if self.drug_license is None and 'pharma' in self.tags:
            return True
        return False


class ProductBarcode(Base):
    """Additional barcodes for a product (EAN, UPC, etc.)."""
    
    __tablename__ = "product_barcodes"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    barcode = Column(String(50), nullable=False, index=True)
    barcode_type = Column(String(20), default="EAN13")  # EAN13, UPC, CODE128, etc.
    is_primary = Column(Boolean, default=False)
    created_at = Column(datetime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_barcode_product', 'product_id', 'is_primary'),
    )


class ProductPriceHistory(Base):
    """Track price changes over time."""
    
    __tablename__ = "product_price_history"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    old_base_price = Column(Numeric(12, 2))
    new_base_price = Column(Numeric(12, 2), nullable=False)
    old_mrp = Column(Numeric(12, 2))
    new_mrp = Column(Numeric(12, 2))
    
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_reason = Column(String(200))
    changed_at = Column(datetime, default=datetime.utcnow, nullable=False)
    
    product = relationship("Product", back_populates="price_history")


class InventoryItem(Base):
    """Stock levels per warehouse/location."""
    
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    
    # Stock quantities
    quantity_available = Column(Integer, default=0, nullable=False)
    quantity_reserved = Column(Integer, default=0, nullable=False)
    quantity_in_transit = Column(Integer, default=0)
    
    # Batch tracking
    batch_number = Column(String(50), index=True)
    manufacturing_date = Column(datetime)
    expiry_date = Column(datetime, index=True)
    
    # Location within warehouse
    bin_location = Column(String(50))
    
    # Valuation
    cost_price = Column(Numeric(12, 2))  # For FIFO/LIFO
    last_purchase_price = Column(Numeric(12, 2))
    
    # Timestamps
    created_at = Column(datetime, default=datetime.utcnow, nullable=False)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    product = relationship("Product", back_populates="inventory_items")
    
    __table_args__ = (
        Index('idx_inventory_org_product', 'organization_id', 'product_id'),
        Index('idx_inventory_org_warehouse', 'organization_id', 'warehouse_id'),
    )
    
    @property
    def total_quantity(self) -> int:
        """Total physical stock."""
        return self.quantity_available + self.quantity_reserved
    
    @property
    def sellable_quantity(self) -> int:
        """Quantity available for sale."""
        return self.quantity_available
    
    @property
    def is_expired(self) -> bool:
        """Check if batch is expired."""
        if self.expiry_date:
            return self.expiry_date < datetime.utcnow()
        return False
    
    @property
    def days_to_expiry(self) -> Optional[int]:
        """Days remaining until expiry."""
        if self.expiry_date:
            delta = self.expiry_date - datetime.utcnow()
            return delta.days
        return None


class Warehouse(Base):
    """Warehouse/storage location."""
    
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True)
    
    # Address
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    country = Column(String(50), default="India")
    
    # Contact
    contact_name = Column(String(100))
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # Configuration
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    warehouse_type = Column(String(20))  # owned, rented, third_party
    
    # Timestamps
    created_at = Column(datetime, default=datetime.utcnow)
    updated_at = Column(datetime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_items = relationship("InventoryItem", back_populates="warehouse")
    
    __table_args__ = (
        Index('idx_warehouse_org', 'organization_id', 'is_active'),
    )


class StockMovement(Base):
    """Audit trail for all stock changes."""
    
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    
    movement_type = Column(String(20), nullable=False)  # IN, OUT, ADJUSTMENT, TRANSFER
    quantity = Column(Integer, nullable=False)  # Positive for IN, negative for OUT
    
    reference_type = Column(String(50))  # ORDER, PURCHASE, ADJUSTMENT, etc.
    reference_id = Column(Integer)
    
    batch_number = Column(String(50))
    reason = Column(String(200))
    
    created_at = Column(datetime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    __table_args__ = (
        Index('idx_stock_movement_org_product', 'organization_id', 'product_id'),
        Index('idx_stock_movement_reference', 'reference_type', 'reference_id'),
    )
