import React, { useEffect, useState } from 'react';
import { collection, getDocs } from 'firebase/firestore';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bell,
  Calendar,
  Clock3,
  ShieldAlert,
  Syringe,
  Wheat,
} from 'lucide-react';
import { db } from '../firebase/config';
import { useAuth } from '../context/AuthContext';

type NotificationType =
  | 'vaccination_overdue'
  | 'vaccination_upcoming'
  | 'low_feed'
  | 'health_alert';
type NotificationPriority = 'High' | 'Medium' | 'Low';

interface FarmNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  relatedName?: string;
  dateText?: string;
  priority: NotificationPriority;
  actionLabel?: string;
  actionPath?: string;
  sortDate?: Date | null;
}

interface LivestockRecord {
  id: string;
  animalId?: string;
  animalName?: string;
  species?: string;
  healthStatus?: string;
}

interface BatchRecord {
  id: string;
  batchName?: string;
  species?: string;
  healthStatus?: string;
}

interface VaccinationRecord {
  id: string;
  vaccineName?: string;
  vaccinationDate?: string;
  nextDueDate?: string | null;
  livestockId?: string;
  batchId?: string;
  targetType?: string;
  animalName?: string;
  batchName?: string;
  notes?: string;
}

interface FeedInventoryRecord {
  id: string;
  feedName?: string;
  quantity?: number | string;
  lowStockThreshold?: number | string;
  targetAnimal?: string;
  stockLevel?: string;
}

interface HealthRecordEntry {
  id: string;
  livestockId?: string;
  animalName?: string;
  diseaseType?: string;
  symptoms?: string;
  treatment?: string;
  medicine?: string;
  vetNotes?: string;
  recoveryStatus?: string;
  createdAt?: unknown;
}

interface NotificationsSnapshot {
  overdueVaccinations: FarmNotification[];
  upcomingVaccinations: FarmNotification[];
  lowFeedAlerts: FarmNotification[];
  healthAlerts: FarmNotification[];
  urgentAlerts: FarmNotification[];
  upcomingReminders: FarmNotification[];
  recentHealthUpdates: FarmNotification[];
}

const emptyNotifications: NotificationsSnapshot = {
  overdueVaccinations: [],
  upcomingVaccinations: [],
  lowFeedAlerts: [],
  healthAlerts: [],
  urgentAlerts: [],
  upcomingReminders: [],
  recentHealthUpdates: [],
};

const priorityStyles: Record<NotificationPriority, string> = {
  High: 'bg-red-100 text-red-700 border border-red-200',
  Medium: 'bg-amber-100 text-amber-700 border border-amber-200',
  Low: 'bg-sky-100 text-sky-700 border border-sky-200',
};

const sectionEmptyMessages = {
  urgent: 'No urgent alerts right now.',
  upcoming: 'No upcoming reminders for the next few days.',
  recent: 'No recent health updates to review.',
};

const toText = (value: unknown) => {
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  return '';
};

