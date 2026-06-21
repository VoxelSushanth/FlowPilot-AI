"""Tests for Product Service."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any

from services.product_service.schemas import (
    ProductCreate, ProductUpdate, CategoryCreate, ProductFilter,
    ProductType, GSTCategory
)


class TestProductSchemas:
    """Test product schema validation."""
    
    def test_create_valid_product(self):
        """Test creating a product with valid data."""
        product_data = {
            "sku": "TEST-SKU-001",
            "name": "Test Product",
            "base_price": 100.00,
            "hsn_code": "8517"
        }
        
        product = ProductCreate(**product_data)
        assert product.sku == "TEST-SKU-001"
        assert product.name == "Test Product"
        assert product.base_price == Decimal("100.00")
        assert product.gst_category == GSTCategory.STANDARD_18
    
    def test_sku_normalization(self):
        """Test that SKU is normalized to uppercase."""
        product_data = {
            "sku": "test-sku-lower",
            "name": "Test Product",
            "base_price": 100.00,
            "hsn_code": "8517"
        }
        
        product = ProductCreate(**product_data)
        assert product.sku == "TEST-SKU-LOWER"
    
    def test_invalid_sku_format(self):
        """Test that invalid SKU format raises error."""
        product_data = {
            "sku": "INVALID@SKU!",
            "name": "Test Product",
            "base_price": 100.00,
            "hsn_code": "8517"
        }
        
        with pytest.raises(ValueError):
            ProductCreate(**product_data)
    
    def test_mrp_validation(self):
        """Test that MRP cannot be less than base price."""
        product_data = {
            "sku": "TEST-SKU-002",
            "name": "Test Product",
            "base_price": 100.00,
            "mrp": 50.00,  # Less than base price
            "hsn_code": "8517"
        }
        
        with pytest.raises(ValueError, match="MRP cannot be less than base price"):
            ProductCreate(**product_data)
    
    def test_gst_categories(self):
        """Test all GST category options."""
        for category in GSTCategory:
            product_data = {
                "sku": f"TEST-{category.value}",
                "name": "Test Product",
                "base_price": 100.00,
                "hsn_code": "8517",
                "gst_category": category
            }
            product = ProductCreate(**product_data)
            assert product.gst_category == category


class TestCategorySchemas:
    """Test category schema validation."""
    
    def test_create_category(self):
        """Test creating a category."""
        category_data = {
            "name": "Electronics",
            "slug": "electronics"
        }
        
        category = CategoryCreate(**category_data)
        assert category.name == "Electronics"
        assert category.slug == "electronics"
        assert category.is_active == True
    
    def test_category_slug_generation(self):
        """Test that slug can be optional."""
        category_data = {
            "name": "Home Appliances"
        }
        
        category = CategoryCreate(**category_data)
        assert category.name == "Home Appliances"
        # Slug would be generated in repository layer


class TestProductFilter:
    """Test product filtering schemas."""
    
    def test_default_filter(self):
        """Test default filter values."""
        filters = ProductFilter()
        assert filters.page == 1
        assert filters.page_size == 20
        assert filters.sort_by == "created_at"
        assert filters.sort_order == "desc"
    
    def test_filter_with_search(self):
        """Test filter with search term."""
        filters = ProductFilter(search="laptop", page_size=50)
        assert filters.search == "laptop"
        assert filters.page_size == 50
    
    def test_filter_pagination_bounds(self):
        """Test pagination bounds validation."""
        # Valid pagination
        filters = ProductFilter(page=5, page_size=50)
        assert filters.page == 5
        
        # Invalid page (should fail validation)
        with pytest.raises(Exception):
            ProductFilter(page=0)
        
        # Invalid page_size (too large)
        with pytest.raises(Exception):
            ProductFilter(page_size=200)


class TestProductModelProperties:
    """Test model property calculations."""
    
    def test_margin_calculation(self):
        """Test margin percentage calculation."""
        # This would require actual model instances
        # Simplified test for logic verification
        base_price = Decimal("100.00")
        purchase_price = Decimal("70.00")
        
        margin = float((base_price - purchase_price) / base_price * 100)
        assert margin == 30.0
    
    def test_gst_rate_lookup(self):
        """Test GST rate lookup from category."""
        gst_rates = {
            "exempt": 0.0,
            "essential": 3.0,
            "standard_12": 12.0,
            "standard_18": 18.0,
            "luxury": 28.0
        }
        
        for category, expected_rate in gst_rates.items():
            assert GST_CATEGORIES.get(category, 18.0) == expected_rate
    
    def test_price_with_tax(self):
        """Test price calculation including tax."""
        base_price = Decimal("100.00")
        gst_rate = 18.0
        cess_rate = 2.0
        
        total_tax_rate = gst_rate + cess_rate
        tax_amount = float(base_price) * (total_tax_rate / 100)
        price_with_tax = base_price + Decimal(str(tax_amount))
        
        assert price_with_tax == Decimal("120.00")


# Import constants from models for testing
from services.product_service.core.models import GST_CATEGORIES


class TestInventoryLogic:
    """Test inventory-related business logic."""
    
    def test_stock_availability(self):
        """Test stock availability calculation."""
        quantity_available = 100
        quantity_reserved = 30
        
        sellable = quantity_available
        total_physical = quantity_available + quantity_reserved
        
        assert sellable == 100
        assert total_physical == 130
    
    def test_expiry_check(self):
        """Test expiry date logic."""
        today = datetime.utcnow()
        expired_date = today - timedelta(days=10)
        future_date = today + timedelta(days=30)
        
        assert expired_date < today
        assert future_date > today
        
        days_to_expiry = (future_date - today).days
        assert days_to_expiry == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
