import React, { useCallback, useEffect, useState } from 'react';
import {
  addDoc,
  collection,
  deleteDoc,
  doc,
  getDocs,
  serverTimestamp,
  updateDoc,
} from 'firebase/firestore';
import { db } from '../firebase/config';
import { useAuth } from '../context/AuthContext';
import type { HealthRecord, Livestock } from '../types';
import { Activity, Plus, Search } from 'lucide-react';

interface HealthRecordFormData {
  livestockId: string;
  diseaseType: string;
  symptoms: string;
  treatment: string;
  medicine: string;
  vetNotes: string;
  recoveryStatus: HealthRecord['recoveryStatus'];
}

const createInitialHealthRecordForm = (): HealthRecordFormData => ({
  livestockId: '',
  diseaseType: '',
  symptoms: '',
  treatment: '',
  medicine: '',
  vetNotes: '',
  recoveryStatus: 'In Treatment'
});

interface LivestockDropdownOption {
  id: string;
  animalName: string;
  animalId: string;
}

interface HealthRecordListItem {
  id: string;
  livestockId: string;
  animalName: string;
  diseaseType: string;
  symptoms: string;
  treatment: string;
  medicine: string;
  vetNotes: string;
  recoveryStatus: string;
  createdAt?: unknown;
  updatedAt?: unknown;
  userId: string;
}

interface StatusMessage {
  type: 'success' | 'error';
  text: string;
}

const toText = (value: unknown) => {
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number') return String(value);
  return '';
};

