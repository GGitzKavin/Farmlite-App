import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { collection, getDocs } from 'firebase/firestore';
import { AlertCircle, Bot, Droplets, Info, Leaf, Loader2, Sparkles, Wheat } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { db } from '../firebase/config';
import { calculateAgeInMonths, getDisplaySpecies, parseDateValue, toText } from '../utils/livestockStatus';

const API_BASE_URL = import.meta.env.VITE_FLASK_API_URL || 'http://127.0.0.1:5000';

interface LivestockRecord {
  id: string;
  animalId: string;
  animalName: string;
  species: string;
  breed: string;
  ageMonths: string;
  weightKg: string;
  birthDate?: unknown;
  userId?: string;
}

interface HealthRecordLike {
  id: string;
  livestockId?: unknown;
  animalId?: unknown;
  status?: unknown;
  healthStatus?: unknown;
  condition?: unknown;
  recoveryStatus?: unknown;
  createdAt?: unknown;
  updatedAt?: unknown;
  date?: unknown;
  userId?: unknown;
}

interface FeedFormData {
  selectedAnimalId: string;
  animalId: string;
  animalName: string;
  breed: string;
  ageMonths: string;
  weightKg: string;
  lactationStage: string;
  daysInMilk: string;
  ambientTemperatureC: string;
  humidityPercent: string;
  previousWeekAvgYield: string;
  bodyConditionScore: string;
  healthStatus: string;
}

interface FeedRecommendationResponse {
  success: boolean;
  animalId?: string | null;
  animalName?: string | null;
  prediction: {
    predictedMilkYieldL: number;
    modelUsed: string;
    target: string;
    featuresUsed?: string[];
    modelLimitation?: string;
  };
  recommendation: {
    totalFeedKg: number;
    roughageKg: number;
    concentrateKg: number;
    mineralMixKg: number;
    waterAdvice: string;
    feedingFrequency: string;
    confidenceLevel: string;
    explanation: string[];
    warnings: string[];
    disclaimer: string;
  };
  limitations: string[];
}

const createInitialFormData = (): FeedFormData => ({
  selectedAnimalId: '',
  animalId: '',
  animalName: '',
  breed: '',
  ageMonths: '',
  weightKg: '',
  lactationStage: 'Mid Lactation',
  daysInMilk: '0',
  ambientTemperatureC: '28',
  humidityPercent: '70',
  previousWeekAvgYield: '0',
  bodyConditionScore: '3.0',
  healthStatus: 'Healthy',
});

const getFirstText = (record: Record<string, unknown>, keys: string[]) => {
  for (const key of keys) {
    const value = toText(record[key]);
    if (value) return value;
  }
  return '';
};

const getFirstNumber = (record: Record<string, unknown>, keys: string[]) => {
  for (const key of keys) {
    const rawValue = record[key];
    if (typeof rawValue === 'number' && Number.isFinite(rawValue)) {
      return rawValue;
    }

    if (typeof rawValue === 'string') {
      const match = rawValue.match(/-?\d+(\.\d+)?/);
      if (match) {
        const parsed = Number(match[0]);
        if (Number.isFinite(parsed)) return parsed;
      }
    }
  }
  return null;
};

const isCattleSpecies = (species: string) => {
  const normalizedSpecies = species.toLowerCase();
  const isClearlyUnsuitable = ['sheep', 'goat', 'chicken', 'duck', 'poultry', 'swine', 'beef'].some((keyword) =>
    normalizedSpecies.includes(keyword)
  );
  if (isClearlyUnsuitable) return false;

  return (
    normalizedSpecies === 'dairy cattle' ||
    normalizedSpecies === 'dairy cow' ||
    normalizedSpecies === 'cattle (dairy)' ||
    normalizedSpecies === 'cow'
  );
};

const getSpeciesPriority = (species: string) => {
  const normalizedSpecies = species.toLowerCase();
  if (normalizedSpecies === 'dairy cattle') return 0;
  if (normalizedSpecies === 'dairy cow' || normalizedSpecies === 'cattle (dairy)') return 1;
  if (normalizedSpecies === 'cow') return 2;
  return 3;
};

