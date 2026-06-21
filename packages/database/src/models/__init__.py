"""
Domain models for FlowPilot AI.

Organized by bounded context:
- organization: Multi-tenancy, users, roles
- product: Catalog, SKUs, pricing
- inventory: Stock levels, batches, warehouses
- order: Sales orders, purchase orders, returns
- retailer: Customer profiles, credit, risk scoring
"""

from .organization import Organization, User, Role, UserRole
from .product import Product, ProductCategory, PricingTier
from .inventory import Warehouse, StockItem, StockMovement, Batch
from .order import SalesOrder, OrderItem, PurchaseOrder, ReturnOrder
from .retailer import Retailer, CreditLimit, RiskScore

__all__ = [
    # Organization
    "Organization",
    "User",
    "Role",
    "UserRole",
    # Product
    "Product",
    "ProductCategory",
    "PricingTier",
    # Inventory
    "Warehouse",
    "StockItem",
    "StockMovement",
    "Batch",
    # Order
    "SalesOrder",
    "OrderItem",
    "PurchaseOrder",
    "ReturnOrder",
    # Retailer
    "Retailer",
    "CreditLimit",
    "RiskScore",
]
