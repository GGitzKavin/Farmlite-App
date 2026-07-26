import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import test from 'node:test';

import {
  isBangladeshPredictionResponse,
} from '../src/api/bangladeshCandidate.ts';
import { parsePublicFeatureFlag } from '../src/config/publicFeatureFlag.ts';
import {
  BANGLADESH_GENETIC_GROUP_OPTIONS,
  buildCandidateRequest,
  candidateSourceLabel,
  formatCandidateNumber,
} from '../src/features/bangladeshCandidate.ts';

const projectRoot = resolve('.');
const source = (path) => readFileSync(join(projectRoot, path), 'utf8');
const pageSource = source('src/pages/FeedRecommendation.tsx');
const componentSource = source('src/components/ResearchPredictions.tsx');
const clientSource = source('src/api/bangladeshCandidate.ts');
const featureFlagSource = source('src/config/featureFlags.ts');

const formValues = {
  breed: 'Holstein-Friesian',
  geneticGroup: 'HF75',
  ageMonths: '48',
  weightKg: '420',
  lactationStage: 'Mid Lactation',
  daysInMilk: '120',
  previousWeekAvgYield: '7',
  bodyConditionScore: '3',
  ambientTemperatureC: '28',
  humidityPercent: '75',
  healthStatus: 'Healthy',
};

const responseFixture = {
  schema_version: '2.0.0-design',
  prediction_status: 'ELIGIBLE',
  eligibility: {
    dmi: { status: 'ELIGIBLE', scope: 'IN_SCOPE', fallback_reason: null },
    milk: { status: 'ELIGIBLE', scope: 'IN_SCOPE', fallback_reason: null },
  },
  environment: {
    calculated_thi: 79.045,
    display_thi: 79.05,
    thi_category: 'T1',
    mapping_version: 'bangladesh_thi_mapping_contract_v1',
    verification_status: 'VERIFIED_WITH_LIMITATIONS',
    source: 'SERVER_CALCULATED',
  },
  ml_predictions: {
    dmi_kg_day: 11.390466994631726,
    milk_yield_l_day: 6.654754896938108,
  },
  model_sources: {
    dmi: 'BANGLADESH_DMI_CANDIDATE_V1',
    milk: 'BANGLADESH_MILK_CANDIDATE_V1',
  },
  rule_recommendation: {
    feed_category: null,
    roughage_kg_day: null,
    concentrate_kg_day: null,
    mineral_mix: null,
    water_advice: null,
  },
  warnings: [],
  limitations: [],
  fallback_reasons: [],
};

test('01 candidate UI flag defaults false', () => {
  assert.equal(parsePublicFeatureFlag(undefined), false);
});

test('02 malformed candidate flags remain false', () => {
  for (const value of ['', 'enabled', '2', 'truth', 'false']) {
    assert.equal(parsePublicFeatureFlag(value), false);
  }
});

test('03 exact enabled flag values are accepted case-insensitively', () => {
  for (const value of ['1', 'true', 'YES', 'On']) {
    assert.equal(parsePublicFeatureFlag(value), true);
  }
});

