"""Product Service - REST API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ...core.database import get_db
from ...core.security import get_current_user
from .schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse, ProductFilter,
    ProductStats, BulkUploadResult
)
from .core.repository import ProductRepository, CategoryRepository, InventoryRepository
from .core.models import Product


router = APIRouter(prefix="/products", tags=["Products"])


# ============== PRODUCT ENDPOINTS ==============

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new product in the catalog."""
    
    repo = ProductRepository(db)
    
    try:
        product = await repo.create(
            product_data=product_data,
            user_id=current_user["id"],
            organization_id=current_user["organization_id"]
        )
        
        # Load category relationship
        await db.refresh(product)
        
        return product
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ProductListResponse)
async def list_products(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    product_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_active: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List products with filtering and pagination."""
    
    filters = ProductFilter(
        search=search,
        category_id=category_id,
        brand=brand,
        product_type=product_type,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    repo = ProductRepository(db)
    products, total = await repo.list_products(
        filters=filters,
        organization_id=current_user["organization_id"]
    )
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        filters=filters.dict(exclude={'page', 'page_size'})
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific product by ID."""
    
    repo = ProductRepository(db)
    product = await repo.get_by_id(
        product_id=product_id,
        organization_id=current_user["organization_id"]
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.get("/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(
    sku: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a product by SKU."""
    
    repo = ProductRepository(db)
    product = await repo.get_by_sku(
        sku=sku.upper(),
        organization_id=current_user["organization_id"]
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.get("/barcode/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Find a product by barcode."""
    
    repo = ProductRepository(db)
    product = await repo.get_by_barcode(
        barcode=barcode,
        organization_id=current_user["organization_id"]
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found for this barcode")
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing product."""
    
    repo = ProductRepository(db)
    product = await repo.update(
        product_id=product_id,
        product_data=product_data,
        user_id=current_user["id"],
        organization_id=current_user["organization_id"]
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a product."""
    
    repo = ProductRepository(db)
    success = await repo.delete(
        product_id=product_id,
        user_id=current_user["id"],
        organization_id=current_user["organization_id"]
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")


@router.post("/bulk", response_model=BulkUploadResult)
async def bulk_upload_products(
    products: List[dict],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Bulk create or update products from CSV/Excel import."""
    
    repo = ProductRepository(db)
    results = await repo.bulk_upsert(
        products_data=products,
        user_id=current_user["id"],
        organization_id=current_user["organization_id"]
    )
    
    return results


@router.get("/stats", response_model=ProductStats)
async def get_product_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get product catalog statistics."""
    
    repo = ProductRepository(db)
    stats = await repo.get_stats(current_user["organization_id"])
    
    # Get low stock count
    inv_repo = InventoryRepository(db)
    low_stock = await inv_repo.get_low_stock_products(current_user["organization_id"])
    
    return ProductStats(
        **stats,
        low_stock_count=len(low_stock),
        out_of_stock_count=0,  # Would need additional query
        top_categories=[]  # Would need aggregation query
    )


# ============== CATEGORY ENDPOINTS ==============

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new product category."""
    
    repo = CategoryRepository(db)
    category = await repo.create(
        category_data=category_data,
        user_id=current_user["id"],
        organization_id=current_user["organization_id"]
    )
    
    return category


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get category tree structure."""
    
    repo = CategoryRepository(db)
    categories = await repo.get_tree(
        organization_id=current_user["organization_id"],
        active_only=active_only
    )
    
    # Return root categories (those without parents)
    root_categories = [cat for cat in categories if cat.parent_id is None]
    return root_categories


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a category."""
    
    repo = CategoryRepository(db)
    category = await repo.update(
        category_id=category_id,
        category_data=category_data,
        user_id=current_user["id"],
        organization_id=current_user["organization_id"]
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


# ============== INVENTORY ENDPOINTS ==============

@router.get("/{product_id}/inventory")
async def get_product_inventory(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get stock levels for a product across all warehouses."""
    
    # Verify product exists
    product_repo = ProductRepository(db)
    product = await product_repo.get_by_id(product_id, current_user["organization_id"])
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    inv_repo = InventoryRepository(db)
    inventory_items = await inv_repo.get_stock_levels(
        product_id=product_id,
        organization_id=current_user["organization_id"]
    )
    
    return {
        "product_id": product_id,
        "sku": product.sku,
        "name": product.name,
        "total_available": sum(item.quantity_available for item in inventory_items),
        "total_reserved": sum(item.quantity_reserved for item in inventory_items),
        "warehouses": [
            {
                "warehouse_id": item.warehouse_id,
                "available": item.quantity_available,
                "reserved": item.quantity_reserved,
                "batch": item.batch_number,
                "expiry": item.expiry_date.isoformat() if item.expiry_date else None,
                "days_to_expiry": item.days_to_expiry
            }
            for item in inventory_items
        ]
    }
