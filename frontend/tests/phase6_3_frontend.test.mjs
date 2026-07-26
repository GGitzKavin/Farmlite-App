import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import test from 'node:test';

import { isBangladeshPredictionResponse } from '../src/api/bangladeshCandidate.ts';
import {
  reconcileOwnedBatches,
  upsertOwnedBatch,
} from '../src/features/batchRecords.ts';
import { buildCandidateRequest } from '../src/features/bangladeshCandidate.ts';
import {
  BATCH_LIVESTOCK_TYPES,
  INDIVIDUAL_LIVESTOCK_TYPES,
} from '../src/features/livestockTypes.ts';
import { getInlineLivestockTypeOptions } from '../src/features/inlineLivestockEdit.ts';

const projectRoot = resolve('.');
const source = (path) => readFileSync(join(projectRoot, path), 'utf8');
const animalEntrySource = source(
  'src/pages/Livestock/AnimalEntryForm.tsx'
);
const batchEntrySource = source(
  'src/pages/Livestock/BatchEntryForm.tsx'
);
const batchManagementSource = source(
  'src/pages/Livestock/BatchManagement.tsx'
);
const editLivestockSource = source(
  'src/pages/Livestock/EditLivestock.tsx'
);
const livestockDetailSource = source(
  'src/pages/Livestock/LivestockDetail.tsx'
);
const livestockListSource = source(
  'src/pages/Livestock/LivestockList.tsx'
);
const feedPageSource = source('src/pages/FeedRecommendation.tsx');
const candidateFeatureSource = source(
  'src/features/bangladeshCandidate.ts'
);
const candidateCardsSource = source(
  'src/components/ResearchPredictions.tsx'
);

const currentUserId = 'farmer-new';
const savedBatch = {
  id: 'batch-new',
  batchName: 'New flock',
  species: 'Chicken',
  headCount: 20,
  userId: currentUserId,
  createdAt: new Date('2026-07-26T10:00:00Z'),
};

const candidateFormValues = {
  breed: 'Holstein-Friesian',
  geneticGroup: '',
  ageMonths: '48',
  weightKg: '420',
  lactationStage: 'Mid Lactation',
  daysInMilk: '120',
  previousWeekAvgYield: '7',
  bodyConditionScore: '3',
  ambientTemperatureC: '28',
  humidityPercent: '70',
  healthStatus: 'Healthy',
};

