import axios from 'axios';
import { FLASK_API_BASE_URL } from './baseUrl.ts';

export type BangladeshGeneticGroup =
  | 'Local'
  | 'HF50'
  | 'HF62.5'
  | 'HF75'
  | 'HF87.5';

export interface BangladeshPredictionRequest {
  breed: string;
  genetic_group?: BangladeshGeneticGroup;
  age_months: number;
  weight_kg: number;
  lactation_stage: string;
  days_in_milk?: number;
  previous_week_avg_yield_l?: number;
  body_condition_score?: number;
  ambient_temperature_c: number;
  humidity_percent: number;
  health_status?: string;
}

export interface CandidateEligibility {
  status: string;
  scope: 'IN_SCOPE' | 'LIMITED_SUPPORT' | 'OUT_OF_SCOPE' | 'UNRESOLVED';
  fallback_reason: string | null;
}

export interface CandidateWarning {
  code: string;
  message: string;
  severity: string;
}

export interface CandidateModelProvenance {
  source: string;
  model_name: string;
  artifact_status: string;
  artifact_sha256: string;
  metadata_sha256: string;
  contract_version: string | null;
  feature_order: string[];
  target: string;
  unit: string;
  dataset_doi: string;
  dataset_licence: string | null;
}

export interface BangladeshPredictionResponse {
  schema_version: string;
  prediction_status:
    | 'DISABLED'
    | 'ELIGIBLE'
    | 'FALLBACK_REQUIRED'
    | 'PARTIAL'
    | 'UNAVAILABLE';
  eligibility: {
    dmi: CandidateEligibility;
    milk: CandidateEligibility;
  };
  environment: {
    calculated_thi: number | null;
    display_thi: number | null;
    thi_category: 'T0' | 'T1' | 'T2' | null;
    mapping_version: string | null;
    verification_status: string | null;
    source: 'SERVER_CALCULATED' | 'UNAVAILABLE';
  };
  ml_predictions: {
    dmi_kg_day: number | null;
    milk_yield_l_day: number | null;
  };
  model_sources: {
    dmi: string | null;
    milk: string | null;
  };
  model_provenance?: {
    dmi: CandidateModelProvenance | null;
    milk: CandidateModelProvenance | null;
  };
  rule_recommendation: {
    feed_category: null;
    roughage_kg_day: null;
    concentrate_kg_day: null;
    mineral_mix: null;
    water_advice: null;
  };
  prediction_units?: {
    dmi_kg_day: string;
    milk_yield_l_day: string;
  };
  value_sources?: Record<string, string>;
  warnings: CandidateWarning[];
  limitations: string[];
  fallback_reasons: string[];
}

interface CandidateErrorBody {
  schema_version?: string;
  prediction_status?: string;
  error_code?: string;
  message?: string;
  field_errors?: Record<string, string>;
}

export class CandidateApiError extends Error {
  readonly status: number | null;
  readonly code: string;
  readonly fieldErrors: Record<string, string>;

