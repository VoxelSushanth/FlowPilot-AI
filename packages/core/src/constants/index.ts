/**
 * Application-wide constants for FlowPilot AI
 */

// Subscription Tiers
export const SUBSCRIPTION_TIERS = {
  STARTER: 'starter',
  GROWTH: 'growth',
  ENTERPRISE: 'enterprise',
} as const;

export const SUBSCRIPTION_LIMITS = {
  starter: {
    maxOrdersPerMonth: 1000,
    maxUsers: 5,
    maxProducts: 1000,
    maxRetailers: 500,
    aiFeaturesEnabled: false,
    apiRateLimit: 100, // requests per minute
  },
  growth: {
    maxOrdersPerMonth: 5000,
    maxUsers: 20,
    maxProducts: 10000,
    maxRetailers: 2000,
    aiFeaturesEnabled: true,
    apiRateLimit: 500,
  },
  enterprise: {
    maxOrdersPerMonth: -1, // unlimited
    maxUsers: -1,
    maxProducts: -1,
    maxRetailers: -1,
    aiFeaturesEnabled: true,
    apiRateLimit: 2000,
  },
} as const;

// Order Status Transitions
export const ORDER_STATUS_TRANSITIONS = {
  draft: ['confirmed', 'cancelled'],
  pending_approval: ['confirmed', 'cancelled'],
  confirmed: ['processing', 'cancelled'],
  processing: ['allocated', 'cancelled'],
  allocated: ['shipped', 'cancelled'],
  shipped: ['delivered', 'returned'],
  delivered: ['returned'],
  cancelled: [],
  returned: [],
} as const;

// Payment Terms
export const PAYMENT_TERM_TYPES = {
  IMMEDIATE: 'immediate',
  CREDIT: 'credit',
  COD: 'cod',
} as const;

export const DEFAULT_CREDIT_DAYS = 0;
export const MAX_CREDIT_DAYS = 90;

// Inventory Management
export const STOCK_MOVEMENT_TYPES = {
  INWARD: 'inward',
  OUTWARD: 'outward',
  ADJUSTMENT: 'adjustment',
  TRANSFER: 'transfer',
  RETURN: 'return',
} as const;

export const INVENTORY_REFERENCE_TYPES = {
  PURCHASE_ORDER: 'purchase_order',
  SALES_ORDER: 'sales_order',
  MANUAL: 'manual',
  SYSTEM: 'system',
} as const;

// Default reorder settings
export const DEFAULT_REORDER_POINT = 10;
export const DEFAULT_REORDER_QUANTITY = 50;

// User Roles & Permissions
export const USER_ROLES = {
  SUPER_ADMIN: 'super_admin',
  OWNER: 'owner',
  WAREHOUSE_MANAGER: 'warehouse_manager',
  SALES_MANAGER: 'sales_manager',
  SALES_REP: 'sales_rep',
  ACCOUNTANT: 'accountant',
  VIEWER: 'viewer',
} as const;

export const ROLE_HIERARCHY = {
  super_admin: 100,
  owner: 90,
  warehouse_manager: 70,
  sales_manager: 60,
  accountant: 50,
  sales_rep: 40,
  viewer: 10,
} as const;

// Default permissions by role
export const DEFAULT_ROLE_PERMISSIONS = {
  super_admin: {
    '*': ['read', 'write', 'delete', 'admin'],
  },
  owner: {
    '*': ['read', 'write', 'delete'],
  },
  warehouse_manager: {
    inventory: ['read', 'write'],
    product: ['read', 'write'],
    order: ['read', 'write'],
    retailer: ['read'],
  },
  sales_manager: {
    order: ['read', 'write'],
    retailer: ['read', 'write'],
    product: ['read'],
    inventory: ['read'],
  },
  sales_rep: {
    order: ['read', 'write'],
    retailer: ['read'],
    product: ['read'],
    inventory: ['read'],
  },
  accountant: {
    order: ['read'],
    retailer: ['read', 'write'],
    payment: ['read', 'write'],
  },
  viewer: {
    '*': ['read'],
  },
} as const;

