import type {
  BangladeshGeneticGroup,
  BangladeshPredictionRequest,
  BangladeshPredictionResponse,
  CandidateWarning,
} from '../api/bangladeshCandidate';

export const BANGLADESH_GENETIC_GROUP_OPTIONS: ReadonlyArray<{
  value: BangladeshGeneticGroup;
  label: string;
}> = [
  { value: 'Local', label: 'Local cattle' },
  { value: 'HF50', label: '50% Holstein Friesian cross' },
  { value: 'HF62.5', label: '62.5% Holstein Friesian cross' },
  { value: 'HF75', label: '75% Holstein Friesian cross' },
  { value: 'HF87.5', label: '87.5% Holstein Friesian cross' },
];

const ALLOWED_GENETIC_GROUPS = new Set<BangladeshGeneticGroup>(
  BANGLADESH_GENETIC_GROUP_OPTIONS.map((option) => option.value)
);

export interface CandidateFormValues {
  breed: string;
  geneticGroup: string;
  ageMonths: string;
  weightKg: string;
  lactationStage: string;
  daysInMilk: string;
  previousWeekAvgYield: string;
  bodyConditionScore: string;
  ambientTemperatureC: string;
  humidityPercent: string;
  healthStatus: string;
}

export interface CandidateRequestDecision {
  request: BangladeshPredictionRequest | null;
  field: 'geneticGroup' | 'ambientTemperatureC' | 'humidityPercent' | null;
  message: string;
}

const optionalFiniteNumber = (value: string): number | undefined => {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

export const buildCandidateRequest = (
  values: CandidateFormValues
): CandidateRequestDecision => {
  const hasKnownGeneticGroup = ALLOWED_GENETIC_GROUPS.has(
    values.geneticGroup as BangladeshGeneticGroup
  );
  const isExplicitlyUnknown = values.geneticGroup === 'Unknown';
  const isUnselectedGeneticGroup = !values.geneticGroup.trim();
  const lacksVerifiedGeneticGroup =
    isExplicitlyUnknown || isUnselectedGeneticGroup;
  if (!hasKnownGeneticGroup && !lacksVerifiedGeneticGroup) {
    return {
      request: null,
      field: 'geneticGroup',
      message:
        'Select a verified genetic group or choose Unknown / Not sure. The normal FarmLite recommendation can still continue.',
    };
  }

  if (!values.ambientTemperatureC.trim()) {
    return {
      request: null,
      field: 'ambientTemperatureC',
      message:
        'Measured ambient temperature is required for the dry-matter intake estimate.',
    };
  }
  const temperature = Number(values.ambientTemperatureC);
  if (!Number.isFinite(temperature)) {
    return {
      request: null,
      field: 'ambientTemperatureC',
      message: 'Ambient temperature must be a numeric Celsius value.',
    };
  }

  if (!values.humidityPercent.trim()) {
    return {
      request: null,
      field: 'humidityPercent',
      message: 'Measured humidity is required for the dry-matter intake estimate.',
    };
  }
  const humidity = Number(values.humidityPercent);
  if (!Number.isFinite(humidity) || humidity < 0 || humidity > 100) {
    return {
      request: null,
      field: 'humidityPercent',
      message:
        'Humidity for the dry-matter intake estimate must be from 0 to 100%.',
    };
  }

  const ageMonths = Number(values.ageMonths);
  const weightKg = Number(values.weightKg);
  const request: BangladeshPredictionRequest = {
    breed: values.breed.trim(),
    age_months: ageMonths,
    weight_kg: weightKg,
    lactation_stage: values.lactationStage,
    ambient_temperature_c: temperature,
    humidity_percent: humidity,
  };
  if (hasKnownGeneticGroup) {
    request.genetic_group = values.geneticGroup as BangladeshGeneticGroup;
  }

  const daysInMilk = optionalFiniteNumber(values.daysInMilk);
  if (
    daysInMilk !== undefined &&
    Number.isInteger(daysInMilk) &&
    daysInMilk >= 0
  ) {
    request.days_in_milk = daysInMilk;
  }
  const previousYield = optionalFiniteNumber(values.previousWeekAvgYield);
  if (previousYield !== undefined && previousYield >= 0) {
    request.previous_week_avg_yield_l = previousYield;
  }
  const conditionScore = optionalFiniteNumber(values.bodyConditionScore);
  if (
    conditionScore !== undefined &&
    conditionScore >= 1 &&
    conditionScore <= 5
  ) {
    request.body_condition_score = conditionScore;
  }
  if (values.healthStatus.trim()) {
    request.health_status = values.healthStatus.trim();
  }

  return {
    request,
    field: null,
    message: lacksVerifiedGeneticGroup
      ? 'A verified genetic group is required to generate the dry-matter intake estimate.'
      : '',
  };
};

export const formatCandidateNumber = (
  value: number | null,
  maximumFractionDigits = 2
): string => {
  if (value === null || !Number.isFinite(value)) return 'Unavailable';
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits,
  }).format(value);
};

export const candidateSourceLabel = (source: string | null): string => {
  if (source === 'BANGLADESH_DMI_CANDIDATE_V1') {
    return 'Collected-data DMI model';
  }
  if (source === 'BANGLADESH_MILK_CANDIDATE_V1') {
    return 'Research-data candidate model';
  }
  return 'Unavailable';
};