test('04 no v2 request starts when frontend flag is disabled', () => {
  assert.match(
    pageSource,
    /if \(BANGLADESH_CANDIDATE_UI_ENABLED\) \{\s*startCandidateRequest\(\)/
  );
});

test('05 existing recommendation endpoint remains available', () => {
  assert.match(pageSource, /\/api\/ai\/feed-recommendation/);
  assert.match(pageSource, /setRecommendation\(response\.data\)/);
});

test('06 exact approved genetic-group values remain unchanged', () => {
  assert.deepEqual(
    BANGLADESH_GENETIC_GROUP_OPTIONS.map((option) => option.value),
    ['Local', 'HF50', 'HF62.5', 'HF75', 'HF87.5']
  );
});

test('07 genetic group has no silent default', () => {
  assert.match(pageSource, /geneticGroup: '',/);
  assert.match(pageSource, /<option value="">Select genetic group<\/option>/);
});

test('08 breed never populates genetic group', () => {
  assert.match(pageSource, /breed: animal\.breed,\s*geneticGroup: '',/);
  assert.doesNotMatch(pageSource, /geneticGroup:\s*animal\.breed/);
});

test('09 missing genetic group preserves a THI-capable request', () => {
  const decision = buildCandidateRequest({ ...formValues, geneticGroup: '' });
  assert.ok(decision.request);
  assert.equal('genetic_group' in decision.request, false);
  assert.equal(decision.field, null);
  assert.equal(
    decision.message,
    'A verified genetic group is required to generate the dry-matter intake estimate.'
  );
});

test('10 explicit Unknown preserves a THI-capable request without a group', () => {
  const decision = buildCandidateRequest({
    ...formValues,
    geneticGroup: 'Unknown',
  });
  assert.ok(decision.request);
  assert.equal('genetic_group' in decision.request, false);
  assert.match(decision.message, /verified genetic group is required/i);
});

test('11 temperature is sent in the Celsius field', () => {
  const decision = buildCandidateRequest(formValues);
  assert.equal(decision.request.ambient_temperature_c, 28);
});

test('12 humidity below zero is rejected', () => {
  assert.equal(
    buildCandidateRequest({ ...formValues, humidityPercent: '-0.1' }).request,
    null
  );
});

test('13 humidity above 100 is rejected', () => {
  assert.equal(
    buildCandidateRequest({ ...formValues, humidityPercent: '100.1' }).request,
    null
  );
});

test('14 undefined optional request values are omitted', () => {
  const decision = buildCandidateRequest({
    ...formValues,
    daysInMilk: '',
    previousWeekAvgYield: '',
    bodyConditionScore: '',
    healthStatus: '',
  });
  for (const field of [
    'days_in_milk',
    'previous_week_avg_yield_l',
    'body_condition_score',
    'health_status',
  ]) {
    assert.equal(field in decision.request, false);
  }
});

test('15 frontend contains no THI formula or category calculation', () => {
  const relevant = [
    pageSource,
    componentSource,
    clientSource,
    source('src/features/bangladeshCandidate.ts'),
  ].join('\n');
  assert.doesNotMatch(relevant, /0\.0055/);
  assert.doesNotMatch(relevant, /calculateThi|calculateTHI/);
});

test('16 v2 client uses the approved endpoint', () => {
  assert.match(clientSource, /\/api\/v2\/predict/);
});

test('17 valid controlled response passes defensive validation', () => {
  assert.equal(isBangladeshPredictionResponse(responseFixture), true);
});

test('18 unexpected THI source fails response validation', () => {
  assert.equal(
    isBangladeshPredictionResponse({
      ...responseFixture,
      environment: { ...responseFixture.environment, source: 'CLIENT' },
    }),
    false
  );
});

test('19 unavailable remains distinct from zero', () => {
  assert.equal(formatCandidateNumber(null), 'Unavailable');
  assert.equal(formatCandidateNumber(0), '0');
});

test('20 DMI retains an explicit dry-matter unit', () => {
  assert.match(componentSource, /kg DM\/cow\/day/);
  assert.match(componentSource, /after excluding moisture/);
});

test('21 farmer candidate cards do not render candidate milk', () => {
  assert.doesNotMatch(componentSource, /milk_yield_l_day|Milk Yield/i);
});

test('22 source-neutral DMI attribution is available', () => {
  assert.equal(
    candidateSourceLabel('BANGLADESH_DMI_CANDIDATE_V1'),
    'Collected-data DMI model'
  );
});

test('23 changing any candidate input invalidates stale state', () => {
  assert.match(pageSource, /CANDIDATE_REQUEST_FORM_FIELDS\.has\(name\)/);
  assert.match(
    pageSource,
    /CANDIDATE_REQUEST_FORM_FIELDS\.has\(name\)[\s\S]*setCandidateResponse\(null\)/
  );
});

test('24 frontend contains no bundled model artifact', () => {
  const walk = (directory) =>
    readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
      const path = join(directory, entry.name);
      return entry.isDirectory() ? walk(path) : [path];
    });
  const files = walk(join(projectRoot, 'src')).concat(
    walk(join(projectRoot, 'public'))
  );
  assert.equal(
    files.some((path) => /\.(joblib|pkl|pickle)$/i.test(path)),
    false
  );
});

test('25 candidate mode is not enabled in source defaults', () => {
  assert.match(
    featureFlagSource,
    /parsePublicFeatureFlag\(\s*import\.meta\.env\.VITE_BANGLADESH_CANDIDATE_UI_ENABLED/
  );
});