// Risk Levels
export const RISK_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical',
} as const;

export const RISK_SCORE_THRESHOLDS = {
  low: { min: 0, max: 30 },
  medium: { min: 31, max: 60 },
  high: { min: 61, max: 85 },
  critical: { min: 86, max: 100 },
} as const;

// Geographic Constants (India-focused)
export const INDIAN_STATES = [
  'Andhra Pradesh',
  'Arunachal Pradesh',
  'Assam',
  'Bihar',
  'Chhattisgarh',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Sikkim',
  'Tamil Nadu',
  'Telangana',
  'Tripura',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
] as const;

export const INDIAN_TIMEZONE = 'Asia/Kolkata';
export const INDIAN_CURRENCY = 'INR';
export const INDIAN_FISCAL_YEAR_START = '04-01'; // April 1st

// GST Rates (common slabs)
export const GST_RATES = [0, 5, 12, 18, 28] as const;

// Packaging Units
export const PACKAGING_UNITS = {
  PIECE: 'piece',
  BOX: 'box',
  CASE: 'case',
  PALLET: 'pallet',
} as const;

// Date Formats
export const DATE_FORMATS = {
  DISPLAY: 'DD MMM YYYY',
  INPUT: 'YYYY-MM-DD',
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  ISO: 'YYYY-MM-DDTHH:mm:ss.SSSZ',
} as const;

// Pagination Defaults
export const PAGINATION_DEFAULTS = {
  PAGE: 1,
  LIMIT: 20,
  MAX_LIMIT: 100,
} as const;

// API Rate Limiting
export const RATE_LIMIT_WINDOWS = {
  SHORT: 60, // 1 minute
  MEDIUM: 300, // 5 minutes
  LONG: 3600, // 1 hour
} as const;

// Event Types (for Kafka/Event Bus)
export const EVENT_TYPES = {
  // Core Domain Events
  ORDER_CREATED: 'order.created',
  ORDER_CONFIRMED: 'order.confirmed',
  ORDER_SHIPPED: 'order.shipped',
  ORDER_DELIVERED: 'order.delivered',
  ORDER_CANCELLED: 'order.cancelled',
  
  INVENTORY_UPDATED: 'inventory.updated',
  STOCK_LOW: 'inventory.low',
  STOCK_EXPIRED: 'inventory.expired',
  
  RETAILER_CREATED: 'retailer.created',
  RETAILER_UPDATED: 'retailer.updated',
  RETAILER_BLOCKED: 'retailer.blocked',
  
  PAYMENT_RECEIVED: 'payment.received',
  PAYMENT_OVERDUE: 'payment.overdue',
  
  // AI/ML Events
  FORECAST_GENERATED: 'forecast.generated',
  PROCUREMENT_SUGGESTION: 'procurement.suggestion',
  RISK_SCORE_UPDATED: 'risk.score_updated',
  
  // System Events
  USER_CREATED: 'user.created',
  USER_LOGIN: 'user.login',
  AUDIT_LOG: 'audit.log',
} as const;

// Feature Flags
export const FEATURE_FLAGS = {
  AI_FORECASTING: 'ai_forecasting',
  AI_RISK_SCORING: 'ai_risk_scoring',
  AI_COPILOT: 'ai_copilot',
  ADVANCED_ANALYTICS: 'advanced_analytics',
  MULTI_WAREHOUSE: 'multi_warehouse',
  BATCH_TRACKING: 'batch_tracking',
  EXPIRY_MANAGEMENT: 'expiry_management',
  ROUTE_OPTIMIZATION: 'route_optimization',
} as const;

// Error Codes
export const ERROR_CODES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  CONFLICT: 'CONFLICT',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  SUBSCRIPTION_LIMIT_EXCEEDED: 'SUBSCRIPTION_LIMIT_EXCEEDED',
  INSUFFICIENT_STOCK: 'INSUFFICIENT_STOCK',
  CREDIT_LIMIT_EXCEEDED: 'CREDIT_LIMIT_EXCEEDED',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
} as const;
