import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { collection, getDocs } from 'firebase/firestore';
import { jsPDF } from 'jspdf';
import { AlertCircle, Bot, Download, Droplets, Leaf, Loader2, Sparkles } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { db } from '../firebase/config';
import { calculateAgeInMonths, getDisplaySpecies, parseDateValue, toText } from '../utils/livestockStatus';
import {
  CandidateApiError,
  predictBangladeshCandidates,
  type BangladeshPredictionResponse,
} from '../api/bangladeshCandidate';
import { FLASK_API_BASE_URL } from '../api/baseUrl';
import CandidateDmiAndThiCards from '../components/ResearchPredictions';
import { BANGLADESH_CANDIDATE_UI_ENABLED } from '../config/featureFlags';
import {
  BANGLADESH_GENETIC_GROUP_OPTIONS,
  buildCandidateRequest,
} from '../features/bangladeshCandidate';
import {
  createFarmerRecommendationPdf,
  DMI_RATION_EXPLANATION,
  FARMER_ADVISORY_DISCLAIMER,
} from '../utils/farmerRecommendationPdf';

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
  geneticGroup: string;
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

type CandidateFieldError = {
  field: 'geneticGroup' | 'ambientTemperatureC' | 'humidityPercent';
  message: string;
};

const CANDIDATE_REQUEST_FORM_FIELDS = new Set([
  'breed',
  'geneticGroup',
  'ageMonths',
  'weightKg',
  'lactationStage',
  'daysInMilk',
  'ambientTemperatureC',
  'humidityPercent',
  'previousWeekAvgYield',
  'bodyConditionScore',
  'healthStatus',
]);

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

const UNKNOWN_GENETIC_GROUP = 'Unknown';

const uniqueText = (values: string[]): string[] =>
  Array.from(new Set(values.map((value) => value.trim()).filter(Boolean)));

const geneticGroupDisplayLabel = (value: string): string => {
  if (value === UNKNOWN_GENETIC_GROUP) return 'Unknown / Not sure';
  return (
    BANGLADESH_GENETIC_GROUP_OPTIONS.find((option) => option.value === value)
      ?.label ?? 'Unavailable'
  );
};

const farmerRuleExplanation = (
  recommendation: FeedRecommendationResponse
): string[] => [
  `The FarmLite nutrition rule engine calculated an advisory ration quantity of ${recommendation.recommendation.totalFeedKg} kg/day.`,
  ...recommendation.recommendation.explanation.filter(
    (item) => !/model supplied an estimated feed quantity/i.test(item)
  ),
];

const candidateCowWarning = (
  response: BangladeshPredictionResponse | null,
  notice: string
): string => {
  const reasons = new Set(response?.fallback_reasons ?? []);
  if (
    reasons.has('ENVIRONMENT_MISSING') ||
    reasons.has('ENVIRONMENT_INVALID') ||
    reasons.has('THI_CATEGORY_UNKNOWN')
  ) {
    return 'Temperature or humidity could not be used for the heat-stress calculation.';
  }
  if (reasons.has('POPULATION_OUT_OF_SCOPE')) {
    return 'The dry-matter intake model does not support this cow’s current production stage.';
  }
  if (/temperature|humidity/i.test(notice)) return notice;
  return '';
};

const dmiScopeMessage = (
  response: BangladeshPredictionResponse | null,
  loading: boolean
): string => {
  if (loading) return 'Dry-matter intake estimate is being calculated.';
  if (
    response?.ml_predictions.dmi_kg_day !== null &&
    response?.ml_predictions.dmi_kg_day !== undefined &&
    Number.isFinite(response.ml_predictions.dmi_kg_day)
  ) {
    if (response.eligibility.dmi.scope === 'LIMITED_SUPPORT') {
      return 'Available with limited validation support for the supplied genetic group.';
    }
    return 'Validated within the current supported model scope.';
  }
  return 'Dry-matter intake estimate is currently unavailable.';
};

