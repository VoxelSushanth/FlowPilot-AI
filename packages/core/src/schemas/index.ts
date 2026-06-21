import { z } from 'zod';

// Organization Schemas
export const OrganizationSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  slug: z.string().regex(/^[a-z0-9-]+$/),
  status: z.enum(['active', 'suspended', 'deleted']),
  subscriptionTier: z.enum(['starter', 'growth', 'enterprise']),
  settings: z.object({
    timezone: z.string().default('Asia/Kolkata'),
    currency: z.string().default('INR'),
    language: z.string().default('en'),
    fiscalYearStart: z.string().regex(/^\d{2}-\d{2}$/).default('04-01'),
    features: z.record(z.boolean()).default({}),
  }),
  createdAt: z.date(),
  updatedAt: z.date(),
});

// User Schemas
export const UserRoleSchema = z.enum([
  'super_admin',
  'owner',
  'warehouse_manager',
  'sales_manager',
  'sales_rep',
  'accountant',
  'viewer',
]);

export const PermissionSchema = z.object({
  resource: z.string(),
  actions: z.array(z.enum(['read', 'write', 'delete', 'admin'])),
});

export const UserSchema = z.object({
  id: z.string().uuid(),
  organizationId: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(1).max(255),
  role: UserRoleSchema,
  permissions: z.array(PermissionSchema).default([]),
  status: z.enum(['active', 'inactive', 'suspended']),
  lastLoginAt: z.date().optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
});

// Product Schemas
export const PackagingUnitSchema = z.object({
  unitType: z.enum(['piece', 'box', 'case', 'pallet']),
  quantity: z.number().positive(),
  price: z.number().nonnegative(),
  mrp: z.number().nonnegative(),
  gstRate: z.number().min(0).max(100),
});

export const ProductSchema = z.object({
  id: z.string().uuid(),
  organizationId: z.string().uuid(),
  sku: z.string().min(1).max(100),
  name: z.string().min(1).max(255),
  description: z.string().max(1000).optional(),
  categoryId: z.string().uuid().optional(),
  brandId: z.string().uuid().optional(),
  hsnCode: z.string().max(8).optional(),
  barcode: z.string().max(100).optional(),
  packagingUnits: z.array(PackagingUnitSchema).min(1),
  attributes: z.record(z.any()).default({}),
  status: z.enum(['active', 'inactive', 'discontinued']),
  createdAt: z.date(),
  updatedAt: z.date(),
});

// Inventory Schemas
export const StockItemSchema = z.object({
  id: z.string().uuid(),
  organizationId: z.string().uuid(),
  productId: z.string().uuid(),
  locationId: z.string().uuid(),
  batchNumber: z.string().max(100).optional(),
  expiryDate: z.date().optional(),
  quantityAvailable: z.number().int().nonnegative(),
  quantityReserved: z.number().int().nonnegative(),
  quantityDamaged: z.number().int().nonnegative(),
  reorderPoint: z.number().int().nonnegative().default(0),
  reorderQuantity: z.number().int().nonnegative().default(0),
  lastCountedAt: z.date().optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
});

export const StockMovementSchema = z.object({
  id: z.string().uuid(),
  organizationId: z.string().uuid(),
  stockItemId: z.string().uuid(),
  type: z.enum(['inward', 'outward', 'adjustment', 'transfer', 'return']),
  quantity: z.number().int(),
  referenceType: z.enum(['purchase_order', 'sales_order', 'manual', 'system']),
  referenceId: z.string(),
  reason: z.string().max(500).optional(),
  performedBy: z.string().uuid(),
  createdAt: z.date(),
});

// Order Schemas
export const OrderStatusSchema = z.enum([
  'draft',
  'pending_approval',
  'confirmed',
  'processing',
  'allocated',
  'shipped',
  'delivered',
  'cancelled',
  'returned',
]);

export const PaymentStatusSchema = z.enum([
  'pending',
  'partial',
  'paid',
  'overdue',
  'refunded',
]);

export const PaymentTermsSchema = z.object({
  type: z.enum(['immediate', 'credit', 'cod']),
  creditDays: z.number().int().nonnegative().optional(),
  discountPercent: z.number().min(0).max(100).optional(),
  discountDays: z.number().int().nonnegative().optional(),
});

export const AddressSchema = z.object({
  line1: z.string().min(1).max(255),
  line2: z.string().max(255).optional(),
  city: z.string().min(1).max(100),
  state: z.string().min(1).max(100),
  pincode: z.string().regex(/^\d{6}$/),
  country: z.string().default('India'),
  latitude: z.number().optional(),
  longitude: z.number().optional(),
});

export const SalesOrderItemSchema = z.object({
  id: z.string().uuid(),
  orderId: z.string().uuid(),
  productId: z.string().uuid(),
  sku: z.string(),
  name: z.string(),
  quantity: z.number().int().positive(),
  unitType: z.string(),
  unitPrice: z.number().nonnegative(),
  discountPercent: z.number().min(0).max(100).default(0),
  taxRate: z.number().min(0).max(100).default(0),
  totalPrice: z.number().nonnegative(),
  allocatedQuantity: z.number().int().nonnegative().default(0),
  shippedQuantity: z.number().int().nonnegative().default(0),
});