export const candidateStatusMessage = (
  response: BangladeshPredictionResponse
): string => {
  if (response.prediction_status === 'ELIGIBLE') {
    return 'Dry-matter intake is available for the supplied inputs.';
  }
  if (response.prediction_status === 'PARTIAL') {
    return 'Only part of the dry-matter intake and heat-stress result is available. No unavailable value was replaced.';
  }

  const reasons = new Set(
    [
      ...response.fallback_reasons,
      response.eligibility.dmi.fallback_reason,
      response.eligibility.milk.fallback_reason,
    ].filter((reason): reason is string => Boolean(reason))
  );
  if (response.prediction_status === 'DISABLED' || reasons.has('FEATURE_DISABLED')) {
    return 'Dry-matter intake estimate is currently unavailable. The existing FarmLite recommendation remains available.';
  }
  if (
    reasons.has('GENETIC_GROUP_MISSING') ||
    reasons.has('GENETIC_GROUP_UNKNOWN')
  ) {
    return 'The dry-matter intake estimate needs an exact verified genetic group. Breed was not used as a substitute.';
  }
  if (
    reasons.has('ENVIRONMENT_MISSING') ||
    reasons.has('ENVIRONMENT_INVALID') ||
    reasons.has('THI_CATEGORY_UNKNOWN')
  ) {
    return 'The dry-matter intake estimate is unavailable because the measured temperature or humidity could not produce a supported heat-stress category.';
  }
  if (reasons.has('POPULATION_OUT_OF_SCOPE')) {
    return 'This animal is outside the currently supported dry-matter intake model scope.';
  }
  if (
    reasons.has('ARTIFACT_UNAVAILABLE') ||
    reasons.has('ARTIFACT_HASH_MISMATCH') ||
    reasons.has('ARTIFACT_METADATA_INVALID') ||
    reasons.has('ARTIFACT_INCOMPATIBLE') ||
    reasons.has('MODEL_ERROR')
  ) {
    return 'The dry-matter intake estimate is temporarily unavailable and was not replaced by another model.';
  }
  return 'Dry-matter intake estimate is currently unavailable.';
};

const catalogWarning = (
  code: string,
  message: string,
  severity: CandidateWarning['severity'] = 'WARNING'
): CandidateWarning => ({ code, message, severity });

const warningPriority = [
  'ARTIFACT_HASH_MISMATCH',
  'ARTIFACT_UNAVAILABLE',
  'MODEL_ERROR',
  'PREDICTION_OUT_OF_SCOPE',
  'BD_LOCAL_LIMITED',
  'BD_DMI_DRY_MATTER',
  'BD_RESEARCH_SCOPE',
  'BD_CANDIDATE_ONLY',
  'BD_EXTERNAL_VALIDATION_MISSING',
  'ADVISORY_ONLY',
];

export const candidateWarnings = (
  response: BangladeshPredictionResponse
): CandidateWarning[] => {
  const hasPrediction =
    response.ml_predictions.dmi_kg_day !== null ||
    response.ml_predictions.milk_yield_l_day !== null;
  const catalogWarnings: CandidateWarning[] = [];

  if (hasPrediction) {
    catalogWarnings.push(
      catalogWarning(
        'BD_RESEARCH_SCOPE',
        'Prediction based on a collected research dataset from 50 lactating cows.'
      ),
      catalogWarning(
        'BD_TWO_FEATURE_MODEL',
        'This prediction uses genetic group and heat-stress category; it does not model individual ration, body weight, lactation stage, or prior yield.',
        'INFORMATION'
      ),
      catalogWarning(
        'BD_CANDIDATE_ONLY',
        'This model remains candidate-only and is not approved for production, commercial, or veterinary use.'
      ),
      catalogWarning(
        'BD_RULE_OWNERSHIP',
        'Feed composition and advisory quantities are generated by FarmLite nutrition rules, not by the DMI model.',
        'INFORMATION'
      ),
      catalogWarning(
        'BD_NO_RATION_LABELS',
        'The study did not provide expert feed types, ration ingredients, roughage, concentrate, mineral, or water recommendation labels.'
      ),
      catalogWarning(
        'BD_EXTERNAL_VALIDATION_MISSING',
        'This candidate has not been validated on an independent farm or FarmLite population.'
      ),
      catalogWarning(
        'ADVISORY_ONLY',
        'This is decision support and not veterinary or qualified animal-nutrition advice.'
      )
    );
  }

  if (response.ml_predictions.dmi_kg_day !== null) {
    catalogWarnings.push(
      catalogWarning(
        'BD_DMI_DRY_MATTER',
        'This output estimates dry-matter intake in kg per cow per day, not total fresh-feed weight.'
      )
    );
  }
  if (response.ml_predictions.milk_yield_l_day !== null) {
    catalogWarnings.push(
      catalogWarning(
        'BD_MILK_DAILY',
        'This output estimates milk yield in litres per cow per day for the study target.',
        'INFORMATION'
      )
    );
  }
  if (
    response.eligibility.dmi.scope === 'LIMITED_SUPPORT' ||
    response.eligibility.milk.scope === 'LIMITED_SUPPORT'
  ) {
    catalogWarnings.push(
      catalogWarning(
        'BD_LOCAL_LIMITED',
        'The Local category was used during development but had no cow in the locked final holdout; support is limited.'
      )
    );
  }

  const seenCodes = new Set<string>();
  const uniqueWarnings = [...response.warnings, ...catalogWarnings].filter(
    (warning) => {
      if (seenCodes.has(warning.code)) return false;
      seenCodes.add(warning.code);
      return true;
    }
  );
  const priority = new Map(
    warningPriority.map((code, index) => [code, index])
  );
  return uniqueWarnings
    .map((warning, index) => ({ warning, index }))
    .sort(
      (left, right) =>
        (priority.get(left.warning.code) ?? warningPriority.length) -
          (priority.get(right.warning.code) ?? warningPriority.length) ||
        left.index - right.index
    )
    .map(({ warning }) => warning);
};
