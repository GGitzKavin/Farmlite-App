import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import test from 'node:test';

import {
  FARM_TYPE_MAX_LENGTH,
  loadFarmType,
  normalizeFarmType,
  validateFarmType,
} from '../src/features/profileForm.ts';

const projectRoot = resolve('.');
const source = (path) => readFileSync(join(projectRoot, path), 'utf8');
const livestockListSource = source('src/pages/Livestock/LivestockList.tsx');
const livestockDetailSource = source(
  'src/pages/Livestock/LivestockDetail.tsx'
);
const inlineLivestockEditSource = source(
  'src/features/inlineLivestockEdit.ts'
);
const batchManagementSource = source(
  'src/pages/Livestock/BatchManagement.tsx'
);
const batchEntrySource = source(
  'src/pages/Livestock/BatchEntryForm.tsx'
);
const notificationsSource = source('src/pages/Notifications.tsx');
const profileSource = source('src/pages/Profile.tsx');
const dashboardSource = source('src/pages/Dashboard.tsx');
const typesSource = source('src/types/index.ts');

test('01 All Species is absent from Livestock Management', () => {
  assert.equal(livestockListSource.includes('All Species'), false);
});

test('02 All Livestock keeps the unfiltered branch', () => {
  assert.match(livestockListSource, /<option value="">All Livestock<\/option>/);
  assert.match(
    source('src/pages/Livestock/LivestockTable.tsx'),
    /filterSpecies[\s\S]*\?\s*getSpeciesFilterValue\(species\) === filterSpecies[\s\S]*:\s*true/
  );
  assert.match(
    batchManagementSource,
    /filterSpecies[\s\S]*\?\s*getSpeciesFilterValue\(species\) === filterSpecies[\s\S]*:\s*true/
  );
});

test('03 Batch Management uses all FarmLite palette tokens', () => {
  const combined = `${batchManagementSource}\n${batchEntrySource}`;
  for (const token of ['#606c38', '#283618', '#fefae0', '#dda15e', '#bc6c25']) {
    assert.match(combined, new RegExp(token));
  }
});

test('04 Batch Management Firestore behavior remains present', () => {
  for (const operation of [
    'onSnapshot',
    'addDoc',
    'updateDoc',
    'deleteDoc',
    'window.confirm',
  ]) {
    assert.equal(batchManagementSource.includes(operation), true);
  }
  assert.match(batchManagementSource, /matchesSearch && matchesFilter/);
});

test('05 Gender is not rendered by Animal Profile', () => {
  assert.doesNotMatch(livestockDetailSource, />Gender</);
  assert.doesNotMatch(livestockDetailSource, /animal\.gender/);
});

test('06 Gender remains stored but is excluded from the partial edit payload', () => {
  assert.match(typesSource, /gender:\s*string/);
  assert.doesNotMatch(livestockDetailSource, /name="gender"/);
  assert.doesNotMatch(inlineLivestockEditSource, /gender\s*:/);
  assert.match(
    livestockDetailSource,
    /await updateDoc[\s\S]*\.\.\.update\.value/
  );
});

test('07 Animal Profile no longer has detail or medical tabs', () => {
  assert.doesNotMatch(livestockDetailSource, /Full Details/);
  assert.doesNotMatch(livestockDetailSource, /Medical & Vaccines/);
  assert.doesNotMatch(livestockDetailSource, /activeTab|setActiveTab/);
});

test('08 Health Status is a separate card', () => {
  assert.match(livestockDetailSource, /aria-labelledby="health-status-title"/);
  assert.match(livestockDetailSource, /id="health-status-title"/);
});

test('09 Medical and Vaccinations is in the continuous page flow', () => {
  assert.match(
    livestockDetailSource,
    /aria-labelledby="medical-vaccinations-title"[\s\S]*Medical and Vaccinations/
  );
  assert.match(livestockDetailSource, /Vaccination History/);
  assert.match(livestockDetailSource, /Medical History/);
});

test('10 Existing health and vaccination actions remain reachable', () => {
  assert.match(livestockDetailSource, /to="\/health"[\s\S]*Add Health Record/);
  assert.match(
    livestockDetailSource,
    /to="\/vaccinations"[\s\S]*Record Vaccination/
  );
  assert.match(source('src/pages/Vaccinations.tsx'), /handleSubmit/);
});

test('11 Notifications subtitle is absent', () => {
  assert.equal(
    notificationsSource.includes('Farm alerts and reminders'),
    false
  );
});

test('12 Profile subtitle is absent', () => {
  assert.equal(
    profileSource.includes('Manage your personal and farm information.'),
    false
  );
});

test('13 About FarmLite does not describe farm scale', () => {
  const about = profileSource.slice(profileSource.indexOf('About FarmLite'));
  assert.doesNotMatch(about, /small farms|medium farms|large farms|farm scale/i);
  assert.doesNotMatch(about, /prototype/i);
});

test('14 About FarmLite uses the approved description', () => {
  assert.match(
    profileSource,
    /AI-assisted livestock management and decision-support system\./
  );
  assert.match(profileSource, /© 2026 FarmLite/);
});

test('15 Farm Type is a text input rather than a select', () => {
  const fieldStart = profileSource.indexOf('htmlFor="farm-type"');
  const fieldEnd = profileSource.indexOf('Farm Contact Number', fieldStart);
  const field = profileSource.slice(fieldStart, fieldEnd);
  assert.match(field, /<input/);
  assert.match(field, /type="text"/);
  assert.match(field, /placeholder="Enter farm type"/);
  assert.doesNotMatch(field, /<select/);
});

