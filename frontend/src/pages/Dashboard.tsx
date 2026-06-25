import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { collection, getDocs } from 'firebase/firestore';
import { db } from '../firebase/config';
import { useAuth } from '../context/AuthContext';
import { Tractor, Syringe, Wheat, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts';
import type { HealthRecord, Livestock } from '../types';
import {
  getDerivedHealthStatus,
  getHealthBadgeStyle,
  parseDateValue,
  toText,
  type DerivedHealthStatus,
} from '../utils/livestockStatus';

interface FeedChartData {
  name: string;
  quantity: number;
  threshold: number;
}

interface RecentAnimalSummary {
  animal: Livestock;
  healthStatus: DerivedHealthStatus;
}

const Dashboard: React.FC = () => {
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalLivestock: 0,
    vaccinationsDue: 0,
    lowFeedAlerts: 0,
    sickAnimals: 0
  });

  const [feedData, setFeedData] = useState<FeedChartData[]>([]);
  const [recentAnimals, setRecentAnimals] = useState<RecentAnimalSummary[]>([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      const currentUserId = currentUser?.uid;
      if (!currentUserId) {
        setStats({
          totalLivestock: 0,
          vaccinationsDue: 0,
          lowFeedAlerts: 0,
          sickAnimals: 0,
        });
        setFeedData([]);
        setRecentAnimals([]);
        setLoading(false);
        return;
      }

      const fetchUserCollection = async <T extends { id: string }>(
        collectionName: string
      ): Promise<T[]> => {
        try {
          const snapshot = await getDocs(collection(db, collectionName));
          return snapshot.docs
            .map((document) => ({
              id: document.id,
              ...document.data(),
            }) as T)
            .filter((record) => {
              const userId = toText((record as Record<string, unknown>).userId);
              return !userId || userId === currentUserId;
            });
        } catch (collectionError) {
          console.error(`Error fetching ${collectionName}:`, collectionError);
          return [];
        }
      };

      try {
        const [animals, healthRecords, vaccinations, feedItems] = await Promise.all([
          fetchUserCollection<Livestock>('livestock'),
          fetchUserCollection<(Partial<HealthRecord> & Record<string, unknown>) & { id: string }>('healthRecords'),
          fetchUserCollection<Record<string, unknown> & { id: string }>('vaccinations'),
          fetchUserCollection<Record<string, unknown> & { id: string }>('feedInventory'),
        ]);

        const healthRecordsByAnimalId: Record<string, Array<Partial<HealthRecord> & Record<string, unknown>>> = {};
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
        const sickCount = animalsWithStatus.filter(
          ({ healthStatus }) =>
            healthStatus !== 'Healthy' && healthStatus !== 'No Health Records'
        ).length;
        
        // Sort for recent animals (newest first)
        animalsWithStatus.sort(
          (left, right) =>
            (parseDateValue(right.animal.createdAt)?.getTime() ?? 0) -
            (parseDateValue(left.animal.createdAt)?.getTime() ?? 0)
        );
        setRecentAnimals(animalsWithStatus.slice(0, 5));

        let dueCount = 0;
        vaccinations.forEach((record) => {
          const nextDueDate = parseDateValue(record.nextDueDate);
          if (nextDueDate && nextDueDate < new Date()) dueCount++;
        });

        let lowFeedCount = 0;
        const chartData: FeedChartData[] = [];
        feedItems.forEach((data) => {
          if (data.stockLevel === 'Low' || data.stockLevel === 'Out of Stock') lowFeedCount++;
          chartData.push({
            name: toText(data.feedName) || 'Feed item',
            quantity: Number(data.quantity) || 0,
            threshold: Number(data.lowStockThreshold) || 0
          });
        });
        setFeedData(chartData);

        setStats({
          totalLivestock: animals.length,
          vaccinationsDue: dueCount,
          lowFeedAlerts: lowFeedCount,
          sickAnimals: sickCount
        });

      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [currentUser]);

  if (loading) {
    return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Farm Overview</h1>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <Link to="/livestock" className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-green-100 rounded-md p-3">
                <Tractor className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Livestock</dt>
                  <dd className="text-2xl font-semibold text-gray-900">{stats.totalLivestock}</dd>
                </dl>
              </div>
            </div>
          </div>
        </Link>

        <Link to="/vaccinations" className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
          <div className="p-5">
            <div className="flex items-center">
              <div className={`flex-shrink-0 rounded-md p-3 ${stats.vaccinationsDue > 0 ? 'bg-red-100' : 'bg-green-100'}`}>
                <Syringe className={`h-6 w-6 ${stats.vaccinationsDue > 0 ? 'text-red-600' : 'text-green-600'}`} />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Vaccines Overdue</dt>
                  <dd className="text-2xl font-semibold text-gray-900">{stats.vaccinationsDue}</dd>
                </dl>
              </div>
            </div>
          </div>
        </Link>

        <Link to="/feed" className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
          <div className="p-5">
            <div className="flex items-center">
              <div className={`flex-shrink-0 rounded-md p-3 ${stats.lowFeedAlerts > 0 ? 'bg-yellow-100' : 'bg-green-100'}`}>
                <Wheat className={`h-6 w-6 ${stats.lowFeedAlerts > 0 ? 'text-yellow-600' : 'text-green-600'}`} />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Low Feed Alerts</dt>
                  <dd className="text-2xl font-semibold text-gray-900">{stats.lowFeedAlerts}</dd>
                </dl>
              </div>
            </div>
          </div>
        </Link>

        <Link to="/health" className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
          <div className="p-5">
            <div className="flex items-center">
              <div className={`flex-shrink-0 rounded-md p-3 ${stats.sickAnimals > 0 ? 'bg-red-100' : 'bg-green-100'}`}>
                <Activity className={`h-6 w-6 ${stats.sickAnimals > 0 ? 'text-red-600' : 'text-green-600'}`} />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Health Alerts</dt>
                  <dd className="text-2xl font-semibold text-gray-900">{stats.sickAnimals}</dd>
                </dl>
              </div>
            </div>
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Wheat className="w-5 h-5 mr-2 text-gray-400" />
            Feed Inventory Levels
          </h2>
          <div className="h-64 w-full">
            {feedData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={feedData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} />
                  <YAxis axisLine={false} tickLine={false} />
                  <RechartsTooltip cursor={{fill: 'transparent'}} />
                  <Bar dataKey="quantity" radius={[4, 4, 0, 0]}>
                    {feedData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.quantity <= entry.threshold ? '#ef4444' : '#10b981'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-500 border-2 border-dashed border-gray-200 rounded-md">
                No feed data available
              </div>
            )}
          </div>
        </div>

        {/* Recent Animals */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Tractor className="w-5 h-5 mr-2 text-gray-400" />
            Recently Added Livestock
          </h2>
          <div className="flow-root">
            <ul className="-my-5 divide-y divide-gray-200">
              {recentAnimals.length > 0 ? recentAnimals.map((animal) => (
                <li key={animal.animal.id} className="py-4">
                  <div className="flex items-center space-x-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {animal.animal.animalName}
                      </p>
                      <p className="text-sm text-gray-500 truncate">
                        ID: {animal.animal.animalId} &bull; {animal.animal.species}
                      </p>
                    </div>
                    <div>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getHealthBadgeStyle(animal.healthStatus)}`}>
                        {animal.healthStatus}
                      </span>
                    </div>
                  </div>
                </li>
              )) : (
                <li className="py-4 text-center text-gray-500">No livestock added yet</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
