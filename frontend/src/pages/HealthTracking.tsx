import React, { useEffect, useState } from 'react';
import { collection, query, where, getDocs, addDoc, serverTimestamp, orderBy } from 'firebase/firestore';
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

const HealthTracking: React.FC = () => {
  const { currentUser } = useAuth();
  const [healthRecords, setHealthRecords] = useState<HealthRecord[]>([]);
  const [livestockList, setLivestockList] = useState<Livestock[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const [formData, setFormData] = useState<HealthRecordFormData>(createInitialHealthRecordForm);

  useEffect(() => {
    const fetchData = async () => {
      if (!currentUser) return;
      
      try {
        const qHR = query(collection(db, 'healthRecords'), where('userId', '==', currentUser.uid), orderBy('createdAt', 'desc'));
        const hrSnapshot = await getDocs(qHR);
        const hrData: HealthRecord[] = [];
        hrSnapshot.forEach((doc) => hrData.push({ id: doc.id, ...doc.data() } as HealthRecord));
        setHealthRecords(hrData);

        const qLs = query(collection(db, 'livestock'), where('userId', '==', currentUser.uid));
        const lsSnapshot = await getDocs(qLs);
        const lsData: Livestock[] = [];
        lsSnapshot.forEach((doc) => lsData.push({ id: doc.id, ...doc.data() } as Livestock));
        setLivestockList(lsData);
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;

    const animal = livestockList.find(a => a.id === formData.livestockId);
    if (!animal) return;

    try {
      const docRef = await addDoc(collection(db, 'healthRecords'), {
        ...formData,
        animalName: animal.animalName,
        userId: currentUser.uid,
        createdAt: serverTimestamp()
      });

      const newRecord: HealthRecord = {
        id: docRef.id,
        ...formData,
        animalName: animal.animalName,
        userId: currentUser.uid,
        createdAt: new Date()
      };

      setHealthRecords([newRecord, ...healthRecords]);
      setShowAddForm(false);
      setFormData(createInitialHealthRecordForm());
    } catch (error) {
      console.error("Error adding health record: ", error);
      alert("Failed to add health record.");
    }
  };

  const filteredRecords = healthRecords.filter(hr => 
    hr.animalName.toLowerCase().includes(searchTerm.toLowerCase()) || 
    hr.diseaseType.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <Activity className="h-6 w-6 mr-2 text-green-600" />
          Health Tracking
        </h1>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
        >
          {showAddForm ? 'Cancel' : <><Plus className="-ml-1 mr-2 h-5 w-5" /> Add Record</>}
        </button>
      </div>

      {showAddForm && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-green-200">
          <h2 className="text-lg font-medium mb-4">New Health Record</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Animal</label>
                <select required name="livestockId" value={formData.livestockId} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm">
                  <option value="">Select an animal...</option>
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
                  <option>Recovered</option>
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
              <button type="submit" className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700">
                Save Health Record
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

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredRecords.length > 0 ? filteredRecords.map((record) => (
            <div key={record.id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-5">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{record.animalName}</h3>
                    <p className="text-sm font-medium text-red-600">{record.diseaseType}</p>
                  </div>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    record.recoveryStatus === 'Recovered' ? 'bg-green-100 text-green-800' : 
                    record.recoveryStatus === 'Critical' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {record.recoveryStatus}
                  </span>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <h4 className="text-xs font-medium text-gray-500 uppercase">Symptoms</h4>
                    <p className="mt-1 text-sm text-gray-900">{record.symptoms}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-xs font-medium text-gray-500 uppercase">Treatment</h4>
                      <p className="mt-1 text-sm text-gray-900">{record.treatment}</p>
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
              </div>
            </div>
          )) : (
            <div className="col-span-full text-center py-12 bg-white rounded-lg border border-gray-200 border-dashed">
              <p className="text-gray-500">No health records found.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HealthTracking;
