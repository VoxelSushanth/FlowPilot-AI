/**
 * Core domain types for FlowPilot AI
 */

// Organization & Multi-tenancy
export interface Organization {
  id: string;
  name: string;
  slug: string;
  status: 'active' | 'suspended' | 'deleted';
  subscriptionTier: 'starter' | 'growth' | 'enterprise';
  settings: OrganizationSettings;
  createdAt: Date;
  updatedAt: Date;
}

export interface OrganizationSettings {
  timezone: string;
  currency: string;
  language: string;
  fiscalYearStart: string; // MM-DD format
  features: Record<string, boolean>;
}

// User & Authentication
export interface User {
  id: string;
  organizationId: string;
  email: string;
  name: string;
  role: UserRole;
  permissions: Permission[];
  status: 'active' | 'inactive' | 'suspended';
  lastLoginAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export type UserRole = 
  | 'super_admin'
  | 'owner'
  | 'warehouse_manager'
  | 'sales_manager'
  | 'sales_rep'
  | 'accountant'
  | 'viewer';

export interface Permission {
  resource: string;
  actions: Array<'read' | 'write' | 'delete' | 'admin'>;
}

// Product & Catalog
export interface Product {
  id: string;
  organizationId: string;
  sku: string;
  name: string;
  description?: string;
  categoryId?: string;
  brandId?: string;
  hsnCode?: string;
  barcode?: string;
  packagingUnits: PackagingUnit[];
  attributes: Record<string, any>;
  status: 'active' | 'inactive' | 'discontinued';
  createdAt: Date;
  updatedAt: Date;
}

export interface PackagingUnit {
  unitType: 'piece' | 'box' | 'case' | 'pallet';
  quantity: number;
  price: number;
  mrp: number;
  gstRate: number;
}

export interface Category {
  id: string;
  organizationId: string;
  name: string;
  parentId?: string;
  path: string; // Materialized path for hierarchy
  level: number;
}

// Inventory
export interface StockItem {
  id: string;
  organizationId: string;
  productId: string;
  locationId: string;
  batchNumber?: string;
  expiryDate?: Date;
  quantityAvailable: number;
  quantityReserved: number;
  quantityDamaged: number;
  reorderPoint: number;
  reorderQuantity: number;
  lastCountedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface StockMovement {
  id: string;
  organizationId: string;
  stockItemId: string;
  type: 'inward' | 'outward' | 'adjustment' | 'transfer' | 'return';
  quantity: number;
  referenceType: 'purchase_order' | 'sales_order' | 'manual' | 'system';
  referenceId: string;
  reason?: string;
  performedBy: string;
  createdAt: Date;
}

// Order Management
export interface SalesOrder {
  id: string;
  organizationId: string;
  orderNumber: string;
  retailerId: string;
  status: OrderStatus;
  items: SalesOrderItem[];
  subtotal: number;
  discountAmount: number;
  taxAmount: number;
  shippingAmount: number;
  totalAmount: number;
  paymentStatus: PaymentStatus;
  paymentTerms: PaymentTerms;
  shippingAddress: Address;
  billingAddress: Address;
  notes?: string;
  metadata?: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
  confirmedAt?: Date;
  shippedAt?: Date;
  deliveredAt?: Date;
  cancelledAt?: Date;
}

export type OrderStatus = 
  | 'draft'
  | 'pending_approval'
  | 'confirmed'
  | 'processing'
  | 'allocated'
  | 'shipped'
  | 'delivered'
  | 'cancelled'
  | 'returned';

export type PaymentStatus = 'pending' | 'partial' | 'paid' | 'overdue' | 'refunded';

export interface PaymentTerms {
  type: 'immediate' | 'credit' | 'cod';
  creditDays?: number;
  discountPercent?: number;
  discountDays?: number;
}

export interface SalesOrderItem {
  id: string;
  orderId: string;
  productId: string;
  sku: string;
  name: string;
  quantity: number;
  unitType: string;
  unitPrice: number;
  discountPercent: number;
  taxRate: number;
  totalPrice: number;
  allocatedQuantity: number;
  shippedQuantity: number;
}

// Retailer & Credit Management
export interface Retailer {
  id: string;
  organizationId: string;
  code: string;
  name: string;
  contactPerson?: string;
  phone: string;
  email?: string;
  gstNumber?: string;
  panNumber?: string;
  address: Address;
  shippingAddresses: Address[];
  creditLimit: number;
  creditDays: number;
  riskScore?: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'blocked' | 'inactive';
  tags: string[];
  salesRepId?: string;
  metadata?: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

export interface Address {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  latitude?: number;
  longitude?: number;
}

// Forecasting & AI
export interface DemandForecast {
  id: string;
  organizationId: string;
  productId: string;
  locationId: string;
  forecastDate: Date;
  predictedQuantity: number;
  confidenceScore: number;
  lowerBound: number;
  upperBound: number;
  modelVersion: string;
  features: Record<string, any>;
  createdAt: Date;
}

export interface ProcurementSuggestion {
  id: string;
  organizationId: string;
  productId: string;
  suggestedQuantity: number;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  reason: string;
  currentStock: number;
  predictedDemand: number;
  leadTimeDays: number;
  supplierId?: string;
  estimatedCost: number;
  createdAt: Date;
}

// Events & Audit
export interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateType: string;
  aggregateId: string;
  organizationId: string;
  payload: Record<string, any>;
  metadata: EventMetadata;
  timestamp: Date;
}

export interface EventMetadata {
  userId?: string;
  correlationId: string;
  causationId?: string;
  version: number;
}

// Common Types
export interface Auditable {
  createdAt: Date;
  updatedAt: Date;
  deletedAt?: Date;
  createdBy?: string;
  updatedBy?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export type Money = {
  amount: number;
  currency: string;
};