test('16 Existing Farm Type values load without remapping', () => {
  assert.equal(loadFarmType('Mixed livestock'), 'Mixed livestock');
  assert.equal(loadFarmType('Research farm'), 'Research farm');
  assert.equal(loadFarmType(undefined), '');
  assert.match(profileSource, /farmType: loadFarmType\(data\.farmType\)/);
});

test('17 Farm Type save values are trimmed', () => {
  assert.equal(normalizeFarmType('  Dairy  '), 'Dairy');
  assert.match(
    profileSource,
    /farmType: normalizeFarmType\(farmForm\.farmType\)/
  );
});

test('18 Whitespace-only Farm Type is rejected accessibly', () => {
  assert.equal(validateFarmType('   '), 'Farm type is required.');
  assert.match(profileSource, /aria-invalid=\{Boolean\(farmTypeError\)\}/);
  assert.match(profileSource, /id="farm-type-error" role="alert"/);
});

test('19 Farm Type has a reasonable enforced maximum length', () => {
  assert.equal(FARM_TYPE_MAX_LENGTH, 80);
  assert.match(profileSource, /maxLength=\{FARM_TYPE_MAX_LENGTH\}/);
  assert.match(validateFarmType('x'.repeat(81)), /80 characters or fewer/);
});

test('20 Dashboard additions read real existing collections', () => {
  assert.match(dashboardSource, /getDocs\(collection\(db, collectionName\)\)/);
  for (const collectionName of [
    'livestock',
    'healthRecords',
    'vaccinations',
    'feedInventory',
    'batches',
  ]) {
    assert.equal(dashboardSource.includes(`'${collectionName}'`), true);
  }
  assert.doesNotMatch(dashboardSource, /Math\.random|fake data|placeholder total/i);
});

test('21 Dashboard contains no duplicate legacy summary widgets', () => {
  for (const legacyTitle of [
    'Total Livestock',
    'Vaccines Overdue',
    'Health Alerts',
    'Low Feed Alerts',
  ]) {
    assert.equal(dashboardSource.includes(`>${legacyTitle}<`), false);
  }
  for (const section of [
    'Attention Required',
    'Upcoming Vaccinations',
    'Livestock Overview',
    'Batch Overview',
    'Quick Actions',
  ]) {
    assert.equal(dashboardSource.match(new RegExp(section, 'g'))?.length, 1);
  }
});

test('22 Dashboard mobile layout guards against horizontal overflow', () => {
  assert.match(dashboardSource, /grid-cols-1/);
  assert.match(dashboardSource, /min-w-0/);
  assert.match(dashboardSource, /overflow-hidden/);
  assert.doesNotMatch(dashboardSource, /min-w-\[[4-9]\d\dpx\]/);
});

test('23 Quick Actions use existing routes', () => {
  for (const route of [
    '/livestock',
    '/livestock?view=batch',
    '/vaccinations',
    '/ai-feed',
  ]) {
    assert.equal(dashboardSource.includes(`path: '${route}'`), true);
  }
  assert.match(livestockListSource, /searchParams\.get\('view'\) === 'batch'/);
});

test('24 Dashboard distinguishes 7-day and 30-day vaccination windows', () => {
  assert.match(dashboardSource, /addDays\(today, 7\)/);
  assert.match(dashboardSource, /addDays\(today, 30\)/);
  assert.match(dashboardSource, /'Due within 7 days'/);
  assert.match(dashboardSource, /'Due within 30 days'/);
});

test('25 Dashboard has meaningful empty states', () => {
  assert.match(dashboardSource, /No vaccinations are due soon\./);
  assert.match(dashboardSource, /No livestock require attention\./);
  assert.match(dashboardSource, /No livestock records are available\./);
});

test('26 Dashboard does not invent unavailable batch assignment metrics', () => {
  assert.doesNotMatch(dashboardSource, /animals assigned to batches/i);
  assert.doesNotMatch(dashboardSource, /animals without a batch/i);
  assert.doesNotMatch(dashboardSource, /active batches/i);
  assert.match(dashboardSource, /Recorded batch headcount/);
});

test('27 Dashboard retains existing real-data widgets', () => {
  assert.match(dashboardSource, /Feed Inventory Levels/);
  assert.match(dashboardSource, /Recent Activity/);
  assert.match(dashboardSource, /Livestock added/);
  assert.match(dashboardSource, /Batch created/);
  assert.match(dashboardSource, /feedInventory/);
  assert.match(dashboardSource, /animal\.createdAt/);
  assert.match(dashboardSource, /batch\.createdAt/);
});

test('28 Batch statuses retain visible text labels', () => {
  assert.match(batchManagementSource, /Health Status/);
  assert.match(batchManagementSource, /Vaccinations/);
  assert.match(batchManagementSource, /\{batch\?\.healthStatus \|\| 'Healthy'\}/);
  assert.match(
    batchManagementSource,
    /\{batch\?\.vaccinationStatus \|\| 'No records'\}/
  );
});

test('29 Accessibility contracts remain present', () => {
  const combined = [
    livestockListSource,
    livestockDetailSource,
    profileSource,
    dashboardSource,
    batchManagementSource,
    batchEntrySource,
  ].join('\n');
  assert.match(livestockListSource, /aria-label="Filter by livestock type"/);
  assert.match(combined, /focus-visible:outline/);
  assert.match(profileSource, /role=\{feedback\.type === 'error'/);
  assert.match(dashboardSource, /role="status"/);
  assert.match(dashboardSource, /role="alert"/);
});

test('30 Phase 6.2 changes remain frontend-only', () => {
  assert.doesNotMatch(dashboardSource, /\/api\/v[12]\/predict/);
  assert.doesNotMatch(profileSource, /\/api\/v[12]\/predict/);
  assert.doesNotMatch(livestockDetailSource, /\/api\/v[12]\/predict/);
});
