export const FARM_TYPE_MAX_LENGTH = 80;

export const loadFarmType = (value: unknown): string =>
  typeof value === 'string' ? value : '';

export const validateFarmType = (value: string): string => {
  const trimmed = value.trim();
  if (!trimmed) return 'Farm type is required.';
  if (trimmed.length > FARM_TYPE_MAX_LENGTH) {
    return `Farm type must be ${FARM_TYPE_MAX_LENGTH} characters or fewer.`;
  }
  return '';
};

export const normalizeFarmType = (value: string): string => value.trim();
