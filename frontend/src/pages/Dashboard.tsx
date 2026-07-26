import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { collection, getDocs } from 'firebase/firestore';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  CalendarDays,
  ClipboardPlus,
  Layers3,
  PlusCircle,
  Tractor,
  Wheat,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { db } from '../firebase/config';
import { useAuth } from '../context/AuthContext';
import type { Batch, HealthRecord, Livestock } from '../types';
import {
  getDerivedHealthStatus,
  getDisplaySpecies,
  parseDateValue,
  toText,
} from '../utils/livestockStatus';

interface FeedChartData {
  name: string;
  quantity: number;
  threshold: number;
}

interface RecentActivityItem {
  id: string;
  kind: 'Livestock added' | 'Batch created';
  title: string;
  detail: string;
  occurredAt: Date;
  path: string;
}

interface DashboardVaccinationRecord extends Record<string, unknown> {
  id: string;
  vaccineName?: unknown;
  nextDueDate?: unknown;
  livestockId?: unknown;
  batchId?: unknown;
  animalName?: unknown;
  batchName?: unknown;
}

interface UpcomingVaccination {
  id: string;
  targetName: string;
  vaccineName: string;
  dueDate: Date;
  dueDateLabel: string;
  status: 'Due within 7 days' | 'Due within 30 days';
  path: string;
}

interface LivestockOverviewItem {
  label: string;
  count: number;
}

interface AttentionCounts {
  overdueVaccinations: number;
  dueSoonVaccinations: number;
  healthAlerts: number;
  incompleteProfiles: number;
  lowFeedAlerts: number;
}

const emptyAttention: AttentionCounts = {
  overdueVaccinations: 0,
  dueSoonVaccinations: 0,
  healthAlerts: 0,
  incompleteProfiles: 0,
  lowFeedAlerts: 0,
};

const formatChartLabel = (value: unknown): string => {
  const label = String(value ?? '');
  return label.length > 13 ? `${label.slice(0, 12)}…` : label;
};

const startOfDay = (date: Date): Date =>
  new Date(date.getFullYear(), date.getMonth(), date.getDate());

const addDays = (date: Date, days: number): Date =>
  new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);

const hasCriticalProfileGap = (animal: Livestock): boolean =>
  !toText(animal.animalName) ||
  !toText(animal.animalId) ||
  !toText(animal.species) ||
  !toText(animal.breed) ||
  !Number.isFinite(Number(animal.age)) ||
  !Number.isFinite(Number(animal.weight));

const quickActions = [
  { label: 'Add Livestock', path: '/livestock', icon: PlusCircle },
  { label: 'Create Batch', path: '/livestock?view=batch', icon: Layers3 },
  { label: 'Record Vaccination', path: '/vaccinations', icon: ClipboardPlus },
  { label: 'Generate Feed Recommendation', path: '/ai-feed', icon: Bot },
] as const;

