import type { HealthRecord, Vaccination } from '../types';

export type DerivedHealthStatus =
  | 'Critical'
  | 'Sick'
  | 'Under Treatment'
  | 'Recovering'
  | 'Healthy'
  | 'No Health Records';

export type DerivedVaccinationStatus =
  | 'Overdue'
  | 'Due Soon'
  | 'Up to date'
  | 'No records';

const healthStatusMap: Record<string, DerivedHealthStatus> = {
  critical: 'Critical',
  sick: 'Sick',
  'in treatment': 'Under Treatment',
  'under treatment': 'Under Treatment',
  quarantined: 'Under Treatment',
  recovering: 'Recovering',
  recovered: 'Healthy',
  healthy: 'Healthy',
};

const startOfDay = (date: Date) =>
  new Date(date.getFullYear(), date.getMonth(), date.getDate());

export const toText = (value: unknown) => {
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return '';
};

export const parseDateValue = (value: unknown): Date | null => {
  if (!value) return null;

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value;
  }

  if (typeof value === 'string') {
    const isoDateMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (isoDateMatch) {
      const [, year, month, day] = isoDateMatch;
      return new Date(Number(year), Number(month) - 1, Number(day));
    }

    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  if (typeof value === 'number') {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  if (typeof value === 'object') {
    const timestampLike = value as {
      toDate?: () => Date;
      seconds?: number;
    };

    if (typeof timestampLike.toDate === 'function') {
      const parsed = timestampLike.toDate();
      return Number.isNaN(parsed.getTime()) ? null : parsed;
    }

    if (typeof timestampLike.seconds === 'number') {
      return new Date(timestampLike.seconds * 1000);
    }
  }

  return null;
};

export const calculateAgeInMonths = (birthDateString: string) => {
  if (!birthDateString) return null;

  const birthDate = new Date(birthDateString);
  if (Number.isNaN(birthDate.getTime())) return null;

  const today = new Date();
  let months = (today.getFullYear() - birthDate.getFullYear()) * 12;
  months += today.getMonth() - birthDate.getMonth();

  if (today.getDate() < birthDate.getDate()) {
    months -= 1;
  }

  return Math.max(0, months);
};

const getRecordTime = (record: { createdAt?: unknown; updatedAt?: unknown }) =>
  parseDateValue(record.updatedAt)?.getTime() ??
  parseDateValue(record.createdAt)?.getTime() ??
  0;

export const getLatestHealthRecord = <
  T extends Pick<Partial<HealthRecord>, 'createdAt' | 'updatedAt'>,
>(
  records: T[]
) =>
  [...records].sort((left, right) => getRecordTime(right) - getRecordTime(left))[0] ??
  null;

export const normalizeHealthStatus = (
  status: unknown,
  fallback: DerivedHealthStatus = 'Healthy'
): DerivedHealthStatus => {
  const normalizedStatus = toText(status).toLowerCase();
  if (!normalizedStatus) return fallback;

  return healthStatusMap[normalizedStatus] ?? fallback;
};

export const getDerivedHealthStatus = <
  T extends Pick<
    Partial<HealthRecord>,
    'createdAt' | 'updatedAt' | 'recoveryStatus'
  >,
>(
  records: T[],
  fallback: DerivedHealthStatus = 'Healthy'
): DerivedHealthStatus => {
  const latestRecord = getLatestHealthRecord(records);
  if (!latestRecord) return fallback;
  return normalizeHealthStatus(latestRecord.recoveryStatus, fallback);
};

export const getHealthBadgeStyle = (
  status: DerivedHealthStatus,
  variant: 'badge' | 'card' = 'badge'
) => {
  const styles =
    status === 'Critical' || status === 'Sick'
      ? {
          badge: 'bg-red-100 text-red-800',
          card: 'bg-red-50 border-red-200 text-red-900',
        }
      : status === 'Under Treatment'
        ? {
            badge: 'bg-yellow-100 text-yellow-800',
            card: 'bg-yellow-50 border-yellow-200 text-yellow-900',
          }
        : status === 'Recovering'
          ? {
              badge: 'bg-blue-100 text-blue-800',
              card: 'bg-blue-50 border-blue-200 text-blue-900',
            }
          : status === 'No Health Records'
            ? {
                badge: 'bg-gray-100 text-gray-700',
                card: 'bg-gray-50 border-gray-200 text-gray-900',
              }
            : {
                badge: 'bg-green-100 text-green-800',
                card: 'bg-green-50 border-green-200 text-green-900',
              };

  return styles[variant];
};

export const getVaccinationStatus = <
  T extends Pick<Partial<Vaccination>, 'nextDueDate'>,
>(
  records: T[],
  upcomingWindowDays = 7
): DerivedVaccinationStatus => {
  if (records.length === 0) return 'No records';

  const today = startOfDay(new Date());
  const dueSoonBoundary = startOfDay(
    new Date(today.getFullYear(), today.getMonth(), today.getDate() + upcomingWindowDays)
  );
  let hasDueSoon = false;

  for (const record of records) {
    const dueDate = parseDateValue(record.nextDueDate);
    if (!dueDate) continue;

    const normalizedDueDate = startOfDay(dueDate);

    if (normalizedDueDate < today) {
      return 'Overdue';
    }

    if (normalizedDueDate <= dueSoonBoundary) {
      hasDueSoon = true;
    }
  }

  if (hasDueSoon) return 'Due Soon';
  return 'Up to date';
};

export const getVaccinationStatusStyle = (
  status: DerivedVaccinationStatus,
  variant: 'text' | 'badge' | 'card' = 'text'
) => {
  const styles =
    status === 'Overdue'
      ? {
          text: 'text-red-600',
          badge: 'bg-red-100 text-red-800',
          card: 'bg-red-50 border-red-200 text-red-900',
        }
      : status === 'Due Soon'
        ? {
            text: 'text-amber-600',
            badge: 'bg-amber-100 text-amber-800',
            card: 'bg-amber-50 border-amber-200 text-amber-900',
          }
        : status === 'No records'
          ? {
              text: 'text-gray-500',
              badge: 'bg-gray-100 text-gray-700',
              card: 'bg-gray-50 border-gray-200 text-gray-900',
            }
          : {
              text: 'text-green-600',
              badge: 'bg-green-100 text-green-800',
              card: 'bg-green-50 border-green-200 text-green-900',
            };

  return styles[variant];
};