  constructor(
    message: string,
    options: {
      status?: number | null;
      code?: string;
      fieldErrors?: Record<string, string>;
    } = {}
  ) {
    super(message);
    this.name = 'CandidateApiError';
    this.status = options.status ?? null;
    this.code = options.code ?? 'CANDIDATE_REQUEST_FAILED';
    this.fieldErrors = options.fieldErrors ?? {};
  }
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const isNullableFiniteNumber = (value: unknown): value is number | null =>
  value === null || (typeof value === 'number' && Number.isFinite(value));

const isEligibility = (value: unknown): value is CandidateEligibility => {
  if (!isRecord(value)) return false;
  return (
    typeof value.status === 'string' &&
    ['IN_SCOPE', 'LIMITED_SUPPORT', 'OUT_OF_SCOPE', 'UNRESOLVED'].includes(
      String(value.scope)
    ) &&
    (value.fallback_reason === null ||
      typeof value.fallback_reason === 'string')
  );
};

const isWarning = (value: unknown): value is CandidateWarning =>
  isRecord(value) &&
  typeof value.code === 'string' &&
  typeof value.message === 'string' &&
  typeof value.severity === 'string';

export const isBangladeshPredictionResponse = (
  value: unknown
): value is BangladeshPredictionResponse => {
  if (!isRecord(value)) return false;
  if (
    typeof value.schema_version !== 'string' ||
    ![
      'DISABLED',
      'ELIGIBLE',
      'FALLBACK_REQUIRED',
      'PARTIAL',
      'UNAVAILABLE',
    ].includes(String(value.prediction_status))
  ) {
    return false;
  }

  const eligibility = value.eligibility;
  const environment = value.environment;
  const predictions = value.ml_predictions;
  const sources = value.model_sources;
  const rules = value.rule_recommendation;
  if (
    !isRecord(eligibility) ||
    !isEligibility(eligibility.dmi) ||
    !isEligibility(eligibility.milk) ||
    !isRecord(environment) ||
    !isRecord(predictions) ||
    !isRecord(sources) ||
    !isRecord(rules)
  ) {
    return false;
  }

  const validThiCategory =
    environment.thi_category === null ||
    ['T0', 'T1', 'T2'].includes(String(environment.thi_category));
  const validEnvironment =
    isNullableFiniteNumber(environment.calculated_thi) &&
    isNullableFiniteNumber(environment.display_thi) &&
    validThiCategory &&
    (environment.mapping_version === null ||
      typeof environment.mapping_version === 'string') &&
    (environment.verification_status === null ||
      typeof environment.verification_status === 'string') &&
    ['SERVER_CALCULATED', 'UNAVAILABLE'].includes(
      String(environment.source)
    );
  const validPredictions =
    isNullableFiniteNumber(predictions.dmi_kg_day) &&
    isNullableFiniteNumber(predictions.milk_yield_l_day) &&
    (predictions.dmi_kg_day === null || predictions.dmi_kg_day >= 0) &&
    (predictions.milk_yield_l_day === null ||
      predictions.milk_yield_l_day >= 0);
  const validSources =
    (sources.dmi === null || typeof sources.dmi === 'string') &&
    (sources.milk === null || typeof sources.milk === 'string');
  const validRules =
    rules.feed_category === null &&
    rules.roughage_kg_day === null &&
    rules.concentrate_kg_day === null &&
    rules.mineral_mix === null &&
    rules.water_advice === null;
  const validWarnings =
    Array.isArray(value.warnings) && value.warnings.every(isWarning);
  const validLimitations =
    Array.isArray(value.limitations) &&
    value.limitations.every((item) => typeof item === 'string');
  const validFallbacks =
    Array.isArray(value.fallback_reasons) &&
    value.fallback_reasons.every((item) => typeof item === 'string');

  return (
    validEnvironment &&
    validPredictions &&
    validSources &&
    validRules &&
    validWarnings &&
    validLimitations &&
    validFallbacks
  );
};

const farmerMessageForStatus = (status: number | null): string => {
  if (status === 400 || status === 422) {
    return 'The dry-matter intake inputs were not accepted. Check the feeding inputs and try again.';
  }
  if (status !== null && status >= 500) {
    return 'The dry-matter intake service is temporarily unavailable. Your existing FarmLite recommendation is unaffected.';
  }
  return 'Could not reach the dry-matter intake service. Your existing FarmLite recommendation is unaffected.';
};

export const predictBangladeshCandidates = async (
  request: BangladeshPredictionRequest,
  signal?: AbortSignal
): Promise<BangladeshPredictionResponse> => {
  try {
    const response = await axios.post<unknown>(
      `${FLASK_API_BASE_URL}/api/v2/predict`,
      request,
      {
        signal,
        headers: { 'Content-Type': 'application/json' },
      }
    );
    if (!isBangladeshPredictionResponse(response.data)) {
      throw new CandidateApiError(
        'The dry-matter intake service returned an unexpected response. Your existing FarmLite recommendation is unaffected.',
        { code: 'MALFORMED_RESPONSE' }
      );
    }
    return response.data;
  } catch (error) {
    if (error instanceof CandidateApiError) throw error;
    if (axios.isCancel(error)) {
      throw new CandidateApiError('Dry-matter intake request cancelled.', {
        code: 'REQUEST_CANCELLED',
      });
    }
    if (!axios.isAxiosError(error)) {
      throw new CandidateApiError(farmerMessageForStatus(null));
    }

    const status = error.response?.status ?? null;
    const body = isRecord(error.response?.data)
      ? (error.response?.data as CandidateErrorBody)
      : null;
    throw new CandidateApiError(farmerMessageForStatus(status), {
      status,
      code:
        typeof body?.error_code === 'string'
          ? body.error_code
          : 'CANDIDATE_REQUEST_FAILED',
      fieldErrors: isRecord(body?.field_errors)
        ? (body.field_errors as Record<string, string>)
        : {},
    });
  }
};