const resolveAgeMonths = (record: Record<string, unknown>) => {
  const birthDateText = getFirstText(record, ['birthDate', 'dateOfBirth', 'dob']);
  if (birthDateText) {
    const calculatedAge = calculateAgeInMonths(birthDateText);
    if (calculatedAge !== null) return String(calculatedAge);
  }

  const ageMonths = getFirstNumber(record, ['ageMonths', 'ageInMonths']);
  if (ageMonths !== null) return String(Math.round(ageMonths));

  const ageYears = getFirstNumber(record, ['ageYears', 'ageInYears']);
  if (ageYears !== null) return String(Math.round(ageYears * 12));

  const rawAge = record.age;
  if (typeof rawAge === 'string') {
    const ageValue = getFirstNumber(record, ['age']);
    if (ageValue === null) return '';

    const normalizedAge = rawAge.toLowerCase();
    if (normalizedAge.includes('year')) return String(Math.round(ageValue * 12));
    return String(Math.round(ageValue));
  }

  const numericAge = getFirstNumber(record, ['age']);
  return numericAge === null ? '' : String(Math.round(numericAge));
};

const normalizeLivestockRecord = (
  documentId: string,
  data: Record<string, unknown>
): LivestockRecord | null => {
  const species = getFirstText(data, ['species', 'animalType', 'type']);
  if (!isCattleSpecies(species)) return null;

  return {
    id: documentId,
    animalId: getFirstText(data, ['animalId', 'tagId', 'tagID']) || documentId,
    animalName: getFirstText(data, ['animalName', 'name']) || 'Unnamed Animal',
    species: getDisplaySpecies(species),
    breed: getFirstText(data, ['breed']),
    ageMonths: resolveAgeMonths(data),
    weightKg: String(getFirstNumber(data, ['weightKg', 'weight']) ?? ''),
    birthDate: data.birthDate,
    userId: getFirstText(data, ['userId']),
  };
};

const getRecordTime = (record: HealthRecordLike) =>
  parseDateValue(record.updatedAt)?.getTime() ??
  parseDateValue(record.createdAt)?.getTime() ??
  parseDateValue(record.date)?.getTime() ??
  0;

const getHealthStatusValue = (record: HealthRecordLike) =>
  toText(record.status) ||
  toText(record.healthStatus) ||
  toText(record.condition) ||
  toText(record.recoveryStatus);

const deriveLatestHealthStatus = (
  healthRecords: HealthRecordLike[],
  animal: LivestockRecord
) => {
  const relatedRecords = healthRecords
    .filter((record) => {
      const livestockId = toText(record.livestockId);
      const recordAnimalId = toText(record.animalId);
      return (
        livestockId === animal.id ||
        livestockId === animal.animalId ||
        recordAnimalId === animal.id ||
        recordAnimalId === animal.animalId
      );
    })
    .sort((left, right) => getRecordTime(right) - getRecordTime(left));

  const latestStatus = relatedRecords.map(getHealthStatusValue).find(Boolean);
  return latestStatus || 'Healthy';
};

const toPositiveNumber = (value: string) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
};

