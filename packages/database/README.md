# FlowPilot AI - Database Package

PostgreSQL ORM layer with multi-tenancy support, migrations, and domain models.

## Features

- **Multi-tenancy**: Logical isolation via `organization_id` on all tables
- **Soft Deletes**: Built-in `deleted_at` tracking
- **Audit Trail**: `created_at`, `updated_at` timestamps
- **Type Safety**: SQLAlchemy 2.0 with full type hints
- **Migrations**: Alembic-based schema versioning

## Installation

```bash
pip install -e packages/database
```

## Usage

### Session Management

```python
from flowpilot_database import get_db_session, tenant_id_context

# Get database session
with get_db_session() as session:
    # Query within tenant context
    with tenant_id_context(org_id=123):
        products = session.query(Product).all()
```

### Using Models

```python
from flowpilot_database.models import Organization, User, Product

# Create organization
org = Organization(
    name="Acme Distributors",
    slug="acme-dist",
    email="contact@acme.com"
)
session.add(org)
session.commit()
```

## Domain Models

- **Organization**: Multi-tenant root entity
- **User**: User accounts with RBAC
- **Product**: Catalog with pricing tiers
- **Inventory**: Warehouses, stock, batches
- **Order**: Sales/purchase orders, returns
- **Retailer**: Customer profiles with credit/risk

## Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/flowpilot` |

## Architecture Decisions

1. **Logical Multi-tenancy**: Single database with `organization_id` filtering
2. **Soft Deletes**: Preserve data for audit/compliance
3. **JSONB Fields**: Flexible attributes without schema changes
4. **Explicit Relationships**: Lazy loading for performance
