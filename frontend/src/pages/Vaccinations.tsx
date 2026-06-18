import React, { useEffect, useState } from 'react';
import { collection, query, where, getDocs, addDoc, doc, deleteDoc, updateDoc, serverTimestamp } from 'firebase/firestore';
import { db } from '../firebase/config';
import { useAuth } from '../context/AuthContext';
import type { Vaccination, Livestock, Batch } from '../types';
import { Syringe, Plus, Search, Calendar, Eye, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const VaccinationManagement: React.FC = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [vaccinations, setVaccinations] = useState<Vaccination[]>([]);
  const [livestockList, setLivestockList] = useState<Livestock[]>([]);
  const [batchesList, setBatchesList] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [targetType, setTargetType] = useState<'Individual Animal' | 'Batch'>('Individual Animal');
  const [selectedAnimalId, setSelectedAnimalId] = useState('');
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [editingRecord, setEditingRecord] = useState<Vaccination | null>(null);

  const getTodayDateString = () => {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  };

  const [formData, setFormData] = useState({
    vaccineName: '',
    vaccinationDate: getTodayDateString(),
    nextDueDate: '',
    reminderStatus: 'Active',
    notes: ''
  });

  useEffect(() => {
    const fetchData = async () => {
      if (!currentUser) return;
      
      try {
        // Fetch Vaccinations
        const qVac = query(
          collection(db, 'vaccinations'),
          where('userId', '==', currentUser.uid)
        );
        const vacSnapshot = await getDocs(qVac);
        const vacData: Vaccination[] = [];
        vacSnapshot.forEach((doc) => vacData.push({ id: doc.id, ...doc.data() } as Vaccination));
        // Sort by next due date manually as it's a string, or simple date sorting
        vacData.sort((a, b) => {
          if (!a.nextDueDate) return 1;
          if (!b.nextDueDate) return -1;
          return new Date(a.nextDueDate).getTime() - new Date(b.nextDueDate).getTime();
        });
        setVaccinations(vacData);

        // Fetch Livestock for dropdown
        const qLs = query(
          collection(db, 'livestock'),
          where('userId', '==', currentUser.uid)
        );
        const lsSnapshot = await getDocs(qLs);
        const lsData: Livestock[] = [];
        lsSnapshot.forEach((doc) => lsData.push({ id: doc.id, ...doc.data() } as Livestock));
        setLivestockList(lsData);

        // Fetch Batches for dropdown
        const qBatches = query(
          collection(db, 'batches'),
          where('userId', '==', currentUser.uid)
        );
        const batchesSnapshot = await getDocs(qBatches);
        const batchesData: Batch[] = [];
        batchesSnapshot.forEach((doc) => batchesData.push({ id: doc.id, ...doc.data() } as Batch));
        setBatchesList(batchesData);

      } catch (error) {
        console.error("Error fetching data: ", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [currentUser]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleCloseForm = () => {
    setShowAddForm(false);
    setEditingRecord(null);
    setFormData({
      vaccineName: '',
      vaccinationDate: getTodayDateString(),
      nextDueDate: '',
      reminderStatus: 'Active',
      notes: ''
    });
    setSelectedAnimalId('');
    setSelectedBatchId('');
    setTargetType('Individual Animal');
  };

  const handleEdit = (vac: Vaccination) => {
    setEditingRecord(vac);
    setTargetType(vac.targetType || (vac.batchId ? 'Batch' : 'Individual Animal'));
    setSelectedAnimalId(vac.livestockId || '');
    setSelectedBatchId(vac.batchId || '');
    setFormData({
      vaccineName: vac.vaccineName,
      vaccinationDate: vac.vaccinationDate,
      nextDueDate: vac.nextDueDate || '',
      reminderStatus: vac.reminderStatus || 'Active',
      notes: vac.notes || ''
    });
    setShowAddForm(true);
  };

  const handleDelete = async (recordId: string) => {
    if (!window.confirm("Are you sure you want to delete this vaccination record?")) return;

    try {
      await deleteDoc(doc(db, 'vaccinations', recordId));
      setVaccinations(prev => prev.filter(vac => vac.id !== recordId));
    } catch (error) {
      console.error("Error deleting record: ", error);
      alert("Failed to delete vaccination record.");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;
    
    try {
      const payload: any = {
        vaccineName: formData.vaccineName,
        vaccinationDate: formData.vaccinationDate,
        nextDueDate: formData.nextDueDate || null,
        notes: formData.notes,
        reminderStatus: formData.reminderStatus,
        targetType: targetType,
        userId: currentUser.uid
      };

      if (targetType === 'Individual Animal') {
        payload.livestockId = selectedAnimalId;
        payload.batchId = '';
      } else {
        payload.batchId = selectedBatchId;
        payload.livestockId = '';
      }

      if (editingRecord && editingRecord.id) {
        // Update existing document
        await updateDoc(doc(db, 'vaccinations', editingRecord.id), payload);
        
        setVaccinations(prev => 
          prev.map(vac => vac.id === editingRecord.id ? { ...vac, ...payload } : vac)
            .sort((a, b) => {
              if (!a.nextDueDate) return 1;
              if (!b.nextDueDate) return -1;
              return new Date(a.nextDueDate).getTime() - new Date(b.nextDueDate).getTime();
            })
        );
      } else {
        // Create new document
        payload.createdAt = serverTimestamp();
        const docRef = await addDoc(collection(db, 'vaccinations'), payload);
        
        setVaccinations(prev => [...prev, { id: docRef.id, ...payload } as Vaccination].sort((a, b) => {
          if (!a.nextDueDate) return 1;
          if (!b.nextDueDate) return -1;
          return new Date(a.nextDueDate).getTime() - new Date(b.nextDueDate).getTime();
        }));
      }

      // Automatically update the health status of the target to "Under Treatment"
      try {
        if (targetType === 'Individual Animal' && selectedAnimalId) {
          await updateDoc(doc(db, 'livestock', selectedAnimalId), {
            healthStatus: 'Under Treatment'
          });
        } else if (targetType === 'Batch' && selectedBatchId) {
          await updateDoc(doc(db, 'batches', selectedBatchId), {
            healthStatus: 'Under Treatment'
          });
        }
      } catch (healthUpdateError) {
        console.error("Non-critical error: Failed to auto-update target health status", healthUpdateError);
      }

      handleCloseForm();
    } catch (error) {
      console.error("Error saving vaccination: ", error);
      alert("Failed to save vaccination record.");
    }
  };

  const getTargetName = (vac: Vaccination | any) => {
    if (vac.targetType === 'Batch' || vac.batchId) {
      const batch = batchesList.find(b => b.id === vac.batchId);
      return batch ? `Batch: ${batch.batchName}` : 'Unknown Batch';
    }
    const animal = livestockList.find(a => a.id === vac.livestockId);
    return animal ? `${animal.animalName} (${animal.animalId})` : 'Unknown Animal';
  };

  const isOverdue = (dateString: string | undefined) => {
    if (!dateString) return false;
    return new Date(dateString) < new Date();
  };

  const filteredVaccinations = vaccinations.filter(v => 
    v.vaccineName.toLowerCase().includes(searchTerm.toLowerCase()) || 
    getTargetName(v).toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <Syringe className="h-6 w-6 mr-2 text-green-600" />
          Vaccination Management
        </h1>
        <button
          onClick={() => {
            if (showAddForm) {
              handleCloseForm();
            } else {
              setShowAddForm(true);
            }
          }}
          className="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
        >
          {showAddForm ? 'Cancel' : <><Plus className="-ml-1 mr-2 h-5 w-5" /> Add Record</>}
        </button>
      </div>

      {showAddForm && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-green-200">
          <h2 className="text-lg font-medium mb-4">
            {editingRecord ? 'Edit Vaccination Record' : 'New Vaccination Record'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Target Type</label>
                <select 
                  required 
                  value={targetType} 
                  onChange={(e) => setTargetType(e.target.value as any)} 
                  className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
                >
                  <option value="Individual Animal">Individual Animal</option>
                  <option value="Batch">Batch</option>
                </select>
              </div>

              {targetType === 'Individual Animal' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Animal ID / Name</label>
                  <select 
                    required 
                    value={selectedAnimalId} 
                    onChange={(e) => setSelectedAnimalId(e.target.value)} 
                    disabled={loading}
                    className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
                  >
                    {loading ? (
                      <option>Loading animals...</option>
                    ) : (
                      <>
                        <option value="">Select an animal...</option>
                        {livestockList?.map(a => (
                          <option key={a.id} value={a.id}>{a.animalName} ({a.animalId})</option>
                        ))}
                      </>
                    )}
                  </select>
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Batch ID / Name</label>
                  <select 
                    required 
                    value={selectedBatchId} 
                    onChange={(e) => setSelectedBatchId(e.target.value)} 
                    disabled={loading}
                    className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
                  >
                    {loading ? (
                      <option>Loading batches...</option>
                    ) : (
                      <>
                        <option value="">Select a batch...</option>
                        {batchesList?.map(b => (
                          <option key={b.id} value={b.id}>{b.batchName}</option>
                        ))}
                      </>
                    )}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700">Vaccine Name</label>
                <input required type="text" name="vaccineName" value={formData.vaccineName} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Vaccination Date</label>
                <input required type="date" name="vaccinationDate" value={formData.vaccinationDate} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm cursor-pointer" onClick={(e) => (e.target as any).showPicker?.()} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Next Due Date (Optional)</label>
                <input type="date" name="nextDueDate" value={formData.nextDueDate} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm cursor-pointer" onClick={(e) => (e.target as any).showPicker?.()} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Notes</label>
              <textarea name="notes" value={formData.notes} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" rows={2}></textarea>
            </div>
            <div className="flex justify-end">
              <button type="submit" className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700">
                Save Record
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
            placeholder="Search vaccines or animals..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md border border-gray-200">
          <ul className="divide-y divide-gray-200">
            {filteredVaccinations.length > 0 ? filteredVaccinations.map((vac) => {
              const overdue = isOverdue(vac.nextDueDate);
              return (
                <li key={vac.id}>
                  <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className={`flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center ${overdue ? 'bg-red-100' : 'bg-green-100'}`}>
                          <Syringe className={`h-6 w-6 ${overdue ? 'text-red-600' : 'text-green-600'}`} />
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-green-600 truncate">{vac.vaccineName}</p>
                          <p className="text-sm text-gray-500">
                            {vac.targetType === 'Batch' || vac.batchId ? 'Batch' : 'Animal'}:{' '}
                            <span className="font-medium text-gray-900">{getTargetName(vac)}</span>
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <div className="flex items-center text-sm text-gray-500">
                          <Calendar className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                          <p>
                            Due: <span className={overdue ? 'text-red-600 font-bold' : 'text-gray-900'}>{vac.nextDueDate}</span>
                          </p>
                        </div>
                        <div className="mt-1 flex items-center text-sm text-gray-500">
                          <p>Given: {vac.vaccinationDate}</p>
                        </div>
                        
                        {/* Action Buttons */}
                        <div className="flex items-center gap-3 mt-1">
                          {vac.livestockId && (
                            <button
                              onClick={() => navigate(`/livestock/${vac.livestockId}`)}
                              className="text-slate-400 hover:text-green-600 transition-colors p-1"
                              title="View Animal Profile"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleEdit(vac)}
                            className="text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                            title="Edit Record"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(vac.id!)}
                            className="text-slate-400 hover:text-red-600 transition-colors p-1"
                            title="Delete Record"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              );
            }) : (
              <div className="text-center py-12">
                <p className="text-gray-500">No vaccination records found.</p>
              </div>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

export default VaccinationManagement;