const parseDateValue = (value: unknown): Date | null => {
  if (!value) return null;

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value;
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

  if (typeof value === 'string' || typeof value === 'number') {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  return null;
};

const normalizeHealthRecord = (
  recordId: string,
  data: Partial<HealthRecord> & Record<string, unknown>
): HealthRecordListItem => ({
  id: recordId,
  livestockId: toText(data.livestockId),
  animalName: toText(data.animalName) || 'Unknown Animal',
  diseaseType: toText(data.diseaseType) || 'Unspecified Issue',
  symptoms: toText(data.symptoms),
  treatment: toText(data.treatment),
  medicine: toText(data.medicine),
  vetNotes: toText(data.vetNotes),
  recoveryStatus: toText(data.recoveryStatus) || 'In Treatment',
  createdAt: data.createdAt,
  updatedAt: data.updatedAt,
  userId: toText(data.userId),
});

const normalizeLivestockRecord = (recordId: string, data: Partial<Livestock> & Record<string, unknown>): LivestockDropdownOption | null => {
  const animalName =
    toText(data.animalName) ||
    toText(data.name);
  const animalId =
    toText(data.animalId) ||
    toText(data.tagId) ||
    toText(data.tagID);

  if (!animalName && !animalId) {
    return null;
  }

  return {
    id: recordId,
    animalName: animalName || 'Unnamed Animal',
    animalId: animalId || recordId,
  };
};

const createHealthRecordFormFromRecord = (
  record: HealthRecordListItem
): HealthRecordFormData => ({
  livestockId: record.livestockId,
  diseaseType: record.diseaseType,
  symptoms: record.symptoms,
  treatment: record.treatment,
  medicine: record.medicine,
  vetNotes: record.vetNotes,
  recoveryStatus: (record.recoveryStatus as HealthRecord['recoveryStatus']) || 'In Treatment',
});

const HealthTracking: React.FC = () => {
  const { currentUser } = useAuth();
  const [healthRecords, setHealthRecords] = useState<HealthRecordListItem[]>([]);
  const [livestockList, setLivestockList] = useState<LivestockDropdownOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState('');
  const [editingRecord, setEditingRecord] = useState<HealthRecordListItem | null>(null);
  const [statusMessage, setStatusMessage] = useState<StatusMessage | null>(null);

  const [formData, setFormData] = useState<HealthRecordFormData>(createInitialHealthRecordForm);

  const fetchHealthRecords = useCallback(async () => {
    const currentUserId = currentUser?.uid;
    if (!currentUserId) {
      setHealthRecords([]);
      setLoading(false);
      return;
    }

    setLoading(true);

    try {
      const snapshot = await getDocs(collection(db, 'healthRecords'));
      const nextHealthRecords = snapshot.docs
        .map((document) =>
          normalizeHealthRecord(
            document.id,
            document.data() as Partial<HealthRecord> & Record<string, unknown>
          )
        )
        .filter((record) => !record.userId || record.userId === currentUserId)
        .sort((left, right) => {
          const leftTime =
            parseDateValue(left.createdAt)?.getTime() ??
            parseDateValue(left.updatedAt)?.getTime() ??
            0;
          const rightTime =
            parseDateValue(right.createdAt)?.getTime() ??
            parseDateValue(right.updatedAt)?.getTime() ??
            0;
          return rightTime - leftTime;
        });

      setHealthRecords(nextHealthRecords);
      setError('');
    } catch (fetchError) {
      console.error('Failed to load health records:', fetchError);
      setHealthRecords([]);
      setError('Unable to load health records right now. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [currentUser?.uid]);

  const fetchLivestock = useCallback(async () => {
    const currentUserId = currentUser?.uid;
    if (!currentUserId) {
      setLivestockList([]);
      return;
    }

    try {
      const snapshot = await getDocs(collection(db, 'livestock'));
      const livestockData = snapshot.docs
        .map((document) => ({
          id: document.id,
          ...document.data(),
        }) as Partial<Livestock> & Record<string, unknown>)
        .filter((animal) => {
          const userId = toText(animal.userId);
          return !userId || userId === currentUserId;
        })
        .map((animal) => normalizeLivestockRecord(animal.id as string, animal))
        .filter((animal): animal is LivestockDropdownOption => animal !== null);

      setLivestockList(livestockData);
    } catch (fetchError) {
      console.error('Failed to load livestock:', fetchError);
      setLivestockList([]);
    }
  }, [currentUser?.uid]);

  useEffect(() => {
    const currentUserId = currentUser?.uid;
    if (!currentUserId) {
      setHealthRecords([]);
      setLivestockList([]);
      setLoading(false);
      return;
    }

    void fetchHealthRecords();
    void fetchLivestock();
  }, [currentUser?.uid, fetchHealthRecords, fetchLivestock]);

  const handleCloseForm = () => {
    setShowAddForm(false);
    setEditingRecord(null);
    setFormData(createInitialHealthRecordForm());
  };

  const handleEdit = (record: HealthRecordListItem) => {
    setEditingRecord(record);
    setFormData(createHealthRecordFormFromRecord(record));
    setShowAddForm(true);
    setStatusMessage(null);
  };

  const handleDelete = async (record: HealthRecordListItem) => {
    if (!record.id) return;
    if (!window.confirm('Are you sure you want to delete this health record?')) return;

    try {
      await deleteDoc(doc(db, 'healthRecords', record.id));

      if (editingRecord?.id === record.id) {
        handleCloseForm();
      }

      await fetchHealthRecords();
      setStatusMessage({
        type: 'success',
        text: 'Health record deleted successfully.',
      });
    } catch (deleteError) {
      console.error('Error deleting health record: ', deleteError);
      setStatusMessage({
        type: 'error',
        text: 'Failed to delete health record.',
      });
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;

    const animal = livestockList.find(a => a.id === formData.livestockId);
    if (!animal && !editingRecord) {
      setStatusMessage({
        type: 'error',
        text: 'Please select an animal before saving this health record.',
      });
      return;
    }

    const animalName = animal?.animalName || editingRecord?.animalName || 'Unknown Animal';

    try {
      if (editingRecord?.id) {
        await updateDoc(doc(db, 'healthRecords', editingRecord.id), {
          ...formData,
          animalName,
          userId: currentUser.uid,
          updatedAt: serverTimestamp(),
        });
        setStatusMessage({
          type: 'success',
          text: 'Health record updated successfully.',
        });
      } else {
        await addDoc(collection(db, 'healthRecords'), {
          ...formData,
          animalName,
          userId: currentUser.uid,
          createdAt: serverTimestamp(),
          updatedAt: serverTimestamp(),
        });
        setStatusMessage({
          type: 'success',
          text: 'Health record added successfully.',
        });
      }

      handleCloseForm();
      await fetchHealthRecords();
    } catch (error) {
      console.error("Error adding health record: ", error);
      setStatusMessage({
        type: 'error',
        text: editingRecord
          ? 'Failed to update health record.'
          : 'Failed to add health record.',
      });
    }
  };

  const searchValue = searchTerm.toLowerCase();
  const filteredRecords = healthRecords.filter((record) =>
    record.animalName.toLowerCase().includes(searchValue) ||
    record.diseaseType.toLowerCase().includes(searchValue) ||
    record.symptoms.toLowerCase().includes(searchValue) ||
    record.treatment.toLowerCase().includes(searchValue) ||
    record.medicine.toLowerCase().includes(searchValue)
  );

  const hasAnimals = livestockList.length > 0;
  const canSubmit = hasAnimals || Boolean(editingRecord);
  const activeLivestockIds = new Set(livestockList.map((animal) => animal.id));
  const selectedAnimalMissing =
    Boolean(editingRecord?.livestockId) &&
    !livestockList.some((animal) => animal.id === formData.livestockId);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <Activity className="h-6 w-6 mr-2 text-green-600" />
          Health Tracking
        </h1>
        <button
          onClick={() => {
            if (showAddForm) {
              handleCloseForm();
              return;
            }

            setShowAddForm(true);
            setEditingRecord(null);
            setFormData(createInitialHealthRecordForm());
            setStatusMessage(null);
          }}
          className="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
        >
          {showAddForm ? 'Cancel' : <><Plus className="-ml-1 mr-2 h-5 w-5" /> Add Record</>}
        </button>
      </div>

      {statusMessage ? (
        <div
          className={`border-l-4 p-4 ${
            statusMessage.type === 'success'
              ? 'bg-green-50 border-green-400'
              : 'bg-red-50 border-red-400'
          }`}
        >
          <p
            className={`text-sm ${
              statusMessage.type === 'success' ? 'text-green-700' : 'text-red-700'
            }`}
          >
            {statusMessage.text}
          </p>
        </div>
      ) : null}

      {showAddForm && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-green-200">
          <h2 className="text-lg font-medium mb-4">
            {editingRecord ? 'Edit Health Record' : 'New Health Record'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Animal</label>
                <select
                  required
                  name="livestockId"
                  value={formData.livestockId}
                  onChange={handleChange}
                  disabled={!canSubmit}
                  className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
                >
                  <option value="">
                    {hasAnimals
                      ? 'Select an animal...'
                      : editingRecord
                        ? 'Animal unavailable'
                        : 'No animals available'}
                  </option>
                  {selectedAnimalMissing ? (
                    <option value={formData.livestockId}>
                      {(editingRecord?.animalName || 'Unknown Animal')} (Animal deleted)
                    </option>
                  ) : null}
                  {livestockList.map(a => (
                    <option key={a.id} value={a.id}>{a.animalName} ({a.animalId})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Disease/Issue Type</label>
                <input required type="text" name="diseaseType" value={formData.diseaseType} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Recovery Status</label>
                <select name="recoveryStatus" value={formData.recoveryStatus} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm">
                  <option>In Treatment</option>
                  <option>Under Treatment</option>
                  <option>Sick</option>
                  <option>Recovered</option>
                  <option>Recovering</option>
                  <option>Healthy</option>
                  <option>Critical</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Medicine Prescribed</label>
                <input type="text" name="medicine" value={formData.medicine} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Symptoms</label>
                <textarea required name="symptoms" value={formData.symptoms} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" rows={2}></textarea>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Treatment Plan</label>
                <textarea required name="treatment" value={formData.treatment} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" rows={2}></textarea>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Vet Notes</label>
                <textarea name="vetNotes" value={formData.vetNotes} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" rows={2}></textarea>
              </div>
            </div>

            <div className="flex justify-end">
              <button type="submit" disabled={!canSubmit} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:bg-green-400">
                {editingRecord ? 'Update Health Record' : 'Save Health Record'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-green-500 focus:border-green-500 sm:text-sm"
            placeholder="Search animal name or disease..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredRecords.length > 0 ? filteredRecords.map((record) => (
            <div key={record.id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-5">
                {record.livestockId && !activeLivestockIds.has(record.livestockId) && (
                  <div className="mb-3 text-xs font-medium text-gray-500">
                    Archived record - animal deleted
                  </div>
                )}
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{record.animalName || 'Unknown Animal'}</h3>
                    <p className="text-sm font-medium text-red-600">{record.diseaseType || 'Unspecified Issue'}</p>
                  </div>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    record.recoveryStatus === 'Recovered' ? 'bg-green-100 text-green-800' : 
                    record.recoveryStatus === 'Critical' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {record.recoveryStatus || 'In Treatment'}
                  </span>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <h4 className="text-xs font-medium text-gray-500 uppercase">Symptoms</h4>
                    <p className="mt-1 text-sm text-gray-900">{record.symptoms || 'Not provided'}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-xs font-medium text-gray-500 uppercase">Treatment</h4>
                      <p className="mt-1 text-sm text-gray-900">{record.treatment || 'Not provided'}</p>
                    </div>
                    <div>
                      <h4 className="text-xs font-medium text-gray-500 uppercase">Medicine</h4>
                      <p className="mt-1 text-sm text-gray-900">{record.medicine || 'None specified'}</p>
                    </div>
                  </div>
                  {record.vetNotes && (
                    <div className="bg-gray-50 p-3 rounded text-sm text-gray-700 italic border-l-4 border-gray-300">
                      " {record.vetNotes} "
                    </div>
                  )}
                </div>

                <div className="mt-4 flex justify-end gap-3 border-t border-gray-100 pt-4">
                  <button
                    type="button"
                    onClick={() => handleEdit(record)}
                    className="text-sm font-medium text-green-700 hover:text-green-800"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDelete(record)}
                    className="text-sm font-medium text-red-600 hover:text-red-700"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )) : (
            <div className="col-span-full text-center py-12 bg-white rounded-lg border border-gray-200 border-dashed">
              <p className="text-gray-500">
                {healthRecords.length === 0 ? 'No health records found.' : 'No health records match your search.'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HealthTracking;
