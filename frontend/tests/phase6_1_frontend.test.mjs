import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import test from 'node:test';

import { buildCandidateRequest } from '../src/features/bangladeshCandidate.ts';
import {
  buildFarmerPdfContent,
  createFarmerRecommendationPdf,
  DMI_RATION_EXPLANATION,
  FARMER_ADVISORY_DISCLAIMER,
} from '../src/utils/farmerRecommendationPdf.ts';

const projectRoot = resolve('.');
const source = (path) => readFileSync(join(projectRoot, path), 'utf8');
const pageSource = source('src/pages/FeedRecommendation.tsx');
const candidateCardsSource = source(
  'src/components/ResearchPredictions.tsx'
);
const pdfSource = source('src/utils/farmerRecommendationPdf.ts');

const candidateFormValues = {
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

const pdfData = {
  generatedAt: new Date('2026-07-26T10:00:00.000Z'),
  animal: {
    name: 'Demo Cow',
    tag: 'COW-001',
    breed: 'Holstein-Friesian',
    ageMonths: '48',
    weightKg: '420',
    lactationStage: 'Mid Lactation',
    healthStatus: 'Healthy',
    daysInMilk: '120',
    previousWeekAvgYieldL: '7',
    bodyConditionScore: '3',
    ambientTemperatureC: '28',
    humidityPercent: '75',
    geneticGroupLabel: '75% Holstein Friesian cross',
  },
  expectedMilkYieldLDay: 17.51,
  predictedDmiKgDay: 11.39,
  calculatedThi: 78.37,
  thiCategory: 'T1',
  ration: {
    totalKgDay: 16.73,
    roughageKgDay: 10.87,
    concentrateKgDay: 5.86,
    mineralMixKgDay: 0.1,
    waterAdvice: 'Provide clean water with free access throughout the day.',
    feedingFrequency: '2 feedings per day',
    confidenceLevel: 'Moderate',
  },
  ruleExplanation: [
    'The FarmLite nutrition rule engine calculated an advisory ration quantity of 16.73 kg/day.',
  ],
  cowAndRationWarnings: [],
  dmiScopeMessage: 'Validated within the current supported model scope.',
  limitations: ['The expected milk yield is an estimate.'],
};

test('01 farmer UI contains one visible milk-yield heading', () => {
  assert.equal(pageSource.match(/Expected Milk Yield/g)?.length, 1);
});

test('02 collected-data candidate milk is absent from farmer UI', () => {
  assert.doesNotMatch(candidateCardsSource, /milk_yield_l_day|Milk Yield/i);
  assert.doesNotMatch(pageSource, /candidate.*milk|comparison milk/i);
});

test('03 collected-data candidate milk is absent from farmer PDF code', () => {
  assert.doesNotMatch(pdfSource, /milk_yield_l_day|candidate milk/i);
});

test('04 expected milk binds to the existing FarmLite prediction', () => {
  assert.match(
    pageSource,
    /Expected Milk Yield[\s\S]*recommendation\.prediction\.predictedMilkYieldL/
  );
});

test('05 DMI binds only to the v2 candidate response', () => {
  assert.match(candidateCardsSource, /response\?\.ml_predictions\.dmi_kg_day/);
});

test('06 DMI uses kg DM per cow per day', () => {
  assert.match(candidateCardsSource, /kg DM\/cow\/day/);
  assert.match(pdfSource, /kg DM\/cow\/day/);
});

test('07 DMI is never labelled total feed or ration', () => {
  const dmiCard = candidateCardsSource;
  assert.doesNotMatch(dmiCard, /Total Feed|Total Ration|Fresh Feed/i);
  assert.match(dmiCard, /Predicted Dry-Matter Intake/);
});

test('08 advisory ration is labelled as rule-engine generated', () => {
  assert.match(pageSource, /Advisory Daily Ration/);
  assert.match(pageSource, /Source: FarmLite nutrition rule engine/);
});

test('09 misleading model-supplied feed sentence is absent', () => {
  const renderedSources = [pageSource, candidateCardsSource, pdfSource].join(
    '\n'
  );
  assert.doesNotMatch(
    renderedSources,
    /The model supplied an estimated feed quantity/i
  );
  assert.match(
    pageSource,
    /FarmLite nutrition rule engine calculated an advisory ration quantity/
  );
});

test('10 genetic group is inside the normal Feeding Inputs section', () => {
  const feedingInputsIndex = pageSource.indexOf('Feeding Inputs');
  const selectorIndex = pageSource.indexOf('id="genetic-group"');
  assert.ok(feedingInputsIndex >= 0);
  assert.ok(selectorIndex > feedingInputsIndex);
});

test('11 breed never supplies genetic group', () => {
  assert.match(pageSource, /breed: animal\.breed,\s*geneticGroup: '',/);
  assert.doesNotMatch(pageSource, /geneticGroup:\s*animal\.breed/);
});

test('12 Unknown group preserves normal request fields and omits backend group', () => {
  const decision = buildCandidateRequest({
    ...candidateFormValues,
    geneticGroup: 'Unknown',
  });
  assert.ok(decision.request);
  assert.equal(decision.request.breed, candidateFormValues.breed);
  assert.equal('genetic_group' in decision.request, false);
  assert.match(pageSource, /setRecommendation\(response\.data\)/);
});

test('13 Unknown group never creates zero DMI', () => {
  const content = buildFarmerPdfContent({
    ...pdfData,
    predictedDmiKgDay: null,
    animal: { ...pdfData.animal, geneticGroupLabel: 'Unknown / Not sure' },
  });
  assert.equal(
    content.primaryResults.find(
      (result) => result.label === 'Predicted Dry-Matter Intake'
    )?.value,
    'Unavailable'
  );
});

test('14 THI is displayed from the backend response', () => {
  assert.match(candidateCardsSource, /response\?\.environment\.calculated_thi/);
  assert.match(candidateCardsSource, /response\?\.environment\.thi_category/);
});

test('15 frontend still contains no THI formula', () => {
  const sources = [pageSource, candidateCardsSource, pdfSource].join('\n');
  assert.doesNotMatch(sources, /0\.0055|calculateThi|calculateTHI/);
});

test('16 candidate failure cannot clear the successful existing result', () => {
  const catchBlock = pageSource.match(
    /\.catch\(\(requestError: unknown\)[\s\S]*?\.finally/
  )?.[0];
  assert.ok(catchBlock);
  assert.doesNotMatch(catchBlock, /setRecommendation\(null\)/);
});

test('17 feature-disabled behavior does not call v2 or show candidate cards', () => {
  assert.match(
    pageSource,
    /if \(BANGLADESH_CANDIDATE_UI_ENABLED\) \{\s*startCandidateRequest\(\)/
  );
  assert.match(
    pageSource,
    /BANGLADESH_CANDIDATE_UI_ENABLED \? \(\s*<CandidateDmiAndThiCards/
  );
});

test('18 feature-disabled PDF retains the existing report path', () => {
  assert.match(
    pageSource,
    /if \(BANGLADESH_CANDIDATE_UI_ENABLED\) \{[\s\S]*createFarmerRecommendationPdf/
  );
  assert.match(pageSource, /FarmLite AI Feed Recommendation Report/);
});

test('19 unified PDF has one milk result and one DMI result', () => {
  const content = buildFarmerPdfContent(pdfData);
  assert.equal(
    content.primaryResults.filter((result) => /Milk Yield/.test(result.label))
      .length,
    1
  );
  assert.equal(
    content.primaryResults.filter((result) =>
      /Dry-Matter Intake/.test(result.label)
    ).length,
    1
  );
});

test('20 user-facing source labels are geography-neutral', () => {
  const renderedSources = [pageSource, candidateCardsSource, pdfSource].join(
    '\n'
  );
  assert.doesNotMatch(
    renderedSources,
    /Bangladesh DMI|Bangladesh milk|Bangladesh research|Bangladesh model/i
  );
});

test('21 banned farmer-facing phrases are absent', () => {
  const renderedSources = [pageSource, candidateCardsSource, pdfSource].join(
    '\n'
  );
  for (const phrase of [
    'Optional research prediction input',
    'Research AI Predictions',
    'Research prototype',
    'Individual Cow Milk Estimate',
  ]) {
    assert.equal(renderedSources.includes(phrase), false);
  }
});

test('22 responsive and accessibility controls remain present', () => {
  assert.match(pageSource, /sm:grid-cols-2/);
  assert.match(candidateCardsSource, /min-w-0/);
  assert.match(pageSource, /aria-invalid/);
  assert.match(pageSource, /aria-describedby/);
  assert.match(pageSource, /focus:ring/);
});

test('23 PDF title is the approved decision-support title', () => {
  assert.equal(
    buildFarmerPdfContent(pdfData).title,
    'FarmLite Feed and Production Decision-Support Report'
  );
});

test('24 PDF value sources use the approved ownership labels', () => {
  assert.deepEqual(buildFarmerPdfContent(pdfData).valueSources, [
    'Expected milk yield: FarmLite milk prediction model',
    'Dry-matter intake: Collected-data DMI model',
    'Heat Stress Index: Backend THI calculation',
    'Advisory ration: FarmLite nutrition rule engine',
  ]);
});

test('25 PDF contains the restrained collected-data DOI note', () => {
  assert.match(
    buildFarmerPdfContent(pdfData).technicalSourceNotes.join(' '),
    /Mendeley Data, DOI: 10\.17632\/954f6g36sb\.2/
  );
});

test('26 unified farmer PDF is exactly two pages for controlled data', () => {
  const report = createFarmerRecommendationPdf(pdfData);
  assert.equal(report.getNumberOfPages(), 2);
});

test('27 unified farmer PDF produces a real non-empty PDF buffer', () => {
  const report = createFarmerRecommendationPdf(pdfData);
  assert.ok(report.output('arraybuffer').byteLength > 3000);
});

test('28 PDF without candidate DMI still produces two usable pages', () => {
  const report = createFarmerRecommendationPdf({
    ...pdfData,
    predictedDmiKgDay: null,
    dmiScopeMessage: 'Dry-matter intake estimate is currently unavailable.',
  });
  assert.equal(report.getNumberOfPages(), 2);
  assert.ok(report.output('arraybuffer').byteLength > 2500);
});

test('29 approved advisory disclaimer is used in UI and PDF', () => {
  assert.match(pageSource, /FARMER_ADVISORY_DISCLAIMER/);
  assert.equal(
    buildFarmerPdfContent(pdfData).disclaimer,
    FARMER_ADVISORY_DISCLAIMER
  );
});

test('30 DMI and ration explanation is shared by UI and PDF', () => {
  assert.match(pageSource, /DMI_RATION_EXPLANATION/);
  assert.ok(buildFarmerPdfContent(pdfData).explanation.includes(
    DMI_RATION_EXPLANATION
  ));
});

test('31 sample values are not hard-coded in production source', () => {
  const productionSources = [pageSource, candidateCardsSource, pdfSource].join(
    '\n'
  );
  for (const value of ['17.51', '11.39', '78.37', '16.73']) {
    assert.equal(productionSources.includes(value), false);
  }
});

test('32 PDF null values never become undefined, null or NaN text', () => {
  const content = buildFarmerPdfContent({
    ...pdfData,
    predictedDmiKgDay: null,
    calculatedThi: null,
    thiCategory: null,
  });
  const serialized = JSON.stringify(content);
  assert.doesNotMatch(serialized, /undefined|NaN/);
  assert.equal(serialized.includes('null'), false);
});
