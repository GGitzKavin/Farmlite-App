export const STOCK_ADJUSTMENT_PERCENT = 0.1;
export const MAX_STOCK_QUANTITY = 1_000_000;

export type StockAdjustmentDirection = 'decrease' | 'increase';

const WHOLE_ITEM_UNITS = new Set([
  'item',
  'items',
  'unit',
  'units',
  'piece',
  'pieces',
  'bag',
  'bags',
  'bale',
  'bales',
  'sack',
  'sacks',
]);

export const getFeedUnit = (unit?: string): string => {
  const normalizedUnit = unit?.trim();
  return normalizedUnit || 'kg';
};

export const usesWholeItemPrecision = (unit?: string): boolean =>
  WHOLE_ITEM_UNITS.has(getFeedUnit(unit).toLowerCase());

export const roundStockQuantity = (quantity: number, unit?: string): number => {
  const precision = usesWholeItemPrecision(unit) ? 1 : 100;
  return Math.round((quantity + Number.EPSILON) * precision) / precision;
};

export const formatStockQuantity = (quantity: number, unit?: string): string => {
  const safeQuantity = Number.isFinite(quantity) ? Math.max(0, quantity) : 0;
  const wholeItems = usesWholeItemPrecision(unit);

  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: wholeItems ? 0 : 2,
  }).format(roundStockQuantity(safeQuantity, unit));
};

export const calculatePercentageStock = (
  currentQuantity: number,
  direction: StockAdjustmentDirection,
  unit?: string,
): number => {
  if (!Number.isFinite(currentQuantity) || currentQuantity < 0) {
    throw new Error('The current stock quantity is invalid.');
  }

  const multiplier =
    direction === 'decrease'
      ? 1 - STOCK_ADJUSTMENT_PERCENT
      : 1 + STOCK_ADJUSTMENT_PERCENT;

  return roundStockQuantity(Math.max(0, currentQuantity * multiplier), unit);
};

export const calculateRestockedStock = (
  currentQuantity: number,
  receivedQuantity: number,
  unit?: string,
): number => {
  if (
    !Number.isFinite(currentQuantity) ||
    currentQuantity < 0 ||
    !Number.isFinite(receivedQuantity) ||
    receivedQuantity <= 0
  ) {
    throw new Error('The stock quantities are invalid.');
  }

  const newQuantity = roundStockQuantity(
    currentQuantity + receivedQuantity,
    unit,
  );

  if (!Number.isFinite(newQuantity) || newQuantity > MAX_STOCK_QUANTITY) {
    throw new Error('The resulting stock quantity exceeds the allowed limit.');
  }

  return newQuantity;
};

export interface RestockValidation {
  value: number | null;
  error: string;
}

export const validateRestockQuantity = (
  rawQuantity: string,
  unit?: string,
): RestockValidation => {
  const normalizedQuantity = rawQuantity.trim();

  if (!normalizedQuantity) {
    return {
      value: null,
      error: 'Enter a quantity greater than zero.',
    };
  }

  const numericQuantity = Number(normalizedQuantity);
  const numericPattern = /^[+-]?(?:\d+\.?\d*|\.\d+)$/;
  if (!numericPattern.test(normalizedQuantity) || !Number.isFinite(numericQuantity)) {
    return {
      value: null,
      error: 'Enter a valid numeric quantity.',
    };
  }

  if (numericQuantity <= 0) {
    return {
      value: null,
      error: 'Enter a quantity greater than zero.',
    };
  }

  if (numericQuantity > MAX_STOCK_QUANTITY) {
    return {
      value: null,
      error: `Enter a quantity no greater than ${MAX_STOCK_QUANTITY.toLocaleString()}.`,
    };
  }

  const wholeItems = usesWholeItemPrecision(unit);
  const allowedPrecision = wholeItems ? 0 : 2;
  const decimalPart = normalizedQuantity.split('.')[1] ?? '';

  if (
    decimalPart.length > allowedPrecision ||
    (wholeItems && !Number.isInteger(numericQuantity))
  ) {
    return {
      value: null,
      error: wholeItems
        ? 'Enter a whole-number quantity for this feed unit.'
        : 'Enter a quantity with no more than two decimal places.',
    };
  }

  return {
    value: roundStockQuantity(numericQuantity, unit),
    error: '',
  };
};

export const calculateFeedStockLevel = (
  quantity: number,
  lowStockThreshold: number,
): 'High' | 'Medium' | 'Low' | 'Out of Stock' => {
  if (quantity <= 0) return 'Out of Stock';
  if (quantity <= lowStockThreshold) return 'Low';
  if (quantity <= lowStockThreshold * 2) return 'Medium';
  return 'High';
};
