import type { Livestock } from '../types';
import { calculateAgeInMonths } from '../utils/livestockStatus.ts';
import { INDIVIDUAL_LIVESTOCK_TYPES } from './livestockTypes.ts';

export interface InlineLivestockEditFormData {
  animalId: string;
  animalName: string;
  species: string;
  breed: string;
  birthDate: string;
  age: string;
  weight: string;
}

export interface InlineLivestockUpdate {
  animalId: string;
  animalName: string;
  species: string;
  breed: string;
  birthDate: string;
  age: number;
  weight: number;
}

export interface InlineLivestockTypeOption {
  value: string;
  label: string;
  legacy: boolean;
}

export interface InlineLivestockUpdateResult {
  value: InlineLivestockUpdate | null;
  error: string;
}

export const EMPTY_INLINE_LIVESTOCK_FORM: InlineLivestockEditFormData = {
  animalId: '',
  animalName: '',
  species: INDIVIDUAL_LIVESTOCK_TYPES[0],
  breed: '',
  birthDate: '',
  age: '',
  weight: '',
};

export const createInlineLivestockForm = (
  animal: Livestock
): InlineLivestockEditFormData => ({
  animalId: animal.animalId ?? '',
  animalName: animal.animalName ?? '',
  species:
    typeof animal.species === 'string' && animal.species.trim()
      ? animal.species
      : INDIVIDUAL_LIVESTOCK_TYPES[0],
  breed: animal.breed ?? '',
  birthDate: animal.birthDate ?? '',
  age: Number.isFinite(animal.age) ? String(animal.age) : '',
  weight: Number.isFinite(animal.weight) ? String(animal.weight) : '',
});

export const getInlineLivestockTypeOptions = (
  storedValue: string
): InlineLivestockTypeOption[] => {
  const normalizedStoredValue = storedValue.trim();
  const approvedOptions = INDIVIDUAL_LIVESTOCK_TYPES.map((value) => ({
    value,
    label: value,
    legacy: false,
  }));

  if (
    !normalizedStoredValue ||
    INDIVIDUAL_LIVESTOCK_TYPES.some(
      (value) => value === normalizedStoredValue
    )
  ) {
    return approvedOptions;
  }

  return [
    {
      value: normalizedStoredValue,
      label: 'Legacy stored value (retained)',
      legacy: true,
    },
    ...approvedOptions,
  ];
};

export const buildInlineLivestockUpdate = (
  formData: InlineLivestockEditFormData
): InlineLivestockUpdateResult => {
  const animalId = formData.animalId.trim();
  const animalName = formData.animalName.trim();
  const species = formData.species.trim();
  const breed = formData.breed.trim();
  const birthDate = formData.birthDate.trim();

  if (!animalId || !animalName || !species || !breed) {
    return {
      value: null,
      error: 'Animal ID, animal name, livestock and breed are required.',
    };
  }

  const enteredAge = Number(formData.age);
  const age = birthDate
    ? calculateAgeInMonths(birthDate)
    : enteredAge;
  if (
    age === null ||
    !Number.isFinite(age) ||
    age < 0
  ) {
    return {
      value: null,
      error: 'Enter a valid age or birth date.',
    };
  }

  const weight = Number(formData.weight);
  if (!Number.isFinite(weight) || weight <= 0) {
    return {
      value: null,
      error: 'Weight must be greater than zero.',
    };
  }

  return {
    value: {
      animalId,
      animalName,
      species,
      breed,
      birthDate,
      age,
      weight,
    },
    error: '',
  };
};
