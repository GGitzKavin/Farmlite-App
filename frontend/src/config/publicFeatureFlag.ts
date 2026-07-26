const ENABLED_PUBLIC_FLAG_VALUES = new Set(['1', 'true', 'yes', 'on']);

export const parsePublicFeatureFlag = (value: unknown): boolean =>
  typeof value === 'string' &&
  ENABLED_PUBLIC_FLAG_VALUES.has(value.trim().toLowerCase());