export const SalesOrderSchema = z.object({
  id: z.string().uuid(),
  organizationId: z.string().uuid(),
  orderNumber: z.string(),
  retailerId: z.string().uuid(),
  status: OrderStatusSchema,
  items: z.array(SalesOrderItemSchema).min(1),
  subtotal: z.number().nonnegative(),
  discountAmount: z.number().nonnegative().default(0),
  taxAmount: z.number().nonnegative().default(0),
  shippingAmount: z.number().nonnegative().default(0),
  totalAmount: z.number().nonnegative(),
  paymentStatus: PaymentStatusSchema,
  paymentTerms: PaymentTermsSchema,
  shippingAddress: AddressSchema,
  billingAddress: AddressSchema,
  notes: z.string().max(1000).optional(),
  metadata: z.record(z.any()).optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
  confirmedAt: z.date().optional(),
  shippedAt: z.date().optional(),
  deliveredAt: z.date().optional(),
  cancelledAt: z.date().optional(),
});

// Retailer Schemas
export const RetailerSchema = z.object({
  id: z.string().uuid(),
  organizationId: z.string().uuid(),
  code: z.string().min(1).max(50),
  name: z.string().min(1).max(255),
  contactPerson: z.string().max(255).optional(),
  phone: z.string().regex(/^\d{10}$/),
  email: z.string().email().optional(),
  gstNumber: z.string().regex(/^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[A-Z]\d$/).optional(),
  panNumber: z.string().regex(/^[A-Z]{5}\d{4}[A-Z]{1}$/).optional(),
  address: AddressSchema,
  shippingAddresses: z.array(AddressSchema).default([]),
  creditLimit: z.number().nonnegative().default(0),
  creditDays: z.number().int().nonnegative().default(0),
  riskScore: z.number().min(0).max(100).optional(),
  riskLevel: z.enum(['low', 'medium', 'high', 'critical']).default('low'),
  status: z.enum(['active', 'blocked', 'inactive']),
  tags: z.array(z.string()).default([]),
  salesRepId: z.string().uuid().optional(),
  metadata: z.record(z.any()).optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
});

// Forecasting Schemas
export const DemandForecastSchema = z.object({
  id: z.string().uuid(),
  organizationId: z.string().uuid(),
  productId: z.string().uuid(),
  locationId: z.string().uuid(),
  forecastDate: z.date(),
  predictedQuantity: z.number().nonnegative(),
  confidenceScore: z.number().min(0).max(1),
  lowerBound: z.number().nonnegative(),
  upperBound: z.number().nonnegative(),
  modelVersion: z.string(),
  features: z.record(z.any()),
  createdAt: z.date(),
});

export const ProcurementSuggestionSchema = z.object({
  id: z.string().uuid(),
  organizationId: z.string().uuid(),
  productId: z.string().uuid(),
  suggestedQuantity: z.number().int().positive(),
  urgency: z.enum(['low', 'medium', 'high', 'critical']),
  reason: z.string(),
  currentStock: z.number().int().nonnegative(),
  predictedDemand: z.number().nonnegative(),
  leadTimeDays: z.number().int().nonnegative(),
  supplierId: z.string().uuid().optional(),
  estimatedCost: z.number().nonnegative(),
  createdAt: z.date(),
});

// Event Schemas
export const DomainEventSchema = z.object({
  eventId: z.string().uuid(),
  eventType: z.string(),
  aggregateType: z.string(),
  aggregateId: z.string(),
  organizationId: z.string().uuid(),
  payload: z.record(z.any()),
  metadata: z.object({
    userId: z.string().uuid().optional(),
    correlationId: z.string().uuid(),
    causationId: z.string().uuid().optional(),
    version: z.number().int().positive(),
  }),
  timestamp: z.date(),
});

// Pagination Schema
export const PaginationSchema = z.object({
  page: z.number().int().positive().default(1),
  limit: z.number().int().positive().max(100).default(20),
});

export const PaginatedResponseSchema = <T extends z.ZodType>(dataSchema: T) =>
  z.object({
    data: z.array(dataSchema),
    pagination: z.object({
      page: z.number().int().positive(),
      limit: z.number().int().positive(),
      total: z.number().int().nonnegative(),
      totalPages: z.number().int().nonnegative(),
    }),
  });

// Export type inference helpers
export type OrganizationInput = z.infer<typeof OrganizationSchema>;
export type UserInput = z.infer<typeof UserSchema>;
export type ProductInput = z.infer<typeof ProductSchema>;
export type StockItemInput = z.infer<typeof StockItemSchema>;
export type SalesOrderInput = z.infer<typeof SalesOrderSchema>;
export type RetailerInput = z.infer<typeof RetailerSchema>;
