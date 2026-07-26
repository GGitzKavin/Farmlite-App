import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import test from 'node:test';

import {
  buildInlineLivestockUpdate,
  createInlineLivestockForm,
  getInlineLivestockTypeOptions,
} from '../src/features/inlineLivestockEdit.ts';

const projectRoot = resolve('.');
const source = (path) => readFileSync(join(projectRoot, path), 'utf8');
const detailSource = source('src/pages/Livestock/LivestockDetail.tsx');
const redirectSource = source('src/pages/Livestock/EditLivestock.tsx');
const appSource = source('src/App.tsx');
const typesSource = source('src/types/index.ts');

const storedAnimal = {
  id: 'animal-1',
  animalId: 'COW-001',
  animalName: 'Luna',
  species: 'Dairy Cattle',
  breed: 'Holstein-Friesian',
  gender: 'Female',
  age: 48,
  weight: 420,
  birthDate: '',
  notes: 'Preserve this stored note.',
  batchId: 'batch-legacy',
  userId: 'farmer-1',
  unknownLegacyField: 'preserve-me',
};

const changedForm = {
  ...createInlineLivestockForm(storedAnimal),
  animalName: 'Luna Updated',
  weight: '425.5',
};

test('01 Animal Profile displays an Edit Livestock button', () => {
  assert.match(detailSource, /onClick=\{handleStartEditing\}/);
  assert.match(detailSource, />\s*Edit Livestock\s*</);
});

test('02 Edit Livestock enables inline editing in the profile card', () => {
  const startHandler = detailSource.slice(
    detailSource.indexOf('const handleStartEditing'),
    detailSource.indexOf('const handleCancelEditing')
  );
  assert.match(startHandler, /setIsEditing\(true\)/);
  assert.match(detailSource, /\{isEditing \? \(\s*<form/);
  assert.match(detailSource, /aria-label="Edit livestock details"/);
});

test('03 save updates local profile data and exits edit mode', () => {
  const saveHandler = detailSource.slice(
    detailSource.indexOf('const handleSaveChanges'),
    detailSource.indexOf('const handleDelete')
  );
  assert.match(saveHandler, /await updateDoc/);
  assert.match(saveHandler, /setAnimal\(updatedAnimal\)/);
  assert.match(saveHandler, /setIsEditing\(false\)/);
  assert.match(saveHandler, /Livestock details updated successfully/);

  const result = buildInlineLivestockUpdate(changedForm);
  assert.equal(result.value?.animalName, 'Luna Updated');
  assert.equal(result.value?.weight, 425.5);
});

test('04 cancel discards form changes and restores stored values', () => {
  const cancelHandler = detailSource.slice(
    detailSource.indexOf('const handleCancelEditing'),
    detailSource.indexOf('const handleEditChange')
  );
  assert.match(cancelHandler, /createInlineLivestockForm\(animal\)/);
  assert.match(cancelHandler, /setIsEditing\(false\)/);
  assert.deepEqual(
    createInlineLivestockForm(storedAnimal),
    createInlineLivestockForm({ ...storedAnimal })
  );
});

test('05 standalone edit route redirects to inline profile edit mode', () => {
  assert.match(
    appSource,
    /path="\/livestock\/edit\/:id"[\s\S]*<EditLivestock \/>/
  );
  assert.match(
    redirectSource,
    /<Navigate to=\{`\/livestock\/\$\{id\}\?edit=true`\} replace \/>/
  );
  assert.doesNotMatch(redirectSource, /<form|updateDoc|getDoc/);
});

test('06 gender is not rendered in inline or compatibility edit UI', () => {
  assert.match(typesSource, /gender:\s*string/);
  assert.doesNotMatch(detailSource, />\s*Gender\s*</);
  assert.doesNotMatch(detailSource, /name="gender"/);
  assert.doesNotMatch(redirectSource, /Gender|name="gender"/);
});

test('07 stored gender is preserved by the partial update', () => {
  const result = buildInlineLivestockUpdate(changedForm);
  assert.ok(result.value);
  assert.equal('gender' in result.value, false);
  assert.equal({ ...storedAnimal, ...result.value }.gender, 'Female');
  assert.match(detailSource, /await updateDoc[\s\S]*\.\.\.update\.value/);
});

test('08 Notes or Extra Details is absent from edit mode', () => {
  assert.doesNotMatch(detailSource, /Notes \/ Extra Details/);
  assert.doesNotMatch(detailSource, /name="notes"/);
  assert.doesNotMatch(redirectSource, /Notes \/ Extra Details|name="notes"/);
});

test('09 stored notes and unknown fields are preserved by save', () => {
  const result = buildInlineLivestockUpdate(changedForm);
  assert.ok(result.value);
  assert.equal('notes' in result.value, false);
  assert.equal('unknownLegacyField' in result.value, false);
  const mergedRecord = { ...storedAnimal, ...result.value };
  assert.equal(mergedRecord.notes, 'Preserve this stored note.');
  assert.equal(mergedRecord.unknownLegacyField, 'preserve-me');
  assert.match(detailSource, /const updatedAnimal[\s\S]*\.\.\.animal/);
});

test('10 removed birth-date helper sentence stays absent', () => {
  const combined = `${detailSource}\n${redirectSource}`;
  assert.doesNotMatch(
    combined,
    /calculated from birth date when available/i
  );
});

test('11 individual edit choices do not show Chicken or Duck', () => {
  const visibleLabels = getInlineLivestockTypeOptions('').map(
    (option) => option.label
  );
  assert.equal(visibleLabels.includes('Chicken'), false);
  assert.equal(visibleLabels.includes('Duck'), false);
  assert.doesNotMatch(detailSource, />\s*(Chicken|Duck)\s*</);
});

test('12 legacy livestock values remain selected without poultry labels', () => {
  const legacyForm = createInlineLivestockForm({
    ...storedAnimal,
    species: 'Chicken',
  });
  const options = getInlineLivestockTypeOptions(legacyForm.species);
  assert.equal(legacyForm.species, 'Chicken');
  assert.deepEqual(options[0], {
    value: 'Chicken',
    label: 'Legacy stored value (retained)',
    legacy: true,
  });
  assert.equal(
    options.some((option) => option.label === 'Chicken'),
    false
  );
});

test('13 Health Status remains below the profile card', () => {
  assert.ok(
    detailSource.indexOf('aria-labelledby="health-status-title"') >
      detailSource.indexOf('aria-labelledby="animal-profile-title"')
  );
});

test('14 Medical and Vaccinations remains below Health Status', () => {
  assert.ok(
    detailSource.indexOf('aria-labelledby="medical-vaccinations-title"') >
      detailSource.indexOf('aria-labelledby="health-status-title"')
  );
});

test('15 inline editor uses responsive overflow-safe FarmLite styling', () => {
  assert.match(detailSource, /min-w-0 space-y-6 overflow-x-hidden/);
  assert.match(detailSource, /grid min-w-0 grid-cols-1 gap-4 md:grid-cols-2/);
  assert.match(detailSource, /w-full[\s\S]*sm:w-auto/);
  for (const token of ['#606c38', '#283618', '#fefae0', '#dda15e', '#bc6c25']) {
    assert.match(detailSource, new RegExp(token));
  }
});
