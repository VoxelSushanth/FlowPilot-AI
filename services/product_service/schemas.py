"""Pydantic schemas for Product Service."""

from pydantic import BaseModel, Field, constr, condecimal, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProductType(str, Enum):
    """Type of product in the catalog."""
    PHYSICAL = "physical"
    SERVICE = "service"
    BUNDLE = "bundle"


class GSTCategory(str, Enum):
    """GST tax categories for Indian compliance."""
    EXEMPT = "exempt"  # 0%
    ESSENTIAL = "essential"  # 3%
    STANDARD_12 = "standard_12"  # 12%
    STANDARD_18 = "standard_18"  # 18%
    LUXURY = "luxury"  # 28%
    SPECIAL = "special"  # Special rate


# ============== CREATE SCHEMAS ==============

class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    
    sku: constr(min_length=3, max_length=50) = Field(
        ..., 
        description="Stock Keeping Unit - unique identifier"
    )
    name: constr(min_length=1, max_length=200) = Field(
        ..., 
        description="Product display name"
    )
    description: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Detailed product description"
    )
    
    # Categorization
    category_id: Optional[int] = Field(None, description="Parent category ID")
    brand: Optional[str] = Field(None, max_length=100)
    product_type: ProductType = Field(default=ProductType.PHYSICAL)
    
    # Pricing
    base_price: condecimal(gt=0, decimal_places=2) = Field(
        ..., 
        description="Base selling price in INR"
    )
    purchase_price: Optional[condecimal(gt=0, decimal_places=2)] = Field(
        None, 
        description="Cost price for margin calculation"
    )
    mrp: Optional[condecimal(gt=0, decimal_places=2)] = Field(
        None, 
        description="Maximum Retail Price"
    )
    
    # Tax & Compliance
    hsn_code: constr(min_length=4, max_length=8) = Field(
        ..., 
        description="HSN code for GST classification"
    )
    gst_category: GSTCategory = Field(
        default=GSTCategory.STANDARD_18,
        description="GST tax slab category"
    )
    cess_rate: Optional[condecimal(ge=0, decimal_places=2)] = Field(
        None, 
        description="Additional cess if applicable"
    )
    
    # Regulatory (India-specific)
    fssai_license: Optional[str] = Field(None, description="FSSAI license for food items")
    drug_license: Optional[str] = Field(None, description="Drug license for pharmaceuticals")
    is_hazardous: bool = Field(default=False, description="Requires special handling")
    
    # Packaging
    primary_unit: str = Field(default="piece", description="Base unit (piece, kg, liter)")
    packaging_details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Packaging hierarchy {box: 12, carton: 10}"
    )
    
    # Attributes
    attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Flexible attributes (color, size, etc.)"
    )
    barcodes: Optional[List[str]] = Field(
        default_factory=list,
        description="List of barcode/UPC/EAN codes"
    )
    
    # Inventory flags
    track_inventory: bool = Field(default=True)
    allow_backorder: bool = Field(default=False)
    min_stock_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)
    
    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list)
    images: Optional[List[str]] = Field(default_factory=list)  # URLs
    
    @validator('sku')
    def validate_sku_format(cls, v):
        """Ensure SKU is uppercase and alphanumeric with hyphens."""
        cleaned = v.strip().upper().replace(' ', '-')
        if not all(c.isalnum() or c == '-' for c in cleaned):
            raise ValueError("SKU must be alphanumeric with hyphens only")
        return cleaned
    
    @validator('mrp')
    def validate_mrp_greater_than_base(cls, v, values):
        """MRP should be >= base price if provided."""
        if v and 'base_price' in values and v < values['base_price']:
            raise ValueError("MRP cannot be less than base price")
        return v


class CategoryCreate(BaseModel):
    """Schema for creating a product category."""
    
    name: constr(min_length=1, max_length=100) = Field(...)
    parent_id: Optional[int] = Field(None, description="Parent category for hierarchy")
    description: Optional[str] = Field(None, max_length=500)
    slug: Optional[constr(min_length=1, max_length=100)] = Field(None)
    image_url: Optional[str] = Field(None)
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BarcodeCreate(BaseModel):
    """Schema for adding a barcode to a product."""
    
    barcode: constr(min_length=8, max_length=50) = Field(...)
    barcode_type: str = Field(default="EAN13", description="EAN13, UPC, CODE128, etc.")
    is_primary: bool = Field(default=False)


