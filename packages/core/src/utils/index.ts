/**
 * Utility functions for FlowPilot AI
 */

import { v4 as uuidv4 } from 'uuid';
import { format, parseISO, isValid } from 'date-fns';
import { INDIAN_TIMEZONE } from '../constants';

/**
 * Generate a UUID v4
 */
export function generateId(): string {
  return uuidv4();
}

/**
 * Generate a human-readable order number
 * Format: FP-YYYYMMDD-XXXXX
 */
export function generateOrderNumber(): string {
  const date = new Date();
  const dateStr = format(date, 'yyyyMMdd');
  const random = Math.floor(10000 + Math.random() * 90000);
  return `FP-${dateStr}-${random}`;
}

/**
 * Generate a retailer code
 * Format: RT-XXXXX
 */
export function generateRetailerCode(): string {
  const random = Math.floor(10000 + Math.random() * 90000);
  return `RT-${random}`;
}

/**
 * Generate a product SKU
 * Format: SKU-XXXXX (or use provided prefix)
 */
export function generateSku(prefix?: string): string {
  const random = Math.floor(10000 + Math.random() * 90000);
  return prefix ? `${prefix}-${random}` : `SKU-${random}`;
}

/**
 * Format date to Indian timezone
 */
export function formatDateToIST(date: Date | string, formatStr = 'yyyy-MM-dd'): string {
  const parsed = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(parsed)) {
    throw new Error('Invalid date provided');
  }
  return format(parsed, formatStr);
}

/**
 * Get current time in Indian timezone
 */
export function getCurrentTimeInIST(): Date {
  // For now, use system timezone; can be enhanced with date-fns-tz
  return new Date();
}

/**
 * Calculate days between two dates
 */
export function daysBetween(date1: Date | string, date2: Date | string): number {
  const d1 = typeof date1 === 'string' ? parseISO(date1) : date1;
  const d2 = typeof date2 === 'string' ? parseISO(date2) : date2;
  
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * Check if a date is overdue based on credit days
 */
export function isOverdue(dueDate: Date | string, graceDays = 0): boolean {
  const due = typeof dueDate === 'string' ? parseISO(dueDate) : dueDate;
  const today = getCurrentTimeInIST();
  
  if (graceDays > 0) {
    const graceEndDate = new Date(due);
    graceEndDate.setDate(graceEndDate.getDate() + graceDays);
    return today > graceEndDate;
  }
  
  return today > due;
}

/**
 * Calculate money with proper rounding
 */
export function calculateMoney(amount: number, decimals = 2): number {
  return Number(amount.toFixed(decimals));
}

/**
 * Calculate GST amount
 */
export function calculateGST(amount: number, gstRate: number): number {
  return calculateMoney((amount * gstRate) / 100);
}

/**
 * Calculate discount amount
 */
export function calculateDiscount(amount: number, discountPercent: number): number {
  return calculateMoney((amount * discountPercent) / 100);
}

/**
 * Calculate total with tax and discount
 */
export function calculateTotal(params: {
  subtotal: number;
  discountAmount?: number;
  taxRate?: number;
  shippingAmount?: number;
}): number {
  const { subtotal, discountAmount = 0, taxRate = 0, shippingAmount = 0 } = params;
  
  const afterDiscount = subtotal - discountAmount;
  const tax = calculateGST(afterDiscount, taxRate);
  
  return calculateMoney(afterDiscount + tax + shippingAmount);
}

/**
 * Validate Indian GST number
 * Format: 2 digits state code + 10 char PAN + 1 digit entity + 1 char Z + 1 check digit
 */
export function validateGSTNumber(gstNumber: string): boolean {
  const gstRegex = /^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[A-Z]\d$/;
  return gstRegex.test(gstNumber);
}

/**
 * Validate Indian PAN number
 * Format: 5 letters + 4 digits + 1 letter
 */
export function validatePANNumber(panNumber: string): boolean {
  const panRegex = /^[A-Z]{5}\d{4}[A-Z]{1}$/;
  return panRegex.test(panNumber);
}

/**
 * Validate Indian pincode
 * Format: 6 digits
 */
export function validatePincode(pincode: string): boolean {
  const pincodeRegex = /^\d{6}$/;
  return pincodeRegex.test(pincode);
}

/**
 * Validate Indian phone number
 * Format: 10 digits starting with 6-9
 */
export function validatePhoneNumber(phone: string): boolean {
  const phoneRegex = /^[6-9]\d{9}$/;
  return phoneRegex.test(phone);
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Throttle function
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Deep clone an object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Pick specific keys from an object
 */
export function pick<T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> {
  return keys.reduce((acc, key) => {
    if (key in obj) {
      acc[key] = obj[key];
    }
    return acc;
  }, {} as Pick<T, K>);
}

/**
 * Omit specific keys from an object
 */
export function omit<T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> {
  const result = { ...obj };
  keys.forEach((key) => {
    delete result[key];
  });
  return result as Omit<T, K>;
}

/**
 * Sleep utility for async operations
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry a function with exponential backoff
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number;
    initialDelay?: number;
    maxDelay?: number;
    multiplier?: number;
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    multiplier = 2,
  } = options;
  
  let lastError: Error;
  let delay = initialDelay;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      if (attempt === maxRetries) {
        break;
      }
      
      await sleep(delay);
      delay = Math.min(delay * multiplier, maxDelay);
    }
  }
  
  throw lastError!;
}

/**
 * Chunk an array into smaller arrays
 */
export function chunk<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

/**
 * Group array by key
 */
export function groupBy<T, K extends keyof any>(
  array: T[],
  keyFn: (item: T) => K
): Record<K, T[]> {
  return array.reduce((acc, item) => {
    const key = keyFn(item);
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(item);
    return acc;
  }, {} as Record<K, T[]>);
}

/**
 * Safely parse JSON
 */
export function safeJsonParse<T>(json: string, defaultValue: T): T {
  try {
    return JSON.parse(json) as T;
  } catch {
    return defaultValue;
  }
}

/**
 * Truncate string with ellipsis
 */
export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

/**
 * Slugify a string
 */
export function slugify(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}
