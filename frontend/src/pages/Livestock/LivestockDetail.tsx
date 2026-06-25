import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { doc, getDoc, collection, query, where, getDocs, writeBatch } from 'firebase/firestore';
import { db } from '../../firebase/config';
import { useAuth } from '../../context/AuthContext';
import type { Livestock, HealthRecord, Vaccination } from '../../types';
import { ArrowLeft, Trash2, Activity, Syringe, Wheat, FileText } from 'lucide-react';
import {
  getDerivedHealthStatus,
  getHealthBadgeStyle,
  parseDateValue,
  getVaccinationStatus,
  getVaccinationStatusStyle,
} from '../../utils/livestockStatus';

const LivestockDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [animal, setAnimal] = useState<Livestock | null>(null);
  const [healthRecords, setHealthRecords] = useState<HealthRecord[]>([]);
  const [vaccinations, setVaccinations] = useState<Vaccination[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('details'); // details, health, feed

  useEffect(() => {
    const fetchAnimalAndRecords = async () => {
      if (!id || !currentUser) {
        setLoading(false);
        return;
      }

      let canLoadRelatedRecords = false;

      try {
        setLoading(true);
        const docRef = doc(db, 'livestock', id);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists() && docSnap.data().userId === currentUser.uid) {
          setAnimal({ id: docSnap.id, ...docSnap.data() } as Livestock);
          canLoadRelatedRecords = true;
        } else {
          setError('Animal not found or you do not have permission.');
          setAnimal(null);
          setHealthRecords([]);
          setVaccinations([]);
          return;
        }
      } catch (err) {
        console.error(err);
        setError('Failed to fetch animal details.');
        setAnimal(null);
        setHealthRecords([]);
        setVaccinations([]);
      } finally {
        setLoading(false);
      }

      if (!canLoadRelatedRecords) {
        return;
      }

      try {
        const healthSnapshot = await getDocs(collection(db, 'healthRecords'));
        const healthData = healthSnapshot.docs
          .map((document) => ({ id: document.id, ...document.data() }) as HealthRecord)
          .filter(
            (record) =>
              record.livestockId === id &&
              (!record.userId || record.userId === currentUser.uid)
          );
        setHealthRecords(healthData);
      } catch (healthError) {
        console.error('Failed to load animal health records:', healthError);
        setHealthRecords([]);
      }

      try {
        const vaccinationSnapshot = await getDocs(collection(db, 'vaccinations'));
        const vaccinationData = vaccinationSnapshot.docs
          .map((document) => ({ id: document.id, ...document.data() }) as Vaccination)
          .filter(
            (record) =>
              record.livestockId === id &&
              (!record.userId || record.userId === currentUser.uid)
          );
        setVaccinations(vaccinationData);
      } catch (vaccinationError) {
        console.error('Failed to load animal vaccinations:', vaccinationError);
        setVaccinations([]);
      }
    };
    fetchAnimalAndRecords();
  }, [id, currentUser]);

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this livestock record?')) return;
    try {
      if (!id || !currentUser) return;

      const [healthSnapshot, vaccinationSnapshot] = await Promise.all([
        getDocs(
          query(
            collection(db, 'healthRecords'),
            where('livestockId', '==', id),
            where('userId', '==', currentUser.uid)
          )
        ),
        getDocs(
          query(
            collection(db, 'vaccinations'),
            where('livestockId', '==', id),
            where('userId', '==', currentUser.uid)
          )
        ),
      ]);

      const batch = writeBatch(db);
      batch.delete(doc(db, 'livestock', id));
      healthSnapshot.forEach((record) => batch.delete(record.ref));
      vaccinationSnapshot.forEach((record) => batch.delete(record.ref));

      await batch.commit();
      navigate('/livestock');
    } catch (err) {
      console.error(err);
      alert('Failed to delete livestock');
    }
  };

  if (loading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div></div>;
  if (error || !animal) return <div className="text-center p-12 text-red-600">{error || 'Not found'}</div>;

  const derivedHealthStatus = getDerivedHealthStatus(healthRecords, 'Healthy');
  const derivedVaccinationStatus = getVaccinationStatus(vaccinations);
  const sortedVaccinations = [...vaccinations].sort((left, right) => {
    const leftTime = parseDateValue(left.vaccinationDate)?.getTime() ?? 0;
    const rightTime = parseDateValue(right.vaccinationDate)?.getTime() ?? 0;
    return rightTime - leftTime;
  });
  const sortedHealthRecords = [...healthRecords].sort((left, right) => {
    const leftTime =
      parseDateValue(left.updatedAt)?.getTime() ??
      parseDateValue(left.createdAt)?.getTime() ??
      0;
    const rightTime =
      parseDateValue(right.updatedAt)?.getTime() ??
      parseDateValue(right.createdAt)?.getTime() ??
      0;
    return rightTime - leftTime;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <Link to="/livestock" className="p-2 bg-white border border-gray-200 rounded-md hover:bg-gray-50 text-gray-600">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{animal.animalName}</h1>
            <p className="text-sm text-gray-500">ID: {animal.animalId} &bull; {animal.species}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Edit is not implemented yet, just a placeholder link */}
          <Link to={`/livestock/edit/${animal.id}`} className="text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors">
            Edit
          </Link>
          <button onClick={handleDelete} className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50">
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button onClick={() => setActiveTab('details')} className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'details' ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
            Full Details
          </button>
          <button onClick={() => setActiveTab('health')} className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'health' ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
            Medical & Vaccines
          </button>
          <button onClick={() => setActiveTab('feed')} className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'feed' ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
            Feed Records
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white shadow rounded-lg border border-gray-200">
        {activeTab === 'details' && (
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center"><FileText className="w-5 h-5 mr-2 text-gray-400" /> Animal Profile</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm font-medium text-gray-500">Species</p>
                  <p className="mt-1 text-base text-gray-900">{animal.species}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm font-medium text-gray-500">Breed</p>
                  <p className="mt-1 text-base text-gray-900">{animal.breed || 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm font-medium text-gray-500">Gender</p>
                  <p className="mt-1 text-base text-gray-900">{animal.gender}</p>
                </div>
              </div>
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm font-medium text-gray-500">Age</p>
                  <p className="mt-1 text-base text-gray-900">{animal.age} Months</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm font-medium text-gray-500">Weight</p>
                  <p className="mt-1 text-base text-gray-900">{animal.weight} kg</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm font-medium text-gray-500">Birth Date</p>
                  <p className="mt-1 text-base text-gray-900">{animal.birthDate || 'N/A'}</p>
                </div>
              </div>
            </div>
            
            {animal.notes && (
              <div className="mt-6 bg-yellow-50 border border-yellow-200 p-4 rounded-md">
                <h4 className="text-sm font-medium text-yellow-800 mb-1">Notes</h4>
                <p className="text-sm text-yellow-700 whitespace-pre-wrap">{animal.notes}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'health' && (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center"><Activity className="w-5 h-5 mr-2 text-gray-400" /> Health Status</h3>
                <div className={`p-4 rounded-md border ${getHealthBadgeStyle(derivedHealthStatus, 'card')}`}>
                  <p className="text-lg font-bold">{derivedHealthStatus}</p>
                  <p className="text-sm mt-1 text-gray-600">Based on the latest health tracking record when available.</p>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center"><Syringe className="w-5 h-5 mr-2 text-gray-400" /> Vaccination Status</h3>
                <div className={`p-4 rounded-md border ${getVaccinationStatusStyle(derivedVaccinationStatus, 'card')}`}>
                  <p className="text-lg font-bold">{derivedVaccinationStatus}</p>
                  <p className="text-sm mt-1 text-gray-600">Derived from this animal&apos;s vaccination records when available.</p>
                </div>
              </div>
            </div>
            <div className="mt-8 space-y-8">
              <div>
                <h3 className="text-md font-bold text-gray-900 mb-4 flex items-center"><Syringe className="w-5 h-5 mr-2 text-green-600" /> Vaccination History</h3>
                {vaccinations.length > 0 ? (
                  <div className="overflow-hidden bg-white border border-gray-200 rounded-md">
                    <ul className="divide-y divide-gray-200">
                      {sortedVaccinations.map((vac) => (
                        <li key={vac.id} className="p-4 hover:bg-gray-50">
                          <div className="flex justify-between">
                            <p className="text-sm font-medium text-green-600">{vac.vaccineName}</p>
                            <p className="text-xs text-gray-500">Given: {vac.vaccinationDate}</p>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">Next Due: <span className="font-bold">{vac.nextDueDate}</span></p>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic">No vaccination records found for this animal.</p>
                )}
              </div>

              <div>
                <h3 className="text-md font-bold text-gray-900 mb-4 flex items-center"><Activity className="w-5 h-5 mr-2 text-red-600" /> Medical History</h3>
                {healthRecords.length > 0 ? (
                  <div className="space-y-4">
                    {sortedHealthRecords.map((hr) => (
                      <div key={hr.id} className="p-4 border border-gray-200 rounded-md bg-white shadow-sm">
                        <div className="flex justify-between items-start">
                          <p className="text-sm font-bold text-gray-900">{hr.diseaseType}</p>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${hr.recoveryStatus === 'Recovered' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                            {hr.recoveryStatus}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-2"><strong>Symptoms:</strong> {hr.symptoms}</p>
                        <p className="text-sm text-gray-600 mt-1"><strong>Treatment:</strong> {hr.treatment}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic">No medical history found for this animal.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'feed' && (
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center"><Wheat className="w-5 h-5 mr-2 text-gray-400" /> Feed Information</h3>
            <div className="bg-green-50 p-6 rounded-lg border border-green-200 text-center">
              <Wheat className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-green-900 mb-2">Optimize Feeding with AI</h4>
              <p className="text-sm text-green-700 mb-6">
                Get a scientifically calculated feed plan based on this {animal.species.toLowerCase()}'s weight, age, and health status.
              </p>
              <Link 
                to={`/ai-feed?id=${animal.id}`}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
              >
                Get AI Recommendation
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LivestockDetail;
