import type { Batch } from '../types';

const batchCreatedTime = (batch: Batch): number => {
  if (batch.createdAt instanceof Date) {
    return batch.createdAt.getTime();
  }

  if (
    batch.createdAt &&
    typeof batch.createdAt === 'object' &&
    typeof batch.createdAt.toDate === 'function'
  ) {
    return batch.createdAt.toDate().getTime();
  }

  return 0;
};

export const reconcileOwnedBatches = (
  batches: Batch[],
  currentUserId: string
): Batch[] =>
  batches
    .filter((batch) => batch.userId === currentUserId)
    .sort((left, right) => batchCreatedTime(right) - batchCreatedTime(left));

export const upsertOwnedBatch = (
  batches: Batch[],
  savedBatch: Batch,
  currentUserId: string
): Batch[] => {
  if (savedBatch.userId !== currentUserId) {
    return reconcileOwnedBatches(batches, currentUserId);
  }

  return reconcileOwnedBatches(
    [savedBatch, ...batches.filter((batch) => batch.id !== savedBatch.id)],
    currentUserId
  );
};
