export const INDIVIDUAL_LIVESTOCK_TYPES = [
  'Dairy Cattle',
  'Cattle (Beef)',
  'Sheep/Goats',
  'Swine',
] as const;

export const BATCH_LIVESTOCK_TYPES = [
  'Dairy Cattle',
  'Cattle (Beef)',
  'Sheep/Goats',
  'Chicken',
  'Duck',
  'Swine',
] as const;

export const ALL_LIVESTOCK_TYPES = Array.from(
  new Set([...INDIVIDUAL_LIVESTOCK_TYPES, ...BATCH_LIVESTOCK_TYPES])
);

export const includeStoredLivestockType = (
  options: readonly string[],
  storedValue: string | undefined
): string[] => {
  const existingValue = storedValue?.trim() ?? '';
  if (!existingValue || options.includes(existingValue)) {
    return [...options];
  }

  return [existingValue, ...options];
};