const createInitialFormData = (): FeedFormData => ({
  selectedAnimalId: '',
  animalId: '',
  animalName: '',
  breed: '',
  geneticGroup: '',
  ageMonths: '',
  weightKg: '',
  lactationStage: 'Mid Lactation',
  daysInMilk: '0',
  ambientTemperatureC: BANGLADESH_CANDIDATE_UI_ENABLED ? '' : '28',
  humidityPercent: BANGLADESH_CANDIDATE_UI_ENABLED ? '' : '70',
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

const makePdfSafeName = (value: string) => {
  const safeName = value.trim().replace(/[^a-z0-9]+/gi, '_').replace(/^_+|_+$/g, '');
  return safeName || 'Animal';
};

const FeedRecommendation: React.FC = () => {
  const { currentUser } = useAuth();
  const [searchParams] = useSearchParams();
  const [animals, setAnimals] = useState<LivestockRecord[]>([]);
  const [healthRecords, setHealthRecords] = useState<HealthRecordLike[]>([]);
  const [loadingAnimals, setLoadingAnimals] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [pdfError, setPdfError] = useState('');
  const [validationMessage, setValidationMessage] = useState('');
  const [recommendation, setRecommendation] = useState<FeedRecommendationResponse | null>(null);
  const [candidateResponse, setCandidateResponse] =
    useState<BangladeshPredictionResponse | null>(null);
  const [candidateLoading, setCandidateLoading] = useState(false);
  const [candidateError, setCandidateError] = useState('');
  const [candidateNotice, setCandidateNotice] = useState('');
  const [candidateFieldError, setCandidateFieldError] =
    useState<CandidateFieldError | null>(null);
  const [formData, setFormData] = useState<FeedFormData>(createInitialFormData);
  const candidateAbortController = useRef<AbortController | null>(null);
  const candidateRequestSequence = useRef(0);

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
    // Intentional mount/user-change data fetch; fetchPageData sets
    // loading/error state before its network await, the standard
    // fetch-on-mount pattern.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchPageData();
  }, [fetchPageData]);

  useEffect(() => {
    if (!requestedAnimalId || animals.length === 0) return;

    const requestedAnimal = animals.find(
      (animal) => animal.id === requestedAnimalId || animal.animalId === requestedAnimalId
    );
    if (!requestedAnimal) return;

    // Syncs the form's selected animal to the ?id= URL param; guarded so it
    // only fires when the derived selection actually changes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setFormData((previous) => {
      if (previous.selectedAnimalId === requestedAnimal.id) return previous;

      return {
        ...previous,
        selectedAnimalId: requestedAnimal.id,
        animalId: requestedAnimal.animalId,
        animalName: requestedAnimal.animalName,
        breed: requestedAnimal.breed,
        geneticGroup: '',
        ageMonths: requestedAnimal.ageMonths,
        weightKg: requestedAnimal.weightKg,
        healthStatus: deriveLatestHealthStatus(healthRecords, requestedAnimal),
      };
    });
  }, [animals, healthRecords, requestedAnimalId]);

  useEffect(
    () => () => {
      candidateAbortController.current?.abort();
    },
    []
  );

  const selectedAnimal = useMemo(
    () => animals.find((animal) => animal.id === formData.selectedAnimalId) ?? null,
    [animals, formData.selectedAnimalId]
  );

  const handleAnimalChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const animal = animals.find((item) => item.id === event.target.value);
    setRecommendation(null);
    setCandidateResponse(null);
    setCandidateError('');
    setCandidateNotice('');
    setCandidateFieldError(null);
    candidateAbortController.current?.abort();
    candidateRequestSequence.current += 1;
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
      geneticGroup: '',
      ageMonths: animal.ageMonths,
      weightKg: animal.weightKg,
      healthStatus: deriveLatestHealthStatus(healthRecords, animal),
    }));
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = event.target;
    setFormData((previous) => ({ ...previous, [name]: value }));
    if (
      BANGLADESH_CANDIDATE_UI_ENABLED &&
      CANDIDATE_REQUEST_FORM_FIELDS.has(name)
    ) {
      candidateAbortController.current?.abort();
      candidateRequestSequence.current += 1;
      setCandidateLoading(false);
      setCandidateFieldError(null);
      setCandidateNotice('');
      setCandidateError('');
      setCandidateResponse(null);
    }
    setValidationMessage('');
  };

  const startCandidateRequest = () => {
    candidateAbortController.current?.abort();
    candidateRequestSequence.current += 1;
    const decision = buildCandidateRequest(formData);
    setCandidateResponse(null);
    setCandidateError('');
    setCandidateNotice('');
    setCandidateFieldError(null);

    if (!decision.request) {
      setCandidateLoading(false);
      setCandidateNotice(decision.message);
      if (decision.field) {
        setCandidateFieldError({
          field: decision.field,
          message: decision.message,
        });
      }
      return;
    }

    setCandidateNotice(decision.message);
    const controller = new AbortController();
    candidateAbortController.current = controller;
    const requestSequence = candidateRequestSequence.current;
    setCandidateLoading(true);

    void predictBangladeshCandidates(decision.request, controller.signal)
      .then((response) => {
        if (candidateRequestSequence.current !== requestSequence) return;
        setCandidateResponse(response);
      })
      .catch((requestError: unknown) => {
        if (candidateRequestSequence.current !== requestSequence) return;
        if (
          requestError instanceof CandidateApiError &&
          requestError.code === 'REQUEST_CANCELLED'
        ) {
          return;
        }
        setCandidateError(
          'Dry-matter intake estimate is currently unavailable.'
        );
      })
      .finally(() => {
        if (candidateRequestSequence.current === requestSequence) {
          setCandidateLoading(false);
        }
      });
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
    setPdfError('');
    setValidationMessage('');
    setRecommendation(null);

    if (BANGLADESH_CANDIDATE_UI_ENABLED) {
      startCandidateRequest();
    }

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
        `${FLASK_API_BASE_URL}/api/ai/feed-recommendation`,
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

  const handleDownloadPdf = () => {
    if (!recommendation) return;

    try {
      setPdfError('');

      const generatedAt = new Date();
      const reportDate = generatedAt.toISOString().slice(0, 10);
      const animalName = formData.animalName || recommendation.animalName || selectedAnimal?.animalName || 'Animal';
      const animalTag = formData.animalId || recommendation.animalId || selectedAnimal?.animalId || 'N/A';

      if (BANGLADESH_CANDIDATE_UI_ENABLED) {
        const warnings = uniqueText([
          ...recommendation.recommendation.warnings,
          candidateCowWarning(candidateResponse, candidateNotice),
        ]);
        const report = createFarmerRecommendationPdf({
          generatedAt,
          animal: {
            name: animalName,
            tag: animalTag,
            breed: formData.breed,
            ageMonths: formData.ageMonths,
            weightKg: formData.weightKg,
            lactationStage: formData.lactationStage,
            healthStatus: formData.healthStatus,
            daysInMilk: formData.daysInMilk,
            previousWeekAvgYieldL: formData.previousWeekAvgYield,
            bodyConditionScore: formData.bodyConditionScore,
            ambientTemperatureC: formData.ambientTemperatureC,
            humidityPercent: formData.humidityPercent,
            geneticGroupLabel: geneticGroupDisplayLabel(
              formData.geneticGroup
            ),
          },
          expectedMilkYieldLDay:
            recommendation.prediction.predictedMilkYieldL,
          predictedDmiKgDay:
            candidateResponse?.ml_predictions.dmi_kg_day ?? null,
          calculatedThi:
            candidateResponse?.environment.calculated_thi ?? null,
          thiCategory: candidateResponse?.environment.thi_category ?? null,
          ration: {
            totalKgDay: recommendation.recommendation.totalFeedKg,
            roughageKgDay: recommendation.recommendation.roughageKg,
            concentrateKgDay:
              recommendation.recommendation.concentrateKg,
            mineralMixKgDay:
              recommendation.recommendation.mineralMixKg,
            waterAdvice: recommendation.recommendation.waterAdvice,
            feedingFrequency:
              recommendation.recommendation.feedingFrequency,
            confidenceLevel:
              recommendation.recommendation.confidenceLevel,
          },
          ruleExplanation: farmerRuleExplanation(recommendation),
          cowAndRationWarnings: warnings,
          dmiScopeMessage: dmiScopeMessage(
            candidateResponse,
            candidateLoading
          ),
          limitations: recommendation.limitations,
        });
        report.save(
          `FarmLite_Decision_Support_Report_${makePdfSafeName(animalName)}_${reportDate}.pdf`
        );
        return;
      }

      const report = new jsPDF();
      const margin = 16;
      const maxTextWidth = 178;
      const pageHeight = report.internal.pageSize.getHeight();
      let yPosition = 18;

      const ensureSpace = (requiredHeight: number) => {
        if (yPosition + requiredHeight <= pageHeight - margin) return;
        report.addPage();
        yPosition = 18;
      };

      const addWrappedText = (
        text: string,
        options: { fontSize?: number; fontStyle?: 'normal' | 'bold'; indent?: number } = {}
      ) => {
        const fontSize = options.fontSize ?? 10;
        const indent = options.indent ?? 0;
        report.setFont('helvetica', options.fontStyle ?? 'normal');
        report.setFontSize(fontSize);

        const lineHeight = fontSize * 0.42;
        const lines = report.splitTextToSize(text, maxTextWidth - indent);
        ensureSpace(lines.length * lineHeight + 2);
        report.text(lines, margin + indent, yPosition);
        yPosition += lines.length * lineHeight + 2;
      };

      const addSectionTitle = (title: string) => {
        yPosition += 3;
        ensureSpace(10);
        addWrappedText(title, { fontSize: 13, fontStyle: 'bold' });
      };

      const addRow = (label: string, value: string | number | null | undefined) => {
        addWrappedText(`${label}: ${value ?? 'N/A'}`);
      };

      const addBullet = (text: string) => {
        addWrappedText(`- ${text}`, { indent: 4 });
      };

      report.setFont('helvetica', 'bold');
      report.setFontSize(17);
      report.text('FarmLite AI Feed Recommendation Report', margin, yPosition);
      yPosition += 10;

      addSectionTitle('Report Metadata');
      addRow('Generated date and time', generatedAt.toLocaleString());
      addRow('Animal name', animalName);
      addRow('Animal ID/tag', animalTag);

      addSectionTitle('Selected Animal Details');
      addRow('Breed', formData.breed);
      addRow('Age in months', formData.ageMonths);
      addRow('Weight in kg', formData.weightKg);
      addRow('Health status', formData.healthStatus);
      addRow('Lactation stage', formData.lactationStage);
      addRow('Days in milk', formData.daysInMilk);
      addRow('Previous week average yield', `${formData.previousWeekAvgYield} L`);
      addRow('Body condition score', formData.bodyConditionScore);
      addRow('Ambient temperature', `${formData.ambientTemperatureC} C`);
      addRow('Humidity', `${formData.humidityPercent}%`);

      addSectionTitle('Prediction');
      addRow('Predicted milk yield', `${recommendation.prediction.predictedMilkYieldL} L/day`);
      addRow('Model used', recommendation.prediction.modelUsed);
      addRow('Target', recommendation.prediction.target);
      addRow('Value source', 'Existing FarmLite prediction flow');

      addSectionTitle('Feed Recommendation');
      addRow('Value source', 'Existing FarmLite rule engine');
      addRow('Total feed', `${recommendation.recommendation.totalFeedKg} kg`);
      addRow('Roughage', `${recommendation.recommendation.roughageKg} kg`);
      addRow('Concentrate', `${recommendation.recommendation.concentrateKg} kg`);
      addRow('Mineral mix', `${recommendation.recommendation.mineralMixKg} kg`);
      addRow('Water advice', recommendation.recommendation.waterAdvice);
      addRow('Feeding frequency', recommendation.recommendation.feedingFrequency);
      addRow('Confidence level', recommendation.recommendation.confidenceLevel);

      addSectionTitle('Explanation');
      recommendation.recommendation.explanation.forEach(addBullet);

      addSectionTitle('Warnings');
      if (recommendation.recommendation.warnings.length > 0) {
        recommendation.recommendation.warnings.forEach(addBullet);
      } else {
        addWrappedText('No major warnings for this input.');
      }

      addSectionTitle('Limitations / Disclaimer');
      recommendation.limitations.forEach(addBullet);
      addBullet(recommendation.recommendation.disclaimer);

      addSectionTitle('Footer');
      addWrappedText(
        'Generated by FarmLite. This recommendation is advisory only and should not replace guidance from a veterinarian or qualified animal nutritionist.'
      );

      report.save(`FarmLite_AI_Feed_Report_${makePdfSafeName(animalName)}_${reportDate}.pdf`);
    } catch (downloadError) {
      console.error('Could not generate AI feed PDF report:', downloadError);
      setPdfError('Could not generate PDF report. Please try again.');
    }
  };

  const displayedRuleExplanation = recommendation
    ? farmerRuleExplanation(recommendation)
    : [];
  const cowAndRationWarnings = recommendation
    ? uniqueText([
        ...recommendation.recommendation.warnings,
        candidateCowWarning(candidateResponse, candidateNotice),
      ])
    : [];
  const recommendationAnimalName =
    formData.animalName ||
    recommendation?.animalName ||
    selectedAnimal?.animalName ||
    'selected cow';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 flex items-center">
        <Bot className="h-6 w-6 mr-2 text-green-600" />
        FarmLite Feed Recommendation
      </h1>

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
              <label htmlFor="selected-animal" className="block text-sm font-medium text-gray-700">Animal</label>
              <select
                id="selected-animal"
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
              <div className="rounded-lg border border-[#dda15e]/70 bg-[#fefae0] p-4">
                <h3 className="text-sm font-semibold text-[#283618]">
                  Selected Animal
                </h3>
                <dl className="mt-3 grid grid-cols-1 gap-x-4 gap-y-2 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="text-xs font-medium uppercase text-gray-500">Name</dt>
                    <dd className="font-semibold text-gray-900">{formData.animalName || 'Unavailable'}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase text-gray-500">ID / Tag</dt>
                    <dd className="font-semibold text-gray-900">{formData.animalId || 'Unavailable'}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase text-gray-500">Breed</dt>
                    <dd className="font-semibold text-gray-900">{formData.breed || 'Unavailable'}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase text-gray-500">Age</dt>
                    <dd className="font-semibold text-gray-900">{formData.ageMonths ? `${formData.ageMonths} months` : 'Unavailable'}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase text-gray-500">Weight</dt>
                    <dd className="font-semibold text-gray-900">{formData.weightKg ? `${formData.weightKg} kg` : 'Unavailable'}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase text-gray-500">Record type</dt>
                    <dd className="font-semibold text-gray-900">{selectedAnimal.species}</dd>
                  </div>
                </dl>
              </div>
            ) : null}

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
                {BANGLADESH_CANDIDATE_UI_ENABLED ? (
                  <div>
                    <label
                      htmlFor="genetic-group"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Genetic Group
                    </label>
                    <select
                      id="genetic-group"
                      name="geneticGroup"
                      value={formData.geneticGroup}
                      onChange={handleChange}
                      aria-describedby={
                        candidateFieldError?.field === 'geneticGroup'
                          ? 'genetic-group-help genetic-group-error'
                          : 'genetic-group-help'
                      }
                      aria-invalid={
                        candidateFieldError?.field === 'geneticGroup'
                      }
                      className="mt-1 block w-full rounded-md border border-gray-300 bg-white p-2 text-sm shadow-sm focus:border-[#606c38] focus:ring-[#606c38]"
                    >
                      <option value="">Select genetic group</option>
                      {BANGLADESH_GENETIC_GROUP_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                      <option value={UNKNOWN_GENETIC_GROUP}>
                        Unknown / Not sure
                      </option>
                    </select>
                    <p id="genetic-group-help" className="mt-2 text-xs text-gray-600">
                      Select the cow’s verified genetic group for the dry-matter intake model.
                    </p>
                    {candidateFieldError?.field === 'geneticGroup' ? (
                      <p
                        id="genetic-group-error"
                        role="alert"
                        className="mt-2 text-xs font-medium text-red-700"
                      >
                        {candidateFieldError.message}
                      </p>
                    ) : null}
                  </div>
                ) : null}
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
                  <label htmlFor="ambient-temperature-c" className="block text-sm font-medium text-gray-700">Ambient Temperature (C)</label>
                  <input id="ambient-temperature-c" type="number" step="0.1" name="ambientTemperatureC" value={formData.ambientTemperatureC} onChange={handleChange} aria-describedby={candidateFieldError?.field === 'ambientTemperatureC' ? 'ambient-temperature-error' : undefined} aria-invalid={candidateFieldError?.field === 'ambientTemperatureC'} className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500" />
                  {candidateFieldError?.field === 'ambientTemperatureC' ? (
                    <p id="ambient-temperature-error" role="alert" className="mt-2 text-xs font-medium text-red-700">
                      {candidateFieldError.message}
                    </p>
                  ) : null}
                </div>
                <div>
                  <label htmlFor="humidity-percent" className="block text-sm font-medium text-gray-700">Humidity (%)</label>
                  <input id="humidity-percent" type="number" min="0" max="100" step="0.1" name="humidityPercent" value={formData.humidityPercent} onChange={handleChange} aria-describedby={candidateFieldError?.field === 'humidityPercent' ? 'humidity-error' : undefined} aria-invalid={candidateFieldError?.field === 'humidityPercent'} className="mt-1 block w-full rounded-md border border-gray-300 p-2 text-sm shadow-sm focus:border-green-500 focus:ring-green-500" />
                  {candidateFieldError?.field === 'humidityPercent' ? (
                    <p id="humidity-error" role="alert" className="mt-2 text-xs font-medium text-red-700">
                      {candidateFieldError.message}
                    </p>
                  ) : null}
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
              className="inline-flex w-full items-center justify-center rounded-lg border border-transparent bg-[#606c38] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#4f5a2f] disabled:bg-[#606c38]/60"
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
            <section
              aria-labelledby="unified-recommendation-title"
              className="min-w-0 space-y-5 rounded-xl border border-[#dda15e]/70 bg-white p-5 shadow-sm"
            >
              <div className="flex flex-col gap-3 border-b border-[#dda15e]/40 pb-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2
                    id="unified-recommendation-title"
                    className="text-xl font-bold text-[#283618]"
                  >
                    FarmLite Recommendation for {recommendationAnimalName}
                  </h2>
                  <p className="mt-1 text-sm text-gray-600">
                    One combined view of production, intake, heat stress and
                    advisory feeding guidance.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleDownloadPdf}
                  className="inline-flex w-full items-center justify-center rounded-lg border border-[#606c38] bg-white px-4 py-2 text-sm font-medium text-[#606c38] shadow-sm hover:bg-[#fefae0] sm:w-auto"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download PDF Report
                </button>
              </div>

              {pdfError ? (
                <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {pdfError}
                </div>
              ) : null}

              <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2">
                <article className="min-w-0 rounded-xl border border-[#dda15e]/70 bg-white p-5 shadow-sm">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-[#283618]">
                    Expected Milk Yield
                  </h3>
                  <p className="mt-3 break-words text-3xl font-bold text-[#283618]">
                    {recommendation.prediction.predictedMilkYieldL} L/day
                  </p>
                  <p className="mt-2 text-sm text-gray-700">
                    Estimated using the selected cow’s production and
                    management inputs.
                  </p>
                  <p className="mt-3 text-xs font-medium text-[#606c38]">
                    Source: FarmLite milk prediction model
                  </p>
                </article>

                {BANGLADESH_CANDIDATE_UI_ENABLED ? (
                  <CandidateDmiAndThiCards
                    response={candidateResponse}
                    loading={candidateLoading}
                    error={candidateError}
                    notice={candidateNotice}
                  />
                ) : null}

                <article className="min-w-0 rounded-xl border border-[#dda15e]/70 bg-[#fefae0] p-5 shadow-sm">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-[#283618]">
                    Advisory Daily Ration
                  </h3>
                  <p className="mt-3 break-words text-3xl font-bold text-[#283618]">
                    {recommendation.recommendation.totalFeedKg} kg/day
                  </p>
                  <p className="mt-2 text-xs font-medium text-[#606c38]">
                    Source: FarmLite nutrition rule engine
                  </p>
                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <Metric label="Roughage" value={`${recommendation.recommendation.roughageKg} kg/day`} />
                    <Metric label="Concentrate" value={`${recommendation.recommendation.concentrateKg} kg/day`} />
                    <Metric label="Mineral mix" value={`${recommendation.recommendation.mineralMixKg} kg/day`} />
                    <Metric label="Frequency" value={recommendation.recommendation.feedingFrequency} />
                    <Metric label="Confidence" value={recommendation.recommendation.confidenceLevel} />
                  </div>
                  <div className="mt-4 rounded-md border border-[#dda15e]/50 bg-white p-3">
                    <p className="flex items-start gap-2 text-sm text-[#283618]">
                      <Droplets className="mt-0.5 h-4 w-4 flex-shrink-0" />
                      {recommendation.recommendation.waterAdvice}
                    </p>
                  </div>
                </article>
              </div>

              {BANGLADESH_CANDIDATE_UI_ENABLED ? (
                <div className="rounded-lg border border-[#606c38]/30 bg-[#fefae0] p-4">
                  <h3 className="font-semibold text-[#283618]">
                    Dry-matter intake and ration quantity
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-gray-700">
                    {DMI_RATION_EXPLANATION}
                  </p>
                </div>
              ) : null}

              <div className="rounded-lg border border-gray-200 bg-white p-4">
                <h3 className="font-semibold text-[#283618]">
                  How the advisory ration was produced
                </h3>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-gray-700">
                  {displayedRuleExplanation.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="rounded-lg border border-[#dda15e]/60 bg-white p-4">
                <h3 className="font-semibold text-[#283618]">
                  Cow and Ration Warnings
                </h3>
                {cowAndRationWarnings.length > 0 ? (
                  <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-amber-800">
                    {cowAndRationWarnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-sm text-gray-700">
                    No cow or ration warnings were identified for the supplied inputs.
                  </p>
                )}
              </div>

              {BANGLADESH_CANDIDATE_UI_ENABLED ? (
                <div className="rounded-lg border border-[#606c38]/40 bg-[#fefae0] p-4">
                  <h3 className="font-semibold text-[#283618]">
                    AI Model Scope
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-gray-700">
                    AI estimates are decision-support values and are not
                    guaranteed outcomes. The DMI model was developed using a
                    collected research dataset and requires wider multi-farm
                    validation.
                  </p>
                  <p className="mt-2 text-sm font-medium text-[#606c38]">
                    {dmiScopeMessage(candidateResponse, candidateLoading)}
                  </p>
                </div>
              ) : null}

              <div className="rounded-lg border border-[#bc6c25]/40 bg-[#fefae0] p-4">
                <p className="text-sm font-semibold text-[#283618]">
                  AI-assisted decision support
                </p>
                <p className="mt-2 text-sm leading-6 text-gray-700">
                  {FARMER_ADVISORY_DISCLAIMER}
                </p>
              </div>
            </section>
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
