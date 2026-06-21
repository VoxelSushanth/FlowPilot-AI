"""Product Service - Repository Layer for Database Operations."""

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal

from .models import (
    Product, Category, ProductBarcode, ProductPriceHistory,
    InventoryItem, Warehouse, StockMovement
)
from .schemas import (
    ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate,
    ProductFilter, ProductType, GSTCategory
)


class ProductRepository:
    """Repository for Product CRUD operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create(self, product_data: ProductCreate, user_id: int, organization_id: int) -> Product:
        """Create a new product."""
        
        # Check for duplicate SKU
        existing = await self.get_by_sku(product_data.sku, organization_id)
        if existing:
            raise ValueError(f"Product with SKU {product_data.sku} already exists")
        
        # Create product instance
        product = Product(
            organization_id=organization_id,
            sku=product_data.sku,
            name=product_data.name,
            description=product_data.description,
            category_id=product_data.category_id,
            brand=product_data.brand,
            product_type=product_data.product_type.value,
            base_price=product_data.base_price,
            purchase_price=product_data.purchase_price,
            mrp=product_data.mrp,
            hsn_code=product_data.hsn_code,
            gst_category=product_data.gst_category.value,
            cess_rate=product_data.cess_rate,
            fssai_license=product_data.fssai_license,
            drug_license=product_data.drug_license,
            is_hazardous=product_data.is_hazardous,
            primary_unit=product_data.primary_unit,
            packaging_details=product_data.packaging_details,
            attributes=product_data.attributes or {},
            barcodes=product_data.barcodes or [],
            track_inventory=product_data.track_inventory,
            allow_backorder=product_data.allow_backorder,
            min_stock_level=product_data.min_stock_level,
            max_stock_level=product_data.max_stock_level,
            tags=product_data.tags or [],
            images=product_data.images or [],
            created_by=user_id,
        )
        
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        
        return product
    
    async def get_by_id(self, product_id: int, organization_id: int) -> Optional[Product]:
        """Get product by ID with category loaded."""
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.organization_id == organization_id)
            .options(selectinload(Product.category))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_sku(self, sku: str, organization_id: int) -> Optional[Product]:
        """Get product by SKU."""
        stmt = select(Product).where(
            Product.sku == sku,
            Product.organization_id == organization_id,
            Product.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_barcode(self, barcode: str, organization_id: int) -> Optional[Product]:
        """Find product by barcode (searches in barcodes JSONB array)."""
        stmt = select(Product).where(
            Product.organization_id == organization_id,
            Product.barcodes.contains([barcode]),
            Product.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_products(
        self,
        filters: ProductFilter,
        organization_id: int
    ) -> Tuple[List[Product], int]:
        """List products with filtering and pagination."""
        
        # Base query
        conditions = [
            Product.organization_id == organization_id,
            Product.deleted_at.is_(None)
        ]
        
        # Apply filters
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                    Product.brand.ilike(search_term)
                )
            )
        
        if filters.category_id:
            conditions.append(Product.category_id == filters.category_id)
        
        if filters.brand:
            conditions.append(Product.brand == filters.brand)
        
        if filters.product_type:
            conditions.append(Product.product_type == filters.product_type.value)
        
        if filters.gst_category:
            conditions.append(Product.gst_category == filters.gst_category.value)
        
        if filters.hsn_code:
            conditions.append(Product.hsn_code.like(f"{filters.hsn_code}%"))
        
        if filters.min_price is not None:
            conditions.append(Product.base_price >= filters.min_price)
        
        if filters.max_price is not None:
            conditions.append(Product.base_price <= filters.max_price)
        
        if filters.is_active is not None:
            conditions.append(Product.is_active == filters.is_active)
        
        if filters.has_low_stock:
            # This requires joining with inventory, handled separately
            pass
        
        # Build query
        stmt = select(Product).where(*conditions)
        
        # Add ordering
        order_column = getattr(Product, filters.sort_by, Product.created_at)
        if filters.sort_order == "desc":
            stmt = stmt.order_by(order_column.desc())
        else:
            stmt = stmt.order_by(order_column.asc())
        
        # Pagination
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.offset(offset).limit(filters.page_size)
        
        # Execute
        result = await self.db.execute(stmt)
        products = result.scalars().all()
        
        # Get total count
        count_stmt = select(func.count()).select_from(Product).where(*conditions)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        return products, total
    
    async def update(
        self,
        product_id: int,
        product_data: ProductUpdate,
        user_id: int,
        organization_id: int
    ) -> Optional[Product]:
        """Update a product."""
        
        product = await self.get_by_id(product_id, organization_id)
        if not product:
            return None
        
        # Update fields
        update_data = product_data.dict(exclude_unset=True)
        
        # Track price changes
        if 'base_price' in update_data or 'mrp' in update_data:
            price_history = ProductPriceHistory(
                product_id=product_id,
                old_base_price=product.base_price,
                new_base_price=update_data.get('base_price', product.base_price),
                old_mrp=product.mrp,
                new_mrp=update_data.get('mrp'),
                changed_by=user_id,
                change_reason=update_data.get('price_change_reason', 'Manual update')
            )
            self.db.add(price_history)
        
        # Apply updates
        for field, value in update_data.items():
            if field != 'price_change_reason' and hasattr(product, field):
                setattr(product, field, value)
        
        product.updated_by = user_id
        
        await self.db.commit()
        await self.db.refresh(product)
        
        return product
    
    async def delete(self, product_id: int, user_id: int, organization_id: int) -> bool:
        """Soft delete a product."""
        
        product = await self.get_by_id(product_id, organization_id)
        if not product:
            return False
        
        product.deleted_at = datetime.utcnow()
        product.updated_by = user_id
        
        await self.db.commit()
        return True
    
    async def bulk_upsert(
        self,
        products_data: List[Dict[str, Any]],
        user_id: int,
        organization_id: int
    ) -> Dict[str, Any]:
        """Bulk create or update products."""
        
        results = {
            'total_processed': len(products_data),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'created_ids': [],
            'updated_ids': []
        }
        
        for idx, data in enumerate(products_data):
            try:
                # Validate required fields
                if not all(k in data for k in ['sku', 'name', 'base_price', 'hsn_code']):
                    raise ValueError("Missing required fields: sku, name, base_price, hsn_code")
                
                # Try to find existing product
                existing = await self.get_by_sku(data['sku'], organization_id)
                
                if existing:
                    # Update existing
                    update_data = ProductUpdate(**data)
                    updated = await self.update(existing.id, update_data, user_id, organization_id)
                    if updated:
                        results['updated_ids'].append(updated.id)
                        results['successful'] += 1
                else:
                    # Create new
                    create_data = ProductCreate(**data)
                    new_product = await self.create(create_data, user_id, organization_id)
                    results['created_ids'].append(new_product.id)
                    results['successful'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'row': idx + 1,
                    'sku': data.get('sku', 'N/A'),
                    'error': str(e)
                })
        
        return results
    
    async def get_stats(self, organization_id: int) -> Dict[str, Any]:
        """Get product statistics."""
        
        # Total products
        total_stmt = select(func.count()).where(
            Product.organization_id == organization_id,
            Product.deleted_at.is_(None)
        )
        total = await self.db.scalar(total_stmt)
        
        # Active products
        active_stmt = select(func.count()).where(
            Product.organization_id == organization_id,
            Product.is_active == True,
            Product.deleted_at.is_(None)
        )
        active = await self.db.scalar(active_stmt)
        
        # Categories count
        cat_stmt = select(func.count(Category.id)).where(
            Category.organization_id == organization_id,
            Category.is_active == True
        )
        categories_count = await self.db.scalar(cat_stmt)
        
        # Average margin
        margin_stmt = select(func.avg(
            ((Product.base_price - Product.purchase_price) / Product.base_price) * 100
        )).where(
            Product.organization_id == organization_id,
            Product.purchase_price.isnot(None),
            Product.deleted_at.is_(None)
        )
        avg_margin = await self.db.scalar(margin_stmt)
        
        return {
            'total_products': total or 0,
            'active_products': active or 0,
            'inactive_products': (total or 0) - (active or 0),
            'categories_count': categories_count or 0,
            'avg_margin_percent': float(avg_margin) if avg_margin else None
        }


class CategoryRepository:
    """Repository for Category operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create(self, category_data: CategoryCreate, user_id: int, organization_id: int) -> Category:
        """Create a new category."""
        
        # Generate slug if not provided
        slug = category_data.slug or category_data.name.lower().replace(' ', '-').replace('_', '-')
        
        category = Category(
            organization_id=organization_id,
            name=category_data.name,
            parent_id=category_data.parent_id,
            description=category_data.description,
            slug=slug,
            image_url=category_data.image_url,
            sort_order=category_data.sort_order,
            is_active=category_data.is_active,
            metadata=category_data.metadata or {},
            created_by=user_id,
        )
        
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        
        return category
    
    async def get_tree(self, organization_id: int, active_only: bool = True) -> List[Category]:
        """Get category tree with children."""
        
        conditions = [Category.organization_id == organization_id]
        if active_only:
            conditions.append(Category.is_active == True)
        
        stmt = (
            select(Category)
            .where(*conditions)
            .options(selectinload(Category.children))
            .order_by(Category.sort_order, Category.name)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update(
        self,
        category_id: int,
        category_data: CategoryUpdate,
        user_id: int,
        organization_id: int
    ) -> Optional[Category]:
        """Update a category."""
        
        stmt = select(Category).where(
            Category.id == category_id,
            Category.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        category = result.scalar_one_or_none()
        
        if not category:
            return None
        
        update_data = category_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        
        category.updated_by = user_id
        
        await self.db.commit()
        await self.db.refresh(category)
        
        return category


class InventoryRepository:
    """Repository for Inventory operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_stock_levels(
        self,
        product_id: int,
        organization_id: int
    ) -> List[InventoryItem]:
        """Get stock levels for a product across all warehouses."""
        
        stmt = select(InventoryItem).where(
            InventoryItem.product_id == product_id,
            InventoryItem.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_total_stock(self, product_id: int, organization_id: int) -> int:
        """Get total stock quantity for a product."""
        
        items = await self.get_stock_levels(product_id, organization_id)
        return sum(item.quantity_available for item in items)
    
    async def reserve_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        organization_id: int
    ) -> bool:
        """Reserve stock for an order."""
        
        stmt = select(InventoryItem).where(
            InventoryItem.product_id == product_id,
            InventoryItem.warehouse_id == warehouse_id,
            InventoryItem.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        inventory = result.scalar_one_or_none()
        
        if not inventory or inventory.quantity_available < quantity:
            return False
        
        inventory.quantity_available -= quantity
        inventory.quantity_reserved += quantity
        
        await self.db.commit()
        return True
    
    async def release_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        organization_id: int
    ) -> bool:
        """Release reserved stock."""
        
        stmt = select(InventoryItem).where(
            InventoryItem.product_id == product_id,
            InventoryItem.warehouse_id == warehouse_id,
            InventoryItem.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        inventory = result.scalar_one_or_none()
        
        if not inventory or inventory.quantity_reserved < quantity:
            return False
        
        inventory.quantity_reserved -= quantity
        inventory.quantity_available += quantity
        
        await self.db.commit()
        return True
    
    async def consume_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        organization_id: int,
        reference_type: str,
        reference_id: int,
        user_id: int
    ) -> bool:
        """Consume reserved stock (after order fulfillment)."""
        
        stmt = select(InventoryItem).where(
            InventoryItem.product_id == product_id,
            InventoryItem.warehouse_id == warehouse_id,
            InventoryItem.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        inventory = result.scalar_one_or_none()
        
        if not inventory or inventory.quantity_reserved < quantity:
            return False
        
        # Reduce reserved stock
        inventory.quantity_reserved -= quantity
        
        # Create stock movement record
        movement = StockMovement(
            organization_id=organization_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type="OUT",
            quantity=-quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            batch_number=inventory.batch_number,
            created_by=user_id
        )
        self.db.add(movement)
        
        await self.db.commit()
        return True
    
    async def add_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        organization_id: int,
        batch_number: Optional[str] = None,
        expiry_date: Optional[datetime] = None,
        cost_price: Optional[Decimal] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> InventoryItem:
        """Add stock to inventory."""
        
        # Find or create inventory item
        stmt = select(InventoryItem).where(
            InventoryItem.product_id == product_id,
            InventoryItem.warehouse_id == warehouse_id,
            InventoryItem.organization_id == organization_id,
            InventoryItem.batch_number == batch_number
        )
        result = await self.db.execute(stmt)
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            inventory = InventoryItem(
                organization_id=organization_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity_available=0,
                quantity_reserved=0,
                batch_number=batch_number,
                expiry_date=expiry_date,
                cost_price=cost_price,
            )
            self.db.add(inventory)
        
        # Update quantities
        inventory.quantity_available += quantity
        if cost_price:
            inventory.last_purchase_price = cost_price
        
        # Create stock movement
        if reference_type and user_id:
            movement = StockMovement(
                organization_id=organization_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                movement_type="IN",
                quantity=quantity,
                reference_type=reference_type,
                reference_id=reference_id,
                batch_number=batch_number,
                created_by=user_id
            )
            self.db.add(movement)
        
        await self.db.commit()
        await self.db.refresh(inventory)
        
        return inventory
    
    async def get_low_stock_products(
        self,
        organization_id: int,
        threshold_days: int = 7
    ) -> List[Product]:
        """Get products below minimum stock level."""
        
        # This would need a more complex query joining products and inventory
        # Simplified version here
        stmt = (
            select(Product)
            .join(InventoryItem, Product.id == InventoryItem.product_id)
            .where(
                Product.organization_id == organization_id,
                Product.min_stock_level.isnot(None),
                InventoryItem.quantity_available < Product.min_stock_level,
                Product.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
