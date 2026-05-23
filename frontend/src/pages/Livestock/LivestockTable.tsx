import React, { useEffect, useState } from 'react';
import { collection, query, where, onSnapshot, orderBy, addDoc, serverTimestamp } from 'firebase/firestore';
import { db } from '../../firebase/config';
import { useAuth } from '../../context/AuthContext';
import type { Livestock } from '../../types';
import { Link } from 'react-router-dom';
import { Plus, Search } from 'lucide-react';
import AnimalEntryForm from './AnimalEntryForm';

interface LivestockTableProps {
  searchTerm: string;
  filterSpecies: string;
  onSuccess: (msg: string) => void;
}

const LivestockTable: React.FC<LivestockTableProps> = ({ searchTerm, filterSpecies, onSuccess }) => {
  const { currentUser } = useAuth();
  const [livestockList, setLivestockList] = useState<Livestock[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!currentUser?.uid) return;
    
    setLoading(true);
    const q = query(
      collection(db, 'livestock'),
      where('userId', '==', currentUser.uid),
      orderBy('createdAt', 'desc')
    );
    
    const unsubscribe = onSnapshot(q, (querySnapshot) => {
      const data: Livestock[] = [];
      querySnapshot.forEach((doc) => {
        data.push({ id: doc.id, ...doc.data() } as Livestock);
      });
      setLivestockList(data);
      setLoading(false);
    }, (error) => {
      console.error("Error listening to livestock: ", error);
      setLoading(false);
    });

    return () => unsubscribe();
  }, [currentUser?.uid]);

  const handleSave = async (data: any) => {
    if (!currentUser?.uid) return;
    setSaving(true);
    try {
      await addDoc(collection(db, 'livestock'), {
        ...data,
        userId: currentUser.uid,
        createdAt: serverTimestamp()
      });
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
    const matchesFilter = filterSpecies ? species === filterSpecies : true;
    
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
    <div className="space-y-8">
      {/* Persistent Inline Entry Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 bg-gray-50">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Plus className="w-5 h-5 text-green-600" /> Add New Animal
          </h2>
        </div>
        <AnimalEntryForm onSave={handleSave} saving={saving} />
      </div>

      {/* Livestock Grid */}
      {filteredList.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredList.map((animal) => (
            <div key={animal?.id} className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200 hover:shadow-md transition-all duration-200">
              <div className="p-5">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{animal?.animalName}</h3>
                    <p className="text-sm text-gray-500">ID: {animal?.animalId}</p>
                  </div>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                    animal?.healthStatus === 'Healthy' ? 'bg-green-100 text-green-800' : 
                    animal?.healthStatus === 'Sick' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {animal?.healthStatus}
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Species</p>
                    <p className="mt-0.5 text-sm text-gray-900 font-medium">{animal?.species}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Breed</p>
                    <p className="mt-0.5 text-sm text-gray-900 font-medium">{animal?.breed}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Age/Weight</p>
                    <p className="mt-0.5 text-sm text-gray-900 font-medium">{animal?.age} mo / {animal?.weight}kg</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Vaccines</p>
                    <p className={`mt-0.5 text-sm font-bold ${animal?.vaccinationStatus === 'Up to date' ? 'text-green-600' : 'text-red-600'}`}>
                      {animal?.vaccinationStatus}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3 border-t border-gray-100">
                <Link to={`/livestock/${animal?.id}`} className="text-sm font-bold text-green-600 hover:text-green-700 w-full text-center block transition-colors">
                  View Full Profile
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
          <div className="bg-white p-4 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4 shadow-sm">
            <Search className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-900">No animals found</h3>
          <p className="text-gray-500 mt-1 max-w-xs mx-auto">
            {searchTerm || filterSpecies 
              ? "We couldn't find any animals matching your current search criteria." 
              : "You haven't added any livestock yet. Use the form above to add your first animal."}
          </p>
        </div>
      )}
    </div>
  );
};

export default LivestockTable;