const parseDateValue = (value: unknown): Date | null => {
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

  if (typeof value === 'object' && value !== null) {
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

const startOfDay = (date: Date) =>
  new Date(date.getFullYear(), date.getMonth(), date.getDate());

const addDays = (date: Date, days: number) => {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
};

const formatDate = (value: unknown) => {
  const parsed = parseDateValue(value);
  if (!parsed) return 'Date unavailable';

  return parsed.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

const toNumber = (value: unknown): number | null => {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

const getPriorityRank = (priority: NotificationPriority) => {
  if (priority === 'High') return 0;
  if (priority === 'Medium') return 1;
  return 2;
};

const sortByPriorityThenDate = (notifications: FarmNotification[]) =>
  [...notifications].sort((left, right) => {
    const priorityDifference =
      getPriorityRank(left.priority) - getPriorityRank(right.priority);

    if (priorityDifference !== 0) return priorityDifference;

    const leftTime = left.sortDate?.getTime() ?? 0;
    const rightTime = right.sortDate?.getTime() ?? 0;
    return rightTime - leftTime;
  });

const sortByDateAscending = (notifications: FarmNotification[]) =>
  [...notifications].sort((left, right) => {
    const leftTime = left.sortDate?.getTime() ?? Number.MAX_SAFE_INTEGER;
    const rightTime = right.sortDate?.getTime() ?? Number.MAX_SAFE_INTEGER;
    return leftTime - rightTime;
  });

const sortByDateDescending = (notifications: FarmNotification[]) =>
  [...notifications].sort((left, right) => {
    const leftTime = left.sortDate?.getTime() ?? 0;
    const rightTime = right.sortDate?.getTime() ?? 0;
    return rightTime - leftTime;
  });

const getNotificationIcon = (type: NotificationType) => {
  switch (type) {
    case 'vaccination_overdue':
      return <ShieldAlert className="h-5 w-5 text-red-600" />;
    case 'vaccination_upcoming':
      return <Calendar className="h-5 w-5 text-amber-600" />;
    case 'low_feed':
      return <Wheat className="h-5 w-5 text-amber-700" />;
    case 'health_alert':
    default:
      return <Activity className="h-5 w-5 text-rose-600" />;
  }
};

const getNotificationIconContainer = (type: NotificationType) => {
  switch (type) {
    case 'vaccination_overdue':
      return 'bg-red-50 border border-red-100';
    case 'vaccination_upcoming':
      return 'bg-amber-50 border border-amber-100';
    case 'low_feed':
      return 'bg-amber-50 border border-amber-100';
    case 'health_alert':
    default:
      return 'bg-rose-50 border border-rose-100';
  }
};

const SummaryCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  count: number;
  description: string;
  accentClass: string;
  backgroundClass: string;
}> = ({ icon, title, count, description, accentClass, backgroundClass }) => (
  <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <p className="mt-2 text-3xl font-bold text-gray-900">{count}</p>
      </div>
      <div className={`rounded-xl p-3 ${backgroundClass}`}>{icon}</div>
    </div>
    <p className={`mt-4 text-sm ${accentClass}`}>{description}</p>
  </div>
);

const NotificationRow: React.FC<{
  notification: FarmNotification;
  onAction: (path?: string) => void;
}> = ({ notification, onAction }) => (
  <div className="px-5 py-4">
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div className="flex min-w-0 gap-4">
        <div
          className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl ${getNotificationIconContainer(notification.type)}`}
        >
          {getNotificationIcon(notification.type)}
        </div>

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-900">
              {notification.title}
            </h3>
            {notification.relatedName ? (
              <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">
                {notification.relatedName}
              </span>
            ) : null}
          </div>

          <p className="mt-1 text-sm leading-6 text-gray-600">
            {notification.message}
          </p>

          {notification.dateText ? (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-gray-500">
              <Clock3 className="h-3.5 w-3.5" />
              <span>{notification.dateText}</span>
            </div>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center lg:flex-col lg:items-end">
        <span
          className={`inline-flex w-fit items-center rounded-full px-2.5 py-1 text-xs font-semibold ${priorityStyles[notification.priority]}`}
        >
          {notification.priority}
        </span>

        <button
          type="button"
          onClick={() => onAction(notification.actionPath)}
          disabled={!notification.actionPath}
          className="inline-flex items-center justify-center rounded-lg border border-green-200 bg-green-50 px-3.5 py-2 text-sm font-semibold text-green-700 transition hover:bg-green-100 disabled:cursor-not-allowed disabled:border-gray-200 disabled:bg-gray-100 disabled:text-gray-400"
        >
          {notification.actionLabel ?? 'Review'}
          <ArrowRight className="ml-2 h-4 w-4" />
        </button>
      </div>
    </div>
  </div>
);

const NotificationSection: React.FC<{
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  notifications: FarmNotification[];
  emptyMessage: string;
  onAction: (path?: string) => void;
}> = ({ title, subtitle, icon, notifications, emptyMessage, onAction }) => (
  <section className="rounded-xl border border-gray-200 bg-white shadow-sm">
    <div className="flex flex-col gap-3 border-b border-gray-100 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-green-50 p-2 text-green-600">{icon}</div>
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        </div>
        <p className="mt-2 text-sm text-gray-500">{subtitle}</p>
      </div>
      <span className="inline-flex w-fit items-center rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-600">
        {notifications.length} item{notifications.length === 1 ? '' : 's'}
      </span>
    </div>

    {notifications.length > 0 ? (
      <div className="divide-y divide-gray-100">
        {notifications.map((notification) => (
          <NotificationRow
            key={notification.id}
            notification={notification}
            onAction={onAction}
          />
        ))}
      </div>
    ) : (
      <div className="px-5 py-10 text-center">
        <Bell className="mx-auto h-10 w-10 text-gray-300" />
        <p className="mt-4 text-sm text-gray-500">{emptyMessage}</p>
      </div>
    )}
  </section>
);

const Notifications: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState<NotificationsSnapshot>(emptyNotifications);

  useEffect(() => {
    if (authLoading) return;

    if (!currentUser) {
      setData(emptyNotifications);
      setLoading(false);
      return;
    }

    let isMounted = true;

    const fetchNotifications = async () => {
      setLoading(true);
      setError('');

      try {
        const fetchUserCollection = async <T extends { id: string }>(
          collectionName: string
        ): Promise<T[]> => {
          try {
            const snapshot = await getDocs(collection(db, collectionName));

            return snapshot.docs.map(
              (document) =>
                ({
                  id: document.id,
                  ...document.data(),
                }) as T
            ).filter((record) => {
              const userId = toText((record as Record<string, unknown>).userId);
              return !userId || userId === currentUser.uid;
            });
          } catch (collectionError) {
            console.error(
              `Error fetching ${collectionName} for notifications:`,
              collectionError
            );
            return [];
          }
        };

        const [
          livestock,
          batches,
          vaccinations,
          feedItems,
          healthRecords,
        ] = await Promise.all([
          fetchUserCollection<LivestockRecord>('livestock'),
          fetchUserCollection<BatchRecord>('batches'),
          fetchUserCollection<VaccinationRecord>('vaccinations'),
          fetchUserCollection<FeedInventoryRecord>('feedInventory'),
          fetchUserCollection<HealthRecordEntry>('healthRecords'),
        ]);

        const livestockById = new Map(livestock.map((animal) => [animal.id, animal]));
        const batchById = new Map(batches.map((batch) => [batch.id, batch]));

        const today = startOfDay(new Date());
        const sevenDaysFromToday = addDays(today, 7);

        const overdueVaccinations: FarmNotification[] = [];
        const upcomingVaccinations: FarmNotification[] = [];
        const lowFeedAlerts: FarmNotification[] = [];
        const healthAlerts: FarmNotification[] = [];
        const urgentHealthAlerts: FarmNotification[] = [];
        const healthFollowUps: FarmNotification[] = [];

        vaccinations.forEach((record) => {
          const dueDate = parseDateValue(record.nextDueDate);
          if (!dueDate) return;

          const normalizedDueDate = startOfDay(dueDate);
          const linkedAnimal = record.livestockId
            ? livestockById.get(record.livestockId)
            : undefined;
          const linkedBatch = record.batchId ? batchById.get(record.batchId) : undefined;
          if (record.livestockId && !linkedAnimal) return;
          if (record.batchId && !linkedBatch) return;
          const vaccineName = toText(record.vaccineName) || 'Vaccination';
          const animalName = toText(record.animalName);
          const batchName = toText(record.batchName);
          const targetType = toText(record.targetType);
          const animalId = toText(linkedAnimal?.animalId);

          const relatedName =
            animalName ||
            toText(linkedAnimal?.animalName) ||
            batchName ||
            toText(linkedBatch?.batchName) ||
            (targetType === 'Batch' || record.batchId ? 'Batch record' : 'Animal record');

          const targetDetails =
            animalId && (record.livestockId || linkedAnimal?.id)
              ? `${relatedName} (${animalId})`
              : relatedName;

          const actionPath = record.livestockId
            ? `/livestock/${record.livestockId}`
            : '/vaccinations';
          const actionLabel = record.livestockId ? 'View Animal' : 'View Vaccination';

          const dateLabel = formatDate(normalizedDueDate);

          if (normalizedDueDate < today) {
            overdueVaccinations.push({
              id: `overdue-${record.id}`,
              type: 'vaccination_overdue',
              title: `${vaccineName} overdue`,
              message: `${vaccineName} was due on ${dateLabel} for ${targetDetails}.`,
              relatedName,
              dateText: `Due ${dateLabel}`,
              priority: 'High',
              actionLabel,
              actionPath,
              sortDate: normalizedDueDate,
            });
            return;
          }

          if (normalizedDueDate <= sevenDaysFromToday) {
            const timeUntilDue = Math.max(
              0,
              Math.ceil(
                (normalizedDueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
              )
            );

            upcomingVaccinations.push({
              id: `upcoming-${record.id}`,
              type: 'vaccination_upcoming',
              title: `${vaccineName} due soon`,
              message:
                timeUntilDue === 0
                  ? `${vaccineName} is due today for ${targetDetails}.`
                  : `${vaccineName} is due in ${timeUntilDue} day${timeUntilDue === 1 ? '' : 's'} for ${targetDetails}.`,
              relatedName,
              dateText: `Due ${dateLabel}`,
              priority: timeUntilDue <= 3 ? 'Medium' : 'Low',
              actionLabel,
              actionPath,
              sortDate: normalizedDueDate,
            });
          }
        });

        feedItems.forEach((record) => {
          const quantity = toNumber(record.quantity);
          const threshold = toNumber(record.lowStockThreshold);
          const feedName = toText(record.feedName) || 'Feed item';
          const targetAnimal = toText(record.targetAnimal);

          if (quantity === null || threshold === null || quantity > threshold) {
            return;
          }

          lowFeedAlerts.push({
            id: `feed-${record.id}`,
            type: 'low_feed',
            title: `${feedName} is running low`,
            message: `${feedName} is at ${quantity} units, which is at or below the low-stock threshold of ${threshold}${targetAnimal ? ` for ${targetAnimal}` : ''}.`,
            relatedName: targetAnimal || feedName || 'Feed inventory',
            dateText: `Current stock ${quantity} / threshold ${threshold}`,
            priority: quantity === 0 ? 'High' : 'Medium',
            actionLabel: 'View Feed',
            actionPath: '/feed',
          });
        });

        const activeHealthStatuses = new Set([
          'in treatment',
          'sick',
          'critical',
          'under treatment',
          'recovering',
        ]);
        const urgentHealthStatuses = new Set(['critical', 'sick']);

        healthRecords
          .sort((left, right) => {
            const leftTime = parseDateValue(left.createdAt)?.getTime() ?? 0;
            const rightTime = parseDateValue(right.createdAt)?.getTime() ?? 0;
            return rightTime - leftTime;
          })
          .forEach((record) => {
            if (record.livestockId && !livestockById.has(record.livestockId)) return;

            const statusText = toText(record.recoveryStatus) || 'Needs review';
            const statusKey = statusText.toLowerCase();
            if (!activeHealthStatuses.has(statusKey)) return;

            const createdAt = parseDateValue(record.createdAt);
            const actionPath = '/health-tracking';
            const actionLabel = 'Review';
            const symptomSummary =
              toText(record.symptoms) ||
              toText(record.treatment) ||
              toText(record.medicine) ||
              toText(record.vetNotes) ||
              'Monitor this health record and review the latest notes.';
            const diseaseType = toText(record.diseaseType) || 'Health issue';
            const animalName = toText(record.animalName) || 'Health record';
            const medicineName = toText(record.medicine);

            const baseNotification: FarmNotification = {
              id: `health-${record.id}`,
              type: 'health_alert',
              title: `${diseaseType} - ${statusText}`,
              message: symptomSummary,
              relatedName: animalName,
              dateText: createdAt
                ? `Updated ${formatDate(createdAt)}`
                : 'Date unavailable',
              priority: urgentHealthStatuses.has(statusKey)
                ? 'High'
                : statusKey === 'recovering'
                  ? 'Low'
                  : 'Medium',
              actionLabel,
              actionPath,
              sortDate: createdAt,
            };

            healthAlerts.push(baseNotification);

            if (urgentHealthStatuses.has(statusKey)) {
              urgentHealthAlerts.push({
                ...baseNotification,
                id: `urgent-${record.id}`,
              });
            }

            if (
              statusKey === 'in treatment' ||
              statusKey === 'under treatment' ||
              statusKey === 'recovering'
            ) {
              healthFollowUps.push({
                ...baseNotification,
                id: `follow-up-${record.id}`,
                title: `${animalName === 'Health record' ? 'Animal' : animalName} follow-up`,
                message: `Review ${diseaseType.toLowerCase()} and confirm treatment progress${medicineName ? ` for ${medicineName}` : ''}.`,
                priority: statusKey === 'recovering' ? 'Low' : 'Medium',
                actionLabel: 'Review',
              });
            }
          });

        const urgentAlerts = sortByPriorityThenDate([
          ...urgentHealthAlerts,
          ...sortByDateAscending(overdueVaccinations),
          ...lowFeedAlerts,
        ]);
        const upcomingReminders = [
          ...sortByDateAscending(upcomingVaccinations),
          ...sortByDateDescending(healthFollowUps),
        ];
        const recentHealthUpdates = sortByDateDescending(healthAlerts);

        if (isMounted) {
          setData({
            overdueVaccinations: sortByDateAscending(overdueVaccinations),
            upcomingVaccinations: sortByDateAscending(upcomingVaccinations),
            lowFeedAlerts: sortByPriorityThenDate(lowFeedAlerts),
            healthAlerts: recentHealthUpdates,
            urgentAlerts,
            upcomingReminders,
            recentHealthUpdates,
          });
        }
      } catch (fetchError) {
        console.error('Error fetching notifications:', fetchError);
        if (isMounted) {
          setData(emptyNotifications);
          setError(
            'Some notification data could not be loaded. Showing available alerts only.'
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchNotifications();

    return () => {
      isMounted = false;
    };
  }, [authLoading, currentUser]);

  const handleAction = (path?: string) => {
    if (!path) return;
    navigate(path);
  };

  const hasNotifications =
    data.urgentAlerts.length > 0 ||
    data.upcomingReminders.length > 0 ||
    data.recentHealthUpdates.length > 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-2xl font-bold text-gray-900">
            <Bell className="h-7 w-7 text-green-600" />
            Notifications
          </h1>
          <p className="mt-1 text-sm text-gray-500">Farm alerts and reminders</p>
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
          {error}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          icon={<Syringe className="h-6 w-6 text-red-600" />}
          title="Overdue Vaccinations"
          count={data.overdueVaccinations.length}
          description="Vaccinations that need attention immediately."
          accentClass="text-red-600"
          backgroundClass="bg-red-50"
        />
        <SummaryCard
          icon={<Calendar className="h-6 w-6 text-amber-600" />}
          title="Upcoming Vaccinations"
          count={data.upcomingVaccinations.length}
          description="Due within the next 7 days."
          accentClass="text-amber-600"
          backgroundClass="bg-amber-50"
        />
        <SummaryCard
          icon={<Wheat className="h-6 w-6 text-amber-700" />}
          title="Low Feed Alerts"
          count={data.lowFeedAlerts.length}
          description="Feed items at or below their safety threshold."
          accentClass="text-amber-700"
          backgroundClass="bg-amber-50"
        />
        <SummaryCard
          icon={<Activity className="h-6 w-6 text-rose-600" />}
          title="Health Alerts"
          count={data.healthAlerts.length}
          description="Animals that still need monitoring or care."
          accentClass="text-rose-600"
          backgroundClass="bg-rose-50"
        />
      </div>

      {!hasNotifications ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white px-6 py-16 text-center shadow-sm">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-50">
            <Bell className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="mt-5 text-xl font-semibold text-gray-900">
            No notifications yet
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-gray-500">
            Your farm alerts and reminders will appear here when action is required.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          <NotificationSection
            title="Urgent Alerts"
            subtitle="Overdue vaccinations, low feed stock, and critical health issues that need fast action."
            icon={<AlertTriangle className="h-5 w-5" />}
            notifications={data.urgentAlerts}
            emptyMessage={sectionEmptyMessages.urgent}
            onAction={handleAction}
          />

          <NotificationSection
            title="Upcoming Reminders"
            subtitle="Vaccinations due soon and active treatment follow-ups to keep on track."
            icon={<Calendar className="h-5 w-5" />}
            notifications={data.upcomingReminders}
            emptyMessage={sectionEmptyMessages.upcoming}
            onAction={handleAction}
          />

          <NotificationSection
            title="Recent Health Updates"
            subtitle="Latest non-recovered health records so you can monitor progress at a glance."
            icon={<Activity className="h-5 w-5" />}
            notifications={data.recentHealthUpdates}
            emptyMessage={sectionEmptyMessages.recent}
            onAction={handleAction}
          />
        </div>
      )}
    </div>
  );
};

export default Notifications;
