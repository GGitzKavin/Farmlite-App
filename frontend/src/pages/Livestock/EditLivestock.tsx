import React, { useEffect, useState } from 'react';
import { doc, getDoc, updateDoc } from 'firebase/firestore';
import { db } from '../../firebase/config';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ArrowLeft, Save, Calendar } from 'lucide-react';
import { calculateAgeInMonths } from '../../utils/livestockStatus';

interface EditLivestockFormData {
  animalId: string;
  animalName: string;
  species: string;
  breed: string;
  gender: string;
  age: string;
  weight: string;
  birthDate: string;
  notes: string;
}

const EditLivestock: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [calculatedAge, setCalculatedAge] = useState<number | null>(null);

  const [formData, setFormData] = useState<EditLivestockFormData>({
    animalId: '',
    animalName: '',
    species: 'Cattle (Beef)',
    breed: '',
    gender: 'Male',
    age: '',
    weight: '',
    birthDate: '',
    notes: ''
  });

  useEffect(() => {
    const fetchAnimal = async () => {
      if (!id || !currentUser) return;
      try {
        const docRef = doc(db, 'livestock', id);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists() && docSnap.data().userId === currentUser.uid) {
          const data = docSnap.data();
          setFormData({
            animalId: data.animalId || '',
            animalName: data.animalName || '',
            species: data.species || 'Cattle (Beef)',
            breed: data.breed || '',
            gender: data.gender || 'Male',
            age: data.age?.toString() || '',
            weight: data.weight?.toString() || '',
            birthDate: data.birthDate || '',
            notes: data.notes || ''
          });
          
          if (data.birthDate) {
            setCalculatedAge(calculateAgeInMonths(data.birthDate));
          }
        } else {
          setError('Animal not found or you do not have permission.');
        }
      } catch (err) {
        console.error(err);
        setError('Failed to fetch animal details.');
      } finally {
        setLoading(false);
      }
    };
    fetchAnimal();
  }, [id, currentUser]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    if (name === 'birthDate') {
      const age = calculateAgeInMonths(value);
      setCalculatedAge(value ? age : null);
      setFormData(prev => ({ 
        ...prev, 
        birthDate: value,
        age: value ? String(age ?? 0) : prev.age
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser || !id) return;

    setSaving(true);
    setError('');

    try {
      const docRef = doc(db, 'livestock', id);
      const resolvedAge = formData.birthDate
        ? calculateAgeInMonths(formData.birthDate) ?? 0
        : Number(formData.age) || 0;

      await updateDoc(docRef, {
        ...formData,
        age: resolvedAge,
        weight: Number(formData.weight),
        updatedAt: new Date()
      });

      navigate(`/livestock/${id}`);
    } catch (err) {
      console.error("Error updating livestock: ", err);
      setError(err instanceof Error ? err.message : 'Failed to update livestock');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div></div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link to={`/livestock/${id}`} className="p-2 bg-white border border-gray-200 rounded-md hover:bg-gray-50 text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Edit Livestock: {formData.animalName}</h1>
      </div>

      <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 p-4 rounded-md border border-red-200">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Info */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 border-b pb-2">Basic Information</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Animal ID / Tag</label>
                <input 
                  required 
                  type="text" 
                  name="animalId" 
                  value={formData.animalId} 
                  onChange={handleChange} 
                  className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" 
                  placeholder="eg- 001" 
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Animal Name</label>
                <input 
                  required 
                  type="text" 
                  name="animalName" 
                  value={formData.animalName} 
                  onChange={handleChange} 
                  className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" 
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Species</label>
                <select name="species" value={formData.species} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm">
                  <option>Cattle (Beef)</option>
                  <option>Cattle (Dairy)</option>
                  <option>Poultry (Chickens, Ducks, Turkeys)</option>
                  <option>Chicken</option>
                  <option>Duck</option>
                  <option>Swine (Pigs)</option>
                  <option>Sheep/Goats</option>
                  <option>Equine (Horses, Donkeys)</option>
                  <option>Other Livestock</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Breed</label>
                <input 
                  required 
                  type="text" 
                  name="breed" 
                  value={formData.breed} 
                  onChange={handleChange} 
                  className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" 
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Gender</label>
                <select name="gender" value={formData.gender} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm">
                  <option>Male</option>
                  <option>Female</option>
                </select>
              </div>
            </div>

            {/* Physical Details */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 border-b pb-2">Physical Details</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Birth Date</label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Calendar className="h-5 w-5 text-gray-400" />
                  </div>
                  <input 
                    type="date" 
                    name="birthDate" 
                    value={formData.birthDate} 
                    onChange={handleChange} 
                    className="block w-full pl-10 rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm cursor-pointer" 
                    onClick={(e: React.MouseEvent<HTMLInputElement>) => e.currentTarget.showPicker?.()}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Age (Months)</label>
                  <input 
                    type="number"
                    min="0"
                    name="age"
                    value={formData.birthDate ? String(calculatedAge ?? 0) : formData.age}
                    onChange={handleChange}
                    readOnly={Boolean(formData.birthDate)}
                    placeholder={formData.birthDate ? 'Auto-calculated' : 'Enter age in months'}
                    className={`mt-1 block w-full rounded-md p-2 sm:text-sm ${
                      formData.birthDate
                        ? 'border-gray-200 border bg-gray-50 text-gray-500 cursor-not-allowed'
                        : 'border-gray-300 border shadow-sm focus:border-green-500 focus:ring-green-500'
                    }`}
                  />
                  <p className="mt-1 text-[10px] text-gray-400 italic font-medium">calculated from birth date when available</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Weight (kg)</label>
                  <input 
                    required 
                    type="number" 
                    min="0" 
                    step="0.1" 
                    name="weight" 
                    value={formData.weight} 
                    onChange={handleChange} 
                    className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" 
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4">
            <label className="block text-sm font-medium text-gray-700">Notes / Extra Details</label>
            <textarea name="notes" rows={3} value={formData.notes} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" placeholder="Additional health or behavior notes..."></textarea>
          </div>

          <div className="pt-5 border-t flex justify-end">
            <button
              type="button"
              onClick={() => navigate(`/livestock/${id}`)}
              className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 mr-3"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400"
            >
              {saving ? 'Saving...' : <><Save className="w-4 h-4 mr-2" /> Update Livestock</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditLivestock;