const toNumberWithDefault = (value: string, fallback: number) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const FeedRecommendation: React.FC = () => {
  const { currentUser } = useAuth();
  const [searchParams] = useSearchParams();
  const [animals, setAnimals] = useState<LivestockRecord[]>([]);
  const [healthRecords, setHealthRecords] = useState<HealthRecordLike[]>([]);
  const [loadingAnimals, setLoadingAnimals] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [validationMessage, setValidationMessage] = useState('');
  const [recommendation, setRecommendation] = useState<FeedRecommendationResponse | null>(null);
  const [formData, setFormData] = useState<FeedFormData>(createInitialFormData);

  const requestedAnimalId = searchParams.get('id') || '';

  const fetchPageData = useCallback(async () => {
    const currentUserId = currentUser?.uid;
    if (!currentUserId) {
      setAnimals([]);
      setHealthRecords([]);
      setLoadingAnimals(false);
      return;
    }

    setLoadingAnimals(true);
    setError('');

    try {
      const [livestockSnapshot, healthSnapshot] = await Promise.all([
        getDocs(collection(db, 'livestock')),
        getDocs(collection(db, 'healthRecords')),
      ]);

      const nextAnimals = livestockSnapshot.docs
        .map((document) =>
          normalizeLivestockRecord(document.id, document.data() as Record<string, unknown>)
        )
        .filter((animal): animal is LivestockRecord => {
          if (!animal) return false;
          return !animal.userId || animal.userId === currentUserId;
        })
        .sort((left, right) => {
          const priorityDifference = getSpeciesPriority(left.species) - getSpeciesPriority(right.species);
          if (priorityDifference !== 0) return priorityDifference;
          return left.animalName.localeCompare(right.animalName);
        });

      const nextHealthRecords = healthSnapshot.docs
        .map((document) => ({
          id: document.id,
          ...document.data(),
        }) as HealthRecordLike)
        .filter((record) => {
          const userId = toText(record.userId);
          return !userId || userId === currentUserId;
        });

      setAnimals(nextAnimals);
      setHealthRecords(nextHealthRecords);
    } catch (fetchError) {
      console.error('Failed to load AI feed recommendation data:', fetchError);
      setError('Unable to load cattle records right now. Please refresh and try again.');
      setAnimals([]);
      setHealthRecords([]);
    } finally {
      setLoadingAnimals(false);
    }
  }, [currentUser?.uid]);

  useEffect(() => {
    void fetchPageData();
  }, [fetchPageData]);

  useEffect(() => {
    if (!requestedAnimalId || animals.length === 0) return;

    const requestedAnimal = animals.find(
      (animal) => animal.id === requestedAnimalId || animal.animalId === requestedAnimalId
    );
    if (!requestedAnimal) return;

    setFormData((previous) => {
      if (previous.selectedAnimalId === requestedAnimal.id) return previous;

      return {
        ...previous,
        selectedAnimalId: requestedAnimal.id,
        animalId: requestedAnimal.animalId,
        animalName: requestedAnimal.animalName,
        breed: requestedAnimal.breed,
        ageMonths: requestedAnimal.ageMonths,
        weightKg: requestedAnimal.weightKg,
        healthStatus: deriveLatestHealthStatus(healthRecords, requestedAnimal),
      };
    });
  }, [animals, healthRecords, requestedAnimalId]);

  const selectedAnimal = useMemo(
    () => animals.find((animal) => animal.id === formData.selectedAnimalId) ?? null,
    [animals, formData.selectedAnimalId]
  );

  const handleAnimalChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const animal = animals.find((item) => item.id === event.target.value);
    setRecommendation(null);
    setValidationMessage('');

    if (!animal) {
      setFormData(createInitialFormData());
      return;
    }

    setFormData((previous) => ({
      ...previous,
      selectedAnimalId: animal.id,
      animalId: animal.animalId,
      animalName: animal.animalName,
      breed: animal.breed,
      ageMonths: animal.ageMonths,
      weightKg: animal.weightKg,
      healthStatus: deriveLatestHealthStatus(healthRecords, animal),
    }));
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = event.target;
    setFormData((previous) => ({ ...previous, [name]: value }));
    setValidationMessage('');
  };

  const validateForm = () => {
    if (!formData.selectedAnimalId) return 'Please select a dairy cow record first.';
    if (!formData.breed.trim()) return 'Breed is required before generating a recommendation.';
    if (toPositiveNumber(formData.ageMonths) === null) return 'Age in months must be a positive number.';
    if (toPositiveNumber(formData.weightKg) === null) return 'Weight must be a positive number.';
    if (!formData.lactationStage.trim()) return 'Lactation stage is required.';
    return '';
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    const nextValidationMessage = validateForm();
    if (nextValidationMessage) {
      setValidationMessage(nextValidationMessage);
      return;
    }

    setSubmitting(true);
    setError('');
    setValidationMessage('');
    setRecommendation(null);

    const payload = {
      animalId: formData.animalId || formData.selectedAnimalId,
      animalName: formData.animalName,
      breed: formData.breed.trim(),
      ageMonths: toNumberWithDefault(formData.ageMonths, 0),
      weightKg: toNumberWithDefault(formData.weightKg, 0),
      lactationStage: formData.lactationStage,
      daysInMilk: toNumberWithDefault(formData.daysInMilk, 0),
      ambientTemperatureC: toNumberWithDefault(formData.ambientTemperatureC, 28),
      humidityPercent: toNumberWithDefault(formData.humidityPercent, 70),
      previousWeekAvgYield: toNumberWithDefault(formData.previousWeekAvgYield, 0),
      bodyConditionScore: toNumberWithDefault(formData.bodyConditionScore, 3.0),
      healthStatus: formData.healthStatus || 'Healthy',
      productionStage: formData.lactationStage,
    };

    try {
      const response = await axios.post<FeedRecommendationResponse>(
        `${API_BASE_URL}/api/ai/feed-recommendation`,
        payload
      );
      setRecommendation(response.data);
    } catch (requestError) {
      console.error('AI feed recommendation request failed:', requestError);

      if (!axios.isAxiosError(requestError)) {
        setError('Could not connect to the AI service. Please make sure the Flask backend is running.');
      } else if (!requestError.response) {
        setError('Could not connect to the AI service. Please make sure the Flask backend is running.');
      } else if (requestError.response.status === 400) {
        const backendMessage = (requestError.response.data as { error?: string })?.error;
        setError(backendMessage || 'Please check the cattle details and try again.');
      } else if (requestError.response.status >= 500) {
        setError('The AI service could not generate a recommendation right now. Please try again later.');
      } else {
        setError('Unable to generate the recommendation. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <Bot className="h-6 w-6 mr-2 text-green-600" />
          AI Feed Recommendation
        </h1>
        <p className="text-sm text-gray-500">
          Generate advisory cattle feed suggestions using milk-yield prediction and rule-based nutrition logic.
        </p>
      </div>

      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <div className="flex gap-3">
          <Info className="h-5 w-5 flex-shrink-0 text-blue-500" />
          <p className="text-sm text-blue-800">
            This module is intended for dairy cattle. Basic animal details are auto-filled from Livestock, while milk and lactation details can be adjusted before generating the recommendation.
          </p>
        </div>
      </div>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4">
          <p className="flex items-start gap-2 text-sm text-red-700">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            {error}
          </p>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <form onSubmit={handleSubmit} className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 px-5 py-4">
            <h2 className="text-lg font-semibold text-gray-900">Cattle Details</h2>
            <p className="mt-1 text-sm text-gray-500">Select an animal, then adjust the feeding inputs.</p>
          </div>

          <div className="space-y-5 p-5">
            <div>
              <label className="block text-sm font-medium text-gray-700">Animal</label>
              <select
                value={formData.selectedAnimalId}
                onChange={handleAnimalChange}
                disabled={loadingAnimals}
                className="mt-1 block w-full rounded-md border border-gray-300 bg-white p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500 disabled:bg-gray-50"
              >
                <option value="">
                  {loadingAnimals ? 'Loading dairy cattle...' : 'Select dairy cattle...'}
                </option>
                {animals.map((animal) => (
                  <option key={animal.id} value={animal.id}>
                    {animal.animalName} ({animal.animalId}) - {animal.species}
                  </option>
                ))}
              </select>
              {!loadingAnimals && animals.length === 0 ? (
                <div className="mt-2 space-y-1 text-xs text-amber-700">
                  <p>No dairy cattle records found. Add a Dairy Cattle record in Livestock Management to use this module.</p>
                  <p>The AI feed recommender is not intended for beef cattle, sheep, goats, poultry, or swine.</p>
                </div>
              ) : null}
            </div>

            {selectedAnimal ? (
              <div className="rounded-md border border-green-100 bg-green-50 p-3 text-sm text-green-800">
                Auto-filled from Livestock: {selectedAnimal.animalName}, {selectedAnimal.species}
              </div>
            ) : null}

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">Animal Name</label>
                <input
                  type="text"
                  name="animalName"
                  value={formData.animalName}
                  onChange={handleChange}
                  className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Breed *</label>
                <input
                  type="text"
                  name="breed"
                  value={formData.breed}
                  onChange={handleChange}
                  className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Age (months) *</label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  name="ageMonths"
                  value={formData.ageMonths}
                  onChange={handleChange}
                  className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Weight (kg) *</label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  name="weightKg"
                  value={formData.weightKg}
                  onChange={handleChange}
                  className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500"
                />
              </div>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-sm font-semibold text-gray-900">Feeding Inputs</h3>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Lactation Stage *</label>
                  <select
                    name="lactationStage"
                    value={formData.lactationStage}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded-md border border-gray-300 bg-white p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500"
                  >
                    <option>Early Lactation</option>
                    <option>Mid Lactation</option>
                    <option>Late Lactation</option>
                    <option>Dry</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Health Status</label>
                  <select
                    name="healthStatus"
                    value={formData.healthStatus}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded-md border border-gray-300 bg-white p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500"
                  >
                    <option>Healthy</option>
                    <option>Sick</option>
                    <option>Under Treatment</option>
                    <option>Recovering</option>
                    <option>Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Days in Milk</label>
                  <input type="number" min="0" name="daysInMilk" value={formData.daysInMilk} onChange={handleChange} className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Previous Week Avg Yield (L)</label>
                  <input type="number" min="0" step="0.1" name="previousWeekAvgYield" value={formData.previousWeekAvgYield} onChange={handleChange} className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Body Condition Score</label>
                  <input type="number" min="1" max="5" step="0.1" name="bodyConditionScore" value={formData.bodyConditionScore} onChange={handleChange} className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Ambient Temperature (C)</label>
                  <input type="number" step="0.1" name="ambientTemperatureC" value={formData.ambientTemperatureC} onChange={handleChange} className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Humidity (%)</label>
                  <input type="number" min="0" max="100" step="0.1" name="humidityPercent" value={formData.humidityPercent} onChange={handleChange} className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500" />
                </div>
              </div>
            </div>

            {validationMessage ? (
              <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                {validationMessage}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={submitting || loadingAnimals}
              className="inline-flex w-full items-center justify-center rounded-md border border-transparent bg-green-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-green-700 disabled:bg-green-400"
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating recommendation...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Recommendation
                </>
              )}
            </button>
          </div>
        </form>

        <div className="space-y-6">
          {recommendation ? (
            <>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="rounded-lg border border-green-200 bg-white p-5 shadow-sm md:col-span-1">
                  <p className="text-sm font-medium text-gray-500">Predicted Milk Yield</p>
                  <p className="mt-2 text-3xl font-bold text-green-700">
                    {recommendation.prediction.predictedMilkYieldL} L/day
                  </p>
                  <p className="mt-3 text-xs text-gray-500">Model: {recommendation.prediction.modelUsed}</p>
                  <p className="text-xs text-gray-500">Target: {recommendation.prediction.target}</p>
                </div>

                <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm md:col-span-2">
                  <h2 className="flex items-center text-lg font-semibold text-gray-900">
                    <Wheat className="mr-2 h-5 w-5 text-green-600" />
                    Recommendation
                  </h2>
                  <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                    <Metric label="Total Feed" value={`${recommendation.recommendation.totalFeedKg} kg`} />
                    <Metric label="Roughage" value={`${recommendation.recommendation.roughageKg} kg`} />
                    <Metric label="Concentrate" value={`${recommendation.recommendation.concentrateKg} kg`} />
                    <Metric label="Mineral Mix" value={`${recommendation.recommendation.mineralMixKg} kg`} />
                    <Metric label="Frequency" value={recommendation.recommendation.feedingFrequency} />
                    <Metric label="Confidence" value={recommendation.recommendation.confidenceLevel} />
                  </div>
                  <div className="mt-4 rounded-md bg-blue-50 p-3">
                    <p className="flex items-start gap-2 text-sm text-blue-800">
                      <Droplets className="mt-0.5 h-4 w-4 flex-shrink-0" />
                      {recommendation.recommendation.waterAdvice}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900">Explanation</h2>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-gray-700">
                  {recommendation.recommendation.explanation.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900">Warnings</h2>
                {recommendation.recommendation.warnings.length > 0 ? (
                  <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-amber-800">
                    {recommendation.recommendation.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-sm text-gray-600">No major warnings for this input.</p>
                )}
              </div>

              <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
                <h2 className="text-lg font-semibold text-amber-900">Limitations / Disclaimer</h2>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-amber-800">
                  {recommendation.limitations.map((limitation) => (
                    <li key={limitation}>{limitation}</li>
                  ))}
                  <li>{recommendation.recommendation.disclaimer}</li>
                </ul>
              </div>
            </>
          ) : (
            <div className="flex min-h-[420px] flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50 p-10 text-center">
              <Leaf className="h-14 w-14 text-gray-300" />
              <h2 className="mt-4 text-lg font-semibold text-gray-900">
                {loadingAnimals || animals.length > 0 ? 'Ready for a dairy cattle profile' : 'No dairy cattle records found'}
              </h2>
              {loadingAnimals || animals.length > 0 ? (
                <p className="mt-2 max-w-md text-sm text-gray-500">
                  Select a dairy cattle record, check the feeding inputs, then generate the advisory feed recommendation.
                </p>
              ) : (
                <div className="mt-2 max-w-md space-y-2 text-sm text-gray-500">
                  <p>No dairy cattle records found. Add a Dairy Cattle record in Livestock Management to use this module.</p>
                  <p>The AI feed recommender is not intended for beef cattle, sheep, goats, poultry, or swine.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

interface MetricProps {
  label: string;
  value: string;
}

const Metric: React.FC<MetricProps> = ({ label, value }) => (
  <div className="rounded-md bg-gray-50 p-3">
    <p className="text-xs font-medium uppercase text-gray-500">{label}</p>
    <p className="mt-1 text-sm font-bold text-gray-900">{value}</p>
  </div>
);

export default FeedRecommendation;
