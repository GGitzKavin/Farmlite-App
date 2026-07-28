import React, { useCallback, useEffect, useState } from 'react';
import { addDoc, collection, getDocs, serverTimestamp } from 'firebase/firestore';
import { db } from '../../firebase/config';
import { useAuth } from '../../context/AuthContext';
import type { HealthRecord, Livestock, Vaccination } from '../../types';
import { Link } from 'react-router-dom';
import { Eye, Plus, Search } from 'lucide-react';
import AnimalEntryForm, { type AnimalFormSubmission } from './AnimalEntryForm';
import {
  getDerivedHealthStatus,
  getHealthBadgeStyle,
  parseDateValue,
  getVaccinationStatus,
  getVaccinationStatusStyle,
  getDisplaySpecies,
  getSpeciesFilterValue,
  toText,
  type DerivedHealthStatus,
  type DerivedVaccinationStatus,
} from '../../utils/livestockStatus';

interface LivestockTableProps {
  searchTerm: string;
  filterSpecies: string;
  onSuccess: (msg: string) => void;
}

const LivestockTable: React.FC<LivestockTableProps> = ({ searchTerm, filterSpecies, onSuccess }) => {
  const { currentUser } = useAuth();
  const [livestockList, setLivestockList] = useState<Livestock[]>([]);
  const [healthStatusByAnimalId, setHealthStatusByAnimalId] = useState<Record<string, DerivedHealthStatus>>({});
  const [vaccinationStatusByAnimalId, setVaccinationStatusByAnimalId] = useState<Record<string, DerivedVaccinationStatus>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchLivestock = useCallback(async () => {
    const currentUserId = currentUser?.uid;
    if (!currentUserId) {
      setLivestockList([]);
      setLoading(false);
      return;
    }

    setLoading(true);

    try {
      const snapshot = await getDocs(collection(db, 'livestock'));
      const data = snapshot.docs
        .map((document) => ({ id: document.id, ...document.data() }) as Livestock)
        .filter((animal) => !animal.userId || animal.userId === currentUserId)
        .sort((left, right) => {
          const leftTime = parseDateValue(left.createdAt)?.getTime() ?? 0;
          const rightTime = parseDateValue(right.createdAt)?.getTime() ?? 0;
          return rightTime - leftTime;
        });

      setLivestockList(data);
    } catch (error) {
      console.error('Error loading livestock: ', error);
      setLivestockList([]);
    } finally {
      setLoading(false);
    }
  }, [currentUser?.uid]);

  const fetchHealthStatuses = useCallback(async () => {
    const currentUserId = currentUser?.uid;
    if (!currentUserId) {
      setHealthStatusByAnimalId({});
      return;
    }

    try {
      const snapshot = await getDocs(collection(db, 'healthRecords'));
      const recordsByAnimalId: Record<string, Array<Partial<HealthRecord> & Record<string, unknown>>> = {};

      snapshot.forEach((document) => {
        const data = document.data() as Partial<HealthRecord> & Record<string, unknown>;
        const userId = toText(data.userId);
        const livestockId = toText(data.livestockId);
        if ((userId && userId !== currentUserId) || !livestockId) return;

        if (!recordsByAnimalId[livestockId]) {
          recordsByAnimalId[livestockId] = [];
        }

        recordsByAnimalId[livestockId].push({
          id: document.id,
          ...data,
        });
      });

      const nextStatuses: Record<string, DerivedHealthStatus> = {};
      Object.entries(recordsByAnimalId).forEach(([livestockId, records]) => {
        nextStatuses[livestockId] = getDerivedHealthStatus(records, 'Healthy');
      });

      setHealthStatusByAnimalId(nextStatuses);
    } catch (error) {
      console.error('Error loading health records: ', error);
      setHealthStatusByAnimalId({});
    }
  }, [currentUser?.uid]);

  const fetchVaccinationStatuses = useCallback(async () => {
    const currentUserId = currentUser?.uid;
    if (!currentUserId) {
      setVaccinationStatusByAnimalId({});
      return;
    }

    try {
      const snapshot = await getDocs(collection(db, 'vaccinations'));
      const recordsByAnimalId: Record<string, Array<Partial<Vaccination> & Record<string, unknown>>> = {};

      snapshot.forEach((document) => {
        const data = document.data() as Partial<Vaccination> & Record<string, unknown>;
        const userId = toText(data.userId);
        const livestockId = toText(data.livestockId);
        if ((userId && userId !== currentUserId) || !livestockId) return;

        if (!recordsByAnimalId[livestockId]) {
          recordsByAnimalId[livestockId] = [];
        }

        recordsByAnimalId[livestockId].push({
          id: document.id,
          ...data,
        });
      });

      const nextStatuses: Record<string, DerivedVaccinationStatus> = {};
      Object.entries(recordsByAnimalId).forEach(([livestockId, records]) => {
        nextStatuses[livestockId] = getVaccinationStatus(records);
      });

      setVaccinationStatusByAnimalId(nextStatuses);
    } catch (error) {
      console.error('Error loading vaccinations: ', error);
      setVaccinationStatusByAnimalId({});
    }
  }, [currentUser?.uid]);

  useEffect(() => {
    // Mount-time Firestore fetches; each sets loading/error state before its
    // network await, the standard fetch-on-mount pattern.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchLivestock();
    void fetchHealthStatuses();
    void fetchVaccinationStatuses();
  }, [fetchLivestock, fetchHealthStatuses, fetchVaccinationStatuses]);

  const handleSave = async (data: AnimalFormSubmission) => {
    if (!currentUser?.uid) return;
    setSaving(true);
    try {
      await addDoc(collection(db, 'livestock'), {
        ...data,
        userId: currentUser.uid,
        createdAt: serverTimestamp()
      });
      await fetchLivestock();
      onSuccess('Animal added successfully!');
    } catch (err) {
      console.error("Error saving livestock:", err);
    } finally {
      setSaving(false);
    }
  };

  const filteredList = livestockList.filter(animal => {
    const name = animal?.animalName?.toLowerCase() || '';
    const id = animal?.animalId?.toLowerCase() || '';
    const breed = animal?.breed?.toLowerCase() || '';
    const species = animal?.species || '';

    const matchesSearch =
      name.includes(searchTerm.toLowerCase()) ||
      id.includes(searchTerm.toLowerCase()) ||
      breed.includes(searchTerm.toLowerCase());
    const matchesFilter = filterSpecies
      ? getSpeciesFilterValue(species) === filterSpecies
      : true;

    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        <p className="text-gray-500 font-medium animate-pulse">Fetching your livestock records...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 rounded-xl bg-[#fefae0]/50 p-1 sm:p-3">
      {/* Persistent Inline Entry Card */}
      <section className="overflow-hidden rounded-xl border border-[#dda15e]/70 bg-white shadow-sm">
        <div className="border-b border-[#dda15e]/40 bg-[#fefae0] p-4">
          <h2 className="flex items-center gap-2 text-lg font-bold text-[#283618]">
            <Plus className="w-5 h-5 text-[#606c38]" /> Add New Animal
          </h2>
        </div>
        <AnimalEntryForm onSave={handleSave} saving={saving} />
      </section>

      {/* Livestock Grid */}
      {filteredList.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredList.map((animal) => {
            const healthStatus = healthStatusByAnimalId[animal.id] ?? 'Healthy';
            const vaccinationStatus = vaccinationStatusByAnimalId[animal.id] ?? 'No records';

            return (
              <div key={animal?.id} className="bg-[#dda15e] overflow-hidden shadow-sm rounded-xl border border-[#bc6c25]/60 hover:shadow-md transition-all duration-200">
                <div className="p-4">
                  <div className="flex justify-between items-start gap-3">
                    <div className="min-w-0">
                      <h3 className="truncate text-lg font-semibold text-[#2f1d0c]">{animal?.animalName}</h3>
                      <p className="text-sm text-[#4a2d11]">ID: {animal?.animalId}</p>
                    </div>
                    <span className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-semibold ${getHealthBadgeStyle(healthStatus)}`}>
                      {healthStatus}
                    </span>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-xs text-[#5a3614] font-medium uppercase tracking-wide">Livestock</p>
                      <p className="mt-0.5 text-sm text-[#2f1d0c] font-semibold">{getDisplaySpecies(animal?.species)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-[#5a3614] font-medium uppercase tracking-wide">Breed</p>
                      <p className="mt-0.5 text-sm text-[#2f1d0c] font-medium">{animal?.breed}</p>
                    </div>
                    <div className="rounded-lg bg-[#fefae0]/80 p-2.5">
                      <p className="text-xs text-[#5a3614] font-medium uppercase tracking-wide">Age / Weight</p>
                      <p className="mt-0.5 text-sm text-[#2f1d0c] font-medium">{animal?.age} mo / {animal?.weight} kg</p>
                    </div>
                    <div className="rounded-lg bg-[#fefae0]/80 p-2.5">
                      <p className="text-xs text-[#5a3614] font-medium uppercase tracking-wide">Vaccines</p>
                      <p className={`mt-0.5 text-sm font-semibold ${getVaccinationStatusStyle(vaccinationStatus)}`}>
                        {vaccinationStatus}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-[#bc6c25]/15 px-4 py-3 border-t border-[#bc6c25]/40">
                  <Link to={`/livestock/${animal?.id}`} className="inline-flex w-full items-center justify-center rounded-lg border border-[#606c38]/30 bg-[#fefae0] px-3 py-2 text-center text-sm font-medium text-[#3f250d] transition-colors hover:bg-white">
                    <Eye className="mr-2 h-4 w-4" />
                    View Full Profile
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-20 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
          <div className="bg-white p-4 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4 shadow-sm">
            <Search className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-900">No livestock found</h3>
          <p className="text-gray-500 mt-1 max-w-xs mx-auto">
            {searchTerm || filterSpecies
              ? "We couldn't find any livestock matching your current search criteria."
              : "You haven't added any livestock yet. Use the form above to add your first animal."}
          </p>
        </div>
      )}
    </div>
  );
};

export default LivestockTable;