const Dashboard: React.FC = () => {
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [loadWarning, setLoadWarning] = useState('');
  const [attention, setAttention] = useState<AttentionCounts>(emptyAttention);
  const [upcomingVaccinations, setUpcomingVaccinations] = useState<
    UpcomingVaccination[]
  >([]);
  const [livestockOverview, setLivestockOverview] = useState<
    LivestockOverviewItem[]
  >([]);
  const [batchOverview, setBatchOverview] = useState({
    totalBatches: 0,
    recordedHeadCount: 0,
  });
  const [feedData, setFeedData] = useState<FeedChartData[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivityItem[]>([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      const currentUserId = currentUser?.uid;
      if (!currentUserId) {
        setAttention(emptyAttention);
        setUpcomingVaccinations([]);
        setLivestockOverview([]);
        setBatchOverview({ totalBatches: 0, recordedHeadCount: 0 });
        setFeedData([]);
        setRecentActivity([]);
        setLoadWarning('');
        setLoading(false);
        return;
      }

      setLoading(true);
      setLoadWarning('');
      const failedCollections: string[] = [];

      const fetchUserCollection = async <T extends { id: string }>(
        collectionName: string
      ): Promise<T[]> => {
        try {
          const snapshot = await getDocs(collection(db, collectionName));
          return snapshot.docs
            .map(
              (document) =>
                ({
                  id: document.id,
                  ...document.data(),
                }) as T
            )
            .filter((record) => {
              const userId = toText(
                (record as Record<string, unknown>).userId
              );
              return !userId || userId === currentUserId;
            });
        } catch (collectionError) {
          console.error(`Error fetching ${collectionName}:`, collectionError);
          failedCollections.push(collectionName);
          return [];
        }
      };

      try {
        const [
          animals,
          healthRecords,
          vaccinations,
          feedItems,
          batches,
        ] = await Promise.all([
          fetchUserCollection<Livestock>('livestock'),
          fetchUserCollection<
            (Partial<HealthRecord> & Record<string, unknown>) & { id: string }
          >('healthRecords'),
          fetchUserCollection<DashboardVaccinationRecord>('vaccinations'),
          fetchUserCollection<Record<string, unknown> & { id: string }>(
            'feedInventory'
          ),
          fetchUserCollection<Batch>('batches'),
        ]);

        const healthRecordsByAnimalId: Record<
          string,
          Array<Partial<HealthRecord> & Record<string, unknown>>
        > = {};
        healthRecords.forEach((record) => {
          const livestockId = toText(record.livestockId);
          if (!livestockId) return;
          if (!healthRecordsByAnimalId[livestockId]) {
            healthRecordsByAnimalId[livestockId] = [];
          }
          healthRecordsByAnimalId[livestockId].push(record);
        });

        const animalsWithStatus = animals.map((animal) => ({
          animal,
          healthStatus: getDerivedHealthStatus(
            healthRecordsByAnimalId[animal.id] ?? [],
            'Healthy'
          ),
        }));
        const healthAlertCount = animalsWithStatus.filter(
          ({ healthStatus }) =>
            healthStatus !== 'Healthy' &&
            healthStatus !== 'No Health Records'
        ).length;

        const overviewCounts = new Map<string, number>();
        animals.forEach((animal) => {
          const label = getDisplaySpecies(animal.species) || 'Other Livestock';
          overviewCounts.set(label, (overviewCounts.get(label) ?? 0) + 1);
        });
        setLivestockOverview(
          Array.from(overviewCounts.entries())
            .map(([label, count]) => ({ label, count }))
            .sort(
              (left, right) =>
                right.count - left.count ||
                left.label.localeCompare(right.label)
            )
        );

        const animalById = new Map(
          animals.map((animal) => [animal.id, animal])
        );
        const batchById = new Map(
          batches.map((batch) => [batch.id, batch])
        );
        const today = startOfDay(new Date());
        const sevenDayBoundary = addDays(today, 7);
        const thirtyDayBoundary = addDays(today, 30);
        let overdueVaccinationCount = 0;
        const upcoming: UpcomingVaccination[] = [];

        vaccinations.forEach((record) => {
          const parsedDueDate = parseDateValue(record.nextDueDate);
          if (!parsedDueDate) return;
          const dueDate = startOfDay(parsedDueDate);
          const livestockId = toText(record.livestockId);
          const batchId = toText(record.batchId);
          const linkedAnimal = livestockId
            ? animalById.get(livestockId)
            : undefined;
          const linkedBatch = batchId ? batchById.get(batchId) : undefined;

          if (livestockId && !linkedAnimal) return;
          if (batchId && !linkedBatch) return;

          if (dueDate < today) {
            overdueVaccinationCount += 1;
            return;
          }
          if (dueDate > thirtyDayBoundary) return;

          const targetName =
            toText(record.animalName) ||
            toText(linkedAnimal?.animalName) ||
            toText(record.batchName) ||
            (linkedBatch ? `Batch: ${linkedBatch.batchName}` : '') ||
            'Livestock record';

          upcoming.push({
            id: record.id,
            targetName,
            vaccineName: toText(record.vaccineName) || 'Vaccination',
            dueDate,
            dueDateLabel: dueDate.toLocaleDateString(),
            status:
              dueDate <= sevenDayBoundary
                ? 'Due within 7 days'
                : 'Due within 30 days',
            path: livestockId ? `/livestock/${livestockId}` : '/vaccinations',
          });
        });
        upcoming.sort(
          (left, right) => left.dueDate.getTime() - right.dueDate.getTime()
        );
        setUpcomingVaccinations(upcoming.slice(0, 6));

        let lowFeedCount = 0;
        const chartData: FeedChartData[] = [];
        feedItems.forEach((record) => {
          const quantity = Number(record.quantity);
          const threshold = Number(record.lowStockThreshold);
          const finiteQuantity = Number.isFinite(quantity) ? quantity : 0;
          const finiteThreshold = Number.isFinite(threshold) ? threshold : 0;
          if (finiteQuantity <= finiteThreshold) {
            lowFeedCount += 1;
          }
          chartData.push({
            name: toText(record.feedName) || 'Feed item',
            quantity: finiteQuantity,
            threshold: finiteThreshold,
          });
        });
        setFeedData(chartData);

        setBatchOverview({
          totalBatches: batches.length,
          recordedHeadCount: batches.reduce(
            (total, batch) =>
              total +
              (Number.isFinite(Number(batch.headCount))
                ? Number(batch.headCount)
                : 0),
            0
          ),
        });

        const recentItems: RecentActivityItem[] = [];
        animals.forEach((animal) => {
          const occurredAt = parseDateValue(animal.createdAt);
          if (!occurredAt) return;
          recentItems.push({
            id: `livestock-${animal.id}`,
            kind: 'Livestock added',
            title: animal.animalName || 'Livestock record',
            detail: `ID: ${animal.animalId || 'Unavailable'} • ${getDisplaySpecies(
              animal.species
            )}`,
            occurredAt,
            path: `/livestock/${animal.id}`,
          });
        });
        batches.forEach((batch) => {
          const occurredAt = parseDateValue(batch.createdAt);
          if (!occurredAt) return;
          recentItems.push({
            id: `batch-${batch.id}`,
            kind: 'Batch created',
            title: batch.batchName || 'Batch record',
            detail: `${getDisplaySpecies(batch.species)} • ${batch.headCount} recorded`,
            occurredAt,
            path: '/livestock?view=batch',
          });
        });
        recentItems.sort(
          (left, right) =>
            right.occurredAt.getTime() - left.occurredAt.getTime()
        );
        setRecentActivity(recentItems.slice(0, 6));

        setAttention({
          overdueVaccinations: overdueVaccinationCount,
          dueSoonVaccinations: upcoming.length,
          healthAlerts: healthAlertCount,
          incompleteProfiles: animals.filter(hasCriticalProfileGap).length,
          lowFeedAlerts: lowFeedCount,
        });

        if (failedCollections.length > 0) {
          setLoadWarning(
            `Some dashboard data could not be loaded: ${failedCollections.join(
              ', '
            )}. Available information is shown.`
          );
        }
      } catch (dashboardError) {
        console.error('Error preparing dashboard data:', dashboardError);
        setLoadWarning(
          'Some dashboard information could not be prepared. Please refresh and try again.'
        );
      } finally {
        setLoading(false);
      }
    };

    void fetchDashboardData();
  }, [currentUser]);

  if (loading) {
    return (
      <div role="status" className="flex items-center justify-center py-16">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-[#606c38]" />
        <span className="sr-only">Loading dashboard</span>
      </div>
    );
  }

  const attentionItems = [
    {
      label: 'Overdue vaccinations',
      count: attention.overdueVaccinations,
      path: '/vaccinations',
      tone: 'warning',
    },
    {
      label: 'Vaccinations due within 30 days',
      count: attention.dueSoonVaccinations,
      path: '/vaccinations',
      tone: 'information',
    },
    {
      label: 'Livestock with health alerts',
      count: attention.healthAlerts,
      path: '/health',
      tone: 'warning',
    },
    {
      label: 'Incomplete livestock profiles',
      count: attention.incompleteProfiles,
      path: '/livestock',
      tone: 'information',
    },
    {
      label: 'Low feed items',
      count: attention.lowFeedAlerts,
      path: '/feed',
      tone: 'warning',
    },
  ] as const;
  const attentionTotal = attentionItems.reduce(
    (total, item) => total + item.count,
    0
  );

  return (
    <div className="w-full min-w-0 space-y-5 xl:space-y-6">
      <h1 className="text-2xl font-bold text-[#283618] lg:text-3xl">
        Farm Overview
      </h1>

      {loadWarning ? (
        <div
          role="alert"
          className="rounded-xl border border-[#dda15e] bg-[#fefae0] px-5 py-4 text-sm text-[#7c3f12]"
        >
          {loadWarning}
        </div>
      ) : null}

      <section aria-labelledby="quick-actions-title">
        <h2 id="quick-actions-title" className="text-lg font-bold text-[#283618]">
          Quick Actions
        </h2>
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.label}
                to={action.path}
                className="group flex min-w-0 items-center justify-between rounded-xl border border-[#dda15e]/60 bg-white p-4 text-[#283618] shadow-sm transition hover:border-[#606c38] hover:bg-[#fefae0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
              >
                <span className="flex min-w-0 items-center gap-3">
                  <span className="rounded-lg bg-[#606c38]/10 p-2 text-[#606c38]">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <span className="break-words text-sm font-semibold">{action.label}</span>
                </span>
                <ArrowRight className="h-4 w-4 shrink-0 text-[#bc6c25] transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
              </Link>
            );
          })}
        </div>
      </section>

      <div className="grid min-w-0 grid-cols-1 gap-5 xl:grid-cols-2">
        <DashboardSection
          title="Attention Required"
          icon={<AlertTriangle className="h-5 w-5" />}
          headingSuffix={attentionTotal > 0 ? `${attentionTotal} items` : undefined}
        >
          {attentionTotal === 0 ? (
            <EmptyState message="No livestock require attention." />
          ) : (
            <ul className="space-y-3">
              {attentionItems.map((item) => (
                <li key={item.label}>
                  <Link
                    to={item.path}
                    className="flex min-w-0 items-center justify-between gap-3 rounded-lg border border-gray-200 p-3 hover:bg-[#fefae0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
                  >
                    <span className="min-w-0 break-words text-sm font-medium text-gray-700">
                      {item.label}
                    </span>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${
                        item.tone === 'warning'
                          ? 'bg-[#bc6c25]/15 text-[#7c3f12]'
                          : 'bg-[#dda15e]/25 text-[#283618]'
                      }`}
                    >
                      {item.count}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </DashboardSection>

        <DashboardSection
          title="Upcoming Vaccinations"
          icon={<CalendarDays className="h-5 w-5" />}
        >
          {upcomingVaccinations.length === 0 ? (
            <EmptyState message="No vaccinations are due soon." />
          ) : (
            <ul className="divide-y divide-gray-200">
              {upcomingVaccinations.map((vaccination) => (
                <li key={vaccination.id} className="py-3 first:pt-0 last:pb-0">
                  <Link
                    to={vaccination.path}
                    className="block rounded-lg p-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
                  >
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <p className="break-words text-sm font-semibold text-[#283618]">
                          {vaccination.targetName}
                        </p>
                        <p className="break-words text-sm text-gray-600">
                          {vaccination.vaccineName}
                        </p>
                      </div>
                      <span
                        className={`w-fit shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${
                          vaccination.status === 'Due within 7 days'
                            ? 'bg-[#bc6c25]/15 text-[#7c3f12]'
                            : 'bg-[#dda15e]/25 text-[#283618]'
                        }`}
                      >
                        {vaccination.status}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-gray-500">
                      Due{' '}
                      <time dateTime={vaccination.dueDate.toISOString()}>
                        {vaccination.dueDateLabel}
                      </time>
                    </p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </DashboardSection>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-5 xl:grid-cols-2">
        <DashboardSection
          title="Livestock Overview"
          icon={<Tractor className="h-5 w-5" />}
        >
          {livestockOverview.length === 0 ? (
            <EmptyState message="No livestock records are available." />
          ) : (
            <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {livestockOverview.map((item) => (
                <li
                  key={item.label}
                  className="flex items-center justify-between rounded-lg border border-[#dda15e]/40 bg-[#fefae0] p-4"
                >
                  <span className="break-words text-sm font-medium text-[#283618]">{item.label}</span>
                  <span className="ml-3 text-xl font-bold text-[#606c38]">{item.count}</span>
                </li>
              ))}
            </ul>
          )}
        </DashboardSection>

        <DashboardSection
          title="Batch Overview"
          icon={<Layers3 className="h-5 w-5" />}
        >
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-[#dda15e]/40 bg-[#fefae0] p-4">
              <dt className="text-sm font-medium text-gray-600">Total batches</dt>
              <dd className="mt-1 text-2xl font-bold text-[#606c38]">{batchOverview.totalBatches}</dd>
            </div>
            <div className="rounded-lg border border-[#dda15e]/40 bg-[#fefae0] p-4">
              <dt className="text-sm font-medium text-gray-600">Recorded batch headcount</dt>
              <dd className="mt-1 text-2xl font-bold text-[#606c38]">{batchOverview.recordedHeadCount}</dd>
            </div>
          </dl>
          <Link
            to="/livestock?view=batch"
            className="mt-4 inline-flex items-center font-semibold text-[#606c38] hover:text-[#283618] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
          >
            Open Batch Management
            <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
          </Link>
        </DashboardSection>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-5 xl:grid-cols-2">
        <DashboardSection
          title="Feed Inventory Levels"
          icon={<Wheat className="h-5 w-5" />}
        >
          <div
            role="img"
            aria-label="Feed inventory quantities compared with low-stock thresholds"
            className="h-56 w-full min-w-0 sm:h-64"
          >
            {feedData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={feedData}
                  margin={{ top: 5, right: 8, left: 0, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12 }}
                    tickFormatter={formatChartLabel}
                    tickMargin={8}
                    minTickGap={12}
                    height={40}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12 }}
                    width={44}
                  />
                  <RechartsTooltip cursor={{ fill: 'transparent' }} />
                  <Bar dataKey="quantity" radius={[4, 4, 0, 0]}>
                    {feedData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={
                          entry.quantity <= entry.threshold
                            ? '#bc6c25'
                            : '#606c38'
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message="No feed inventory data is available." />
            )}
          </div>
        </DashboardSection>

        <DashboardSection
          title="Recent Activity"
          icon={<Activity className="h-5 w-5" />}
        >
          {recentActivity.length === 0 ? (
            <EmptyState message="No recent livestock or batch activity is available." />
          ) : (
            <ul className="divide-y divide-gray-200">
              {recentActivity.map((activity) => (
                <li key={activity.id} className="py-3 first:pt-0 last:pb-0">
                  <Link
                    to={activity.path}
                    className="flex min-w-0 items-center gap-3 rounded-lg p-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold uppercase tracking-wide text-[#606c38]">
                        {activity.kind}
                      </p>
                      <p className="mt-1 truncate text-sm font-semibold text-[#283618]">
                        {activity.title}
                      </p>
                      <p className="truncate text-sm text-gray-500">{activity.detail}</p>
                    </div>
                    <time
                      dateTime={activity.occurredAt.toISOString()}
                      className="shrink-0 text-xs text-gray-500"
                    >
                      {activity.occurredAt.toLocaleDateString()}
                    </time>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </DashboardSection>
      </div>
    </div>
  );
};

interface DashboardSectionProps {
  title: string;
  icon: React.ReactNode;
  headingSuffix?: string;
  children: React.ReactNode;
}

const DashboardSection: React.FC<DashboardSectionProps> = ({
  title,
  icon,
  headingSuffix,
  children,
}) => {
  const headingId = `dashboard-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
  return (
    <section
      aria-labelledby={headingId}
      className="min-w-0 overflow-hidden rounded-xl border border-[#dda15e]/60 bg-white p-4 shadow-sm sm:p-5"
    >
      <div className="mb-4 flex min-w-0 items-center justify-between gap-3">
        <h2 id={headingId} className="flex min-w-0 items-center text-lg font-bold text-[#283618]">
          <span className="mr-2 shrink-0 text-[#606c38]" aria-hidden="true">
            {icon}
          </span>
          <span className="break-words">{title}</span>
        </h2>
        {headingSuffix ? (
          <span className="shrink-0 rounded-full bg-[#dda15e]/25 px-2.5 py-1 text-xs font-semibold text-[#283618]">
            {headingSuffix}
          </span>
        ) : null}
      </div>
      {children}
    </section>
  );
};

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="flex min-h-24 items-center justify-center rounded-lg border border-dashed border-[#dda15e] bg-[#fefae0] p-5 text-center text-sm text-gray-700">
    {message}
  </div>
);

export default Dashboard;
