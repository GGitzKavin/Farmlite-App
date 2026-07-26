import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import test from 'node:test';

import {
  MAX_STOCK_QUANTITY,
  calculatePercentageStock,
  calculateRestockedStock,
  roundStockQuantity,
  validateRestockQuantity,
} from '../src/features/feedStock.ts';

const projectRoot = resolve('.');
const source = (path) => readFileSync(join(projectRoot, path), 'utf8');
const inventorySource = source('src/pages/FeedInventory.tsx');

const sourceSection = (start, end) =>
  inventorySource.slice(
    inventorySource.indexOf(start),
    inventorySource.indexOf(end),
  );

test('01 fixed decrease control is replaced by −10%', () => {
  assert.match(inventorySource, />\s*−10%\s*</);
  assert.doesNotMatch(inventorySource, />\s*[−-]10\s*</);
});

test('02 fixed increase control is replaced by +10%', () => {
  assert.match(inventorySource, />\s*\+10%\s*</);
  assert.doesNotMatch(inventorySource, />\s*\+10\s*</);
});

test('03 Restock opens a manual quantity field', () => {
  assert.match(
    inventorySource,
    /openStockDialog\(feed, 'restock'\)/,
  );
  assert.match(
    inventorySource,
    /id="restock-quantity"[\s\S]*type="number"/,
  );
});

test('04 Restock input has the required unambiguous label and helper', () => {
  assert.match(inventorySource, />\s*Quantity received\s*</);
  assert.match(
    inventorySource,
    /Enter the amount of new feed added to the current stock\./,
  );
});

test('05 reducing 1,000 by ten percent returns 900', () => {
  assert.equal(calculatePercentageStock(1_000, 'decrease', 'kg'), 900);
});

test('06 increasing 1,000 by ten percent returns 1,100', () => {
  assert.equal(calculatePercentageStock(1_000, 'increase', 'kg'), 1_100);
});

test('07 restocking 1,000 with 350 returns 1,350', () => {
  assert.equal(calculateRestockedStock(1_000, 350, 'kg'), 1_350);
});

test('08 Restock adds the received amount instead of replacing stock', () => {
  assert.equal(calculateRestockedStock(75, 25, 'kg'), 100);
  assert.notEqual(calculateRestockedStock(75, 25, 'kg'), 25);
});