# ============== UPDATE SCHEMAS ==============

class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)."""
    
    name: Optional[constr(min_length=1, max_length=200)] = None
    description: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[int] = None
    brand: Optional[str] = Field(None, max_length=100)
    
    # Pricing updates
    base_price: Optional[condecimal(gt=0, decimal_places=2)] = None
    purchase_price: Optional[condecimal(gt=0, decimal_places=2)] = None
    mrp: Optional[condecimal(gt=0, decimal_places=2)] = None
    
    # Tax updates
    hsn_code: Optional[constr(min_length=4, max_length=8)] = None
    gst_category: Optional[GSTCategory] = None
    cess_rate: Optional[condecimal(ge=0, decimal_places=2)] = None
    
    # Regulatory updates
    fssai_license: Optional[str] = None
    drug_license: Optional[str] = None
    is_hazardous: Optional[bool] = None
    
    # Packaging updates
    primary_unit: Optional[str] = None
    packaging_details: Optional[Dict[str, Any]] = None
    
    # Attribute updates
    attributes: Optional[Dict[str, Any]] = None
    barcodes: Optional[List[str]] = None
    
    # Inventory flags
    track_inventory: Optional[bool] = None
    allow_backorder: Optional[bool] = None
    min_stock_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)
    
    tags: Optional[List[str]] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    
    name: Optional[constr(min_length=1, max_length=100)] = None
    parent_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=500)
    slug: Optional[constr(min_length=1, max_length=100)] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


# ============== RESPONSE SCHEMAS ==============

class ProductResponse(BaseModel):
    """Complete product response with computed fields."""
    
    id: int
    organization_id: int
    sku: str
    name: str
    description: Optional[str]
    
    # Hierarchy
    category: Optional["CategoryResponse"] = None
    brand: Optional[str]
    product_type: ProductType
    
    # Pricing
    base_price: float
    purchase_price: Optional[float]
    mrp: Optional[float]
    margin_percent: Optional[float] = Field(None, description="Calculated margin %")
    
    # Tax
    hsn_code: str
    gst_category: GSTCategory
    gst_rate: float = Field(..., description="Computed GST rate %")
    cess_rate: Optional[float]
    total_tax_rate: float = Field(..., description="GST + Cess")
    
    # Regulatory
    fssai_license: Optional[str]
    drug_license: Optional[str]
    is_hazardous: bool
    
    # Packaging
    primary_unit: str
    packaging_details: Optional[Dict[str, Any]]
    
    # Attributes
    attributes: Dict[str, Any]
    barcodes: List[str]
    
    # Inventory status
    track_inventory: bool
    allow_backorder: bool
    min_stock_level: Optional[int]
    max_stock_level: Optional[int]
    current_stock: Optional[int] = Field(None, description="Total stock across warehouses")
    
    # Metadata
    tags: List[str]
    images: List[str]
    is_active: bool
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: Optional[int]
    
    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    """Category with hierarchy information."""
    
    id: int
    organization_id: int
    name: str
    parent_id: Optional[int]
    parent: Optional["CategoryResponse"] = None
    children: List["CategoryResponse"] = Field(default_factory=list)
    description: Optional[str]
    slug: str
    image_url: Optional[str]
    sort_order: int
    is_active: bool
    product_count: int = Field(default=0, description="Number of products in category")
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Paginated list of products."""
    
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    # Filters applied
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None


class ProductStats(BaseModel):
    """Product statistics for dashboard."""
    
    total_products: int
    active_products: int
    inactive_products: int
    low_stock_count: int  # Products below min_stock_level
    out_of_stock_count: int
    categories_count: int
    avg_margin_percent: Optional[float]
    top_categories: List[Dict[str, Any]]  # Top 5 by product count


# ============== QUERY SCHEMAS ==============

class ProductFilter(BaseModel):
    """Filter parameters for product search."""
    
    search: Optional[str] = Field(None, description="Search in name, SKU, barcode")
    category_id: Optional[int] = None
    brand: Optional[str] = None
    product_type: Optional[ProductType] = None
    gst_category: Optional[GSTCategory] = None
    hsn_code: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    has_low_stock: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    
    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    # Sorting
    sort_by: Optional[str] = Field(default="created_at")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")


class BulkUploadResult(BaseModel):
    """Result of bulk product upload."""
    
    total_processed: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]]  # Row number and error message
    created_ids: List[int]
    updated_ids: List[int]