const missingGroupResponse = {
  schema_version: '2.0.0-design',
  prediction_status: 'FALLBACK_REQUIRED',
  eligibility: {
    dmi: {
      status: 'MISSING_REQUIRED_INPUT',
      scope: 'UNRESOLVED',
      fallback_reason: 'GENETIC_GROUP_MISSING',
    },
    milk: {
      status: 'MISSING_REQUIRED_INPUT',
      scope: 'UNRESOLVED',
      fallback_reason: 'GENETIC_GROUP_MISSING',
    },
  },
  environment: {
    calculated_thi: 78.61,
    display_thi: 78.61,
    thi_category: 'T1',
    mapping_version: 'bangladesh_thi_mapping_contract_v1',
    verification_status: 'VERIFIED_WITH_LIMITATIONS',
    source: 'SERVER_CALCULATED',
  },
  ml_predictions: {
    dmi_kg_day: null,
    milk_yield_l_day: null,
  },
  model_sources: {
    dmi: null,
    milk: null,
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
  fallback_reasons: ['GENETIC_GROUP_MISSING'],
};

test('01 a successfully saved owned batch is inserted immediately', () => {
  assert.deepEqual(upsertOwnedBatch([], savedBatch, currentUserId), [
    savedBatch,
  ]);
});

test('02 batch save awaits Firestore before local display and success', () => {
  const saveFlow = batchManagementSource.slice(
    batchManagementSource.indexOf('const handleSave = async'),
    batchManagementSource.indexOf('const handleDeleteBatch')
  );
  const writeIndex = saveFlow.indexOf('await addDoc');
  const stateIndex = saveFlow.indexOf('setBatches');
  const successIndex = saveFlow.indexOf("onSuccess('Batch created successfully!')");
  assert.ok(writeIndex >= 0);
  assert.ok(stateIndex > writeIndex);
  assert.ok(successIndex > stateIndex);
});

test('03 saved batches include the current authenticated user ownership', () => {
  assert.match(
    batchManagementSource,
    /const currentUserId = currentUser\.uid[\s\S]*await addDoc\(collection\(db, 'batches'\), \{[\s\S]*userId: currentUserId/
  );
});

test('04 another user’s batches are excluded from rendered state', () => {
  const otherBatch = {
    ...savedBatch,
    id: 'batch-other',
    userId: 'farmer-other',
  };
  assert.deepEqual(
    reconcileOwnedBatches([otherBatch, savedBatch], currentUserId),
    [savedBatch]
  );
  assert.match(
    batchManagementSource,
    /if \(batch\.userId !== currentUser\?\.uid\) return false/
  );
});

test('05 the listener keeps the Firestore ownership predicate', () => {
  assert.match(
    batchManagementSource,
    /collection\(db, 'batches'\)[\s\S]*where\('userId', '==', currentUserId\)/
  );
});

test('06 batch ordering no longer requires a composite Firestore index', () => {
  assert.doesNotMatch(batchManagementSource, /\borderBy\(/);
  assert.match(batchManagementSource, /reconcileOwnedBatches/);
});

test('07 listener and optimistic write reconcile by document ID', () => {
  const serverCopy = {
    ...savedBatch,
    batchName: 'New flock from listener',
  };
  const reconciled = upsertOwnedBatch(
    [savedBatch],
    serverCopy,
    currentUserId
  );
  assert.equal(reconciled.length, 1);
  assert.equal(reconciled[0].batchName, 'New flock from listener');
});

test('08 active search and type filters clear after batch creation', () => {
  assert.match(
    livestockListSource,
    /handleBatchCreated[\s\S]*setSearchTerm\(''\)[\s\S]*setFilterSpecies\(''\)/
  );
  assert.match(
    livestockListSource,
    /onBatchCreated=\{handleBatchCreated\}/
  );
});

test('09 the Add Animal field is visibly and accessibly Livestock', () => {
  assert.match(
    animalEntrySource,
    /<label htmlFor="individual-livestock-type"[\s\S]*Livestock[\s\S]*<select[\s\S]*id="individual-livestock-type"/
  );
});

test('10 Species is absent from the individual livestock field label', () => {
  assert.doesNotMatch(animalEntrySource, />\s*Species\s*</);
  assert.doesNotMatch(editLivestockSource, />\s*Species\s*</);
  assert.doesNotMatch(livestockDetailSource, />\s*Species\s*</);
});

test('11 individual options retain only supported non-poultry values', () => {
  assert.deepEqual([...INDIVIDUAL_LIVESTOCK_TYPES], [
    'Dairy Cattle',
    'Cattle (Beef)',
    'Sheep/Goats',
    'Swine',
  ]);
  assert.equal(INDIVIDUAL_LIVESTOCK_TYPES.includes('Chicken'), false);
  assert.equal(INDIVIDUAL_LIVESTOCK_TYPES.includes('Duck'), false);
});

test('12 batch options retain the existing poultry values', () => {
  assert.equal(BATCH_LIVESTOCK_TYPES.includes('Chicken'), true);
  assert.equal(BATCH_LIVESTOCK_TYPES.includes('Duck'), true);
  assert.match(batchEntrySource, /BATCH_LIVESTOCK_TYPES/);
});

test('13 existing stored types remain available without remapping', () => {
  const legacyOptions = getInlineLivestockTypeOptions('Chicken');
  assert.equal(legacyOptions[0].value, 'Chicken');
  assert.equal(legacyOptions[0].label, 'Legacy stored value (retained)');
  assert.match(
    livestockDetailSource,
    /getInlineLivestockTypeOptions\(editForm\.species\)/
  );
});

test('14 an unselected group still produces a backend THI request', () => {
  const decision = buildCandidateRequest(candidateFormValues);
  assert.ok(decision.request);
  assert.equal('genetic_group' in decision.request, false);
  assert.equal(decision.request.ambient_temperature_c, 28);
  assert.equal(decision.request.humidity_percent, 70);
});

test('15 missing group uses the required DMI message and never zero', () => {
  const decision = buildCandidateRequest(candidateFormValues);
  assert.equal(
    decision.message,
    'A verified genetic group is required to generate the dry-matter intake estimate.'
  );
  assert.equal(missingGroupResponse.ml_predictions.dmi_kg_day, null);
});

test('16 missing group preserves existing milk and ration orchestration', () => {
  assert.match(feedPageSource, /\/api\/ai\/feed-recommendation/);
  assert.match(feedPageSource, /setRecommendation\(response\.data\)/);
  assert.match(
    feedPageSource,
    /if \(BANGLADESH_CANDIDATE_UI_ENABLED\) \{\s*startCandidateRequest\(\)/
  );
});

test('17 backend-calculated THI fallback passes validation and is rendered', () => {
  assert.equal(isBangladeshPredictionResponse(missingGroupResponse), true);
  assert.match(
    candidateCardsSource,
    /response\?\.environment\.calculated_thi/
  );
  assert.match(
    candidateCardsSource,
    /response\?\.environment\.thi_category/
  );
  assert.match(candidateCardsSource, /Source: Backend THI calculation/);
});

test('18 the frontend contains no THI formula or genetic inference', () => {
  const combined = [
    candidateFeatureSource,
    candidateCardsSource,
    feedPageSource,
  ].join('\n');
  assert.doesNotMatch(combined, /0\.0055|calculateThi|calculateTHI/);
  assert.doesNotMatch(combined, /geneticGroup:\s*animal\.breed/);
});