test('09 stock calculations use the latest Firestore document quantity', () => {
  const openHandler = sourceSection(
    'const openStockDialog',
    'const handleRestockQuantityChange',
  );
  const confirmationHandler = sourceSection(
    'const confirmStockAdjustment',
    'const handleDeleteFeed',
  );

  assert.match(openHandler, /runTransaction/);
  assert.match(openHandler, /transaction\.get\(feedRef\)/);
  assert.match(openHandler, /currentQuantity = Number\(data\.quantity\)/);
  assert.match(
    confirmationHandler,
    /latestQuantity = Number\(data\.quantity\)/,
  );
  assert.match(
    confirmationHandler,
    /calculatePercentageStock\(\s*latestQuantity/,
  );
});

test('10 decimal calculations share stable two-decimal rounding', () => {
  assert.equal(calculatePercentageStock(95, 'decrease', 'kg'), 85.5);
  assert.equal(calculatePercentageStock(95, 'increase', 'kg'), 104.5);
  assert.equal(calculateRestockedStock(95, 20.25, 'kg'), 115.25);
  assert.equal(roundStockQuantity(0.1 + 0.2, 'kg'), 0.3);
});

test('11 percentage reductions never produce negative stock', () => {
  assert.equal(calculatePercentageStock(0, 'decrease', 'kg'), 0);
  assert.ok(calculatePercentageStock(0.01, 'decrease', 'kg') >= 0);
});

test('12 zero-stock percentage controls cannot create a false increase', () => {
  assert.equal(calculatePercentageStock(0, 'increase', 'kg'), 0);
  const controls = sourceSection(
    '{feed.quantity <= 0 &&',
    '<div className="mt-3 flex justify-end">',
  );
  assert.match(controls, /Use Restock to enter the newly received quantity\./);
  assert.equal((controls.match(/feed\.quantity <= 0/g) ?? []).length, 3);
});

test('13 zero stock can be restored using a received quantity', () => {
  assert.equal(calculateRestockedStock(0, 42.5, 'kg'), 42.5);
  assert.match(inventorySource, /openStockDialog\(feed, 'restock'\)/);
});

test('14 invalid Restock values and unsupported precision are rejected', () => {
  assert.equal(
    validateRestockQuantity('', 'kg').error,
    'Enter a quantity greater than zero.',
  );
  assert.equal(
    validateRestockQuantity('0', 'kg').error,
    'Enter a quantity greater than zero.',
  );
  assert.equal(
    validateRestockQuantity('-3', 'kg').error,
    'Enter a quantity greater than zero.',
  );
  for (const value of ['letters', 'NaN', 'Infinity']) {
    assert.equal(
      validateRestockQuantity(value, 'kg').error,
      'Enter a valid numeric quantity.',
    );
  }
  assert.ok(validateRestockQuantity('1.234', 'kg').error);
  assert.ok(validateRestockQuantity('1.5', 'bags').error);
  assert.ok(
    validateRestockQuantity(String(MAX_STOCK_QUANTITY + 1), 'kg').error,
  );
});

test('15 Cancel closes the preview without a Firestore write', () => {
  const closeHandler = sourceSection(
    'const closeStockDialog',
    'const openStockDialog',
  );
  assert.match(closeHandler, /setStockDialog\(null\)/);
  assert.doesNotMatch(closeHandler, /runTransaction|transaction\.update|setFeeds/);
  assert.match(inventorySource, /onClick=\{closeStockDialog\}/);
});

test('16 a successful transaction updates visible quantity immediately', () => {
  const confirmationHandler = sourceSection(
    'const confirmStockAdjustment',
    'const handleDeleteFeed',
  );
  assert.match(confirmationHandler, /transaction\.update\(feedRef, stockUpdate\)/);
  assert.match(confirmationHandler, /setFeeds\(\(previousFeeds\)/);
  assert.ok(
    confirmationHandler.indexOf('await runTransaction') <
      confirmationHandler.indexOf('setFeeds((previousFeeds)'),
  );
  assert.match(confirmationHandler, /setFeedback\(\{ type: 'success'/);
});

test('17 a failed update preserves the previous visible quantity', () => {
  const confirmationHandler = sourceSection(
    'const confirmStockAdjustment',
    'const handleDeleteFeed',
  );
  const failureHandler = confirmationHandler.slice(
    confirmationHandler.lastIndexOf('} catch (error)'),
  );
  assert.doesNotMatch(failureHandler, /setFeeds/);
  assert.match(failureHandler, /previous quantity was preserved/);
});

test('18 transactions verify ownership and preserve unrelated feed fields', () => {
  const confirmationHandler = sourceSection(
    'const confirmStockAdjustment',
    'const handleDeleteFeed',
  );
  const stockUpdate = confirmationHandler.slice(
    confirmationHandler.indexOf('const stockUpdate'),
    confirmationHandler.indexOf('transaction.update'),
  );

  assert.match(confirmationHandler, /data\.userId !== currentUser\.uid/);
  assert.match(stockUpdate, /quantity: newQuantity/);
  assert.match(stockUpdate, /hasOwnProperty\.call\(data, 'updatedAt'\)/);
  assert.doesNotMatch(
    stockUpdate,
    /feedName|unit:|supplier|cost|price|lowStockThreshold|userId|createdAt/,
  );
});

test('19 mobile stock controls stack and cards prevent horizontal overflow', () => {
  assert.match(
    inventorySource,
    /grid min-w-0 grid-cols-1 gap-2 border-t pt-4 sm:grid-cols-3/,
  );
  assert.match(
    inventorySource,
    /min-w-0 overflow-hidden rounded-lg border bg-white/,
  );
  assert.match(inventorySource, /className="w-full max-w-md overflow-hidden/);
});
