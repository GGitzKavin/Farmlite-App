import React, { useState } from 'react';
import { Save, Calendar, Weight, Activity, Tag, Info } from 'lucide-react';

type AnimalHealthStatus = 'Healthy' | 'Sick' | 'Under Treatment' | 'Quarantined';
type AnimalVaccinationStatus = 'Up to date' | 'Pending' | 'Overdue';

interface AnimalFormValues {
  animalId: string;
  animalName: string;
  species: string;
  breed: string;
  birthDate: string;
  weight: string;
  healthStatus: AnimalHealthStatus;
  feedType: string;
  vaccinationStatus: AnimalVaccinationStatus;
}

export interface AnimalFormSubmission extends Omit<AnimalFormValues, 'weight'> {
  age: number;
  weight: number;
}

interface AnimalEntryFormProps {
  onSave: (data: AnimalFormSubmission) => Promise<void>;
  saving: boolean;
}

const createInitialAnimalForm = (): AnimalFormValues => ({
  animalId: '',
  animalName: '',
  species: 'Cattle (Beef)',
  breed: '',
  birthDate: '',
  weight: '',
  healthStatus: 'Healthy',
  feedType: '',
  vaccinationStatus: 'Up to date'
});

const AnimalEntryForm: React.FC<AnimalEntryFormProps> = ({ onSave, saving }) => {
  const [formData, setFormData] = useState<AnimalFormValues>(createInitialAnimalForm);

  const calculateAgeInMonths = (birthDate: string) => {
    if (!birthDate) return 0;
    const birth = new Date(birthDate);
    const today = new Date();
    return (today.getFullYear() - birth.getFullYear()) * 12 + (today.getMonth() - birth.getMonth());
  };

  const ageInMonths = calculateAgeInMonths(formData.birthDate);

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave({
      ...formData,
      age: ageInMonths,
      weight: Number(formData.weight)
    });
    setFormData(createInitialAnimalForm());
  };

  return (
    <form onSubmit={handleSubmit} className="p-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Basic Info */}
        <div className="space-y-4">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Tag className="w-3 h-3" /> Basic Info
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-gray-500 mb-1">Tag ID *</label>
              <input required type="text" name="animalId" value={formData.animalId} onChange={handleFormChange} placeholder="eg- 001" className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm" />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-500 mb-1">Name</label>
              <input type="text" name="animalName" value={formData.animalName} onChange={handleFormChange} placeholder="e.g., Bessie" className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-gray-500 mb-1">Species</label>
              <select name="species" value={formData.species} onChange={handleFormChange} className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm bg-white">
                <option>Cattle (Beef)</option>
                <option>Cattle (Dairy)</option>
                <option>Poultry</option>
                <option>Chicken</option>
                <option>Duck</option>
                <option>Swine</option>
                <option>Sheep/Goats</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-500 mb-1">Breed</label>
              <input type="text" name="breed" value={formData.breed} onChange={handleFormChange} placeholder="e.g., Angus" className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm" />
            </div>
          </div>
        </div>

        {/* Physical Details */}
        <div className="space-y-4">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Info className="w-3 h-3" /> Physical Details
          </h3>
          <div>
            <label className="block text-xs font-bold text-gray-500 mb-1">Birth Date</label>
            <div className="relative group">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-green-500 transition-colors pointer-events-none" />
              <input 
                type="date" 
                name="birthDate" 
                value={formData.birthDate} 
                onChange={handleFormChange} 
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-green-500 focus:border-green-500 shadow-sm bg-white cursor-pointer" 
                onClick={(e: React.MouseEvent<HTMLInputElement>) => e.currentTarget.showPicker?.()}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-gray-500 mb-1">Age (Months)</label>
              <input disabled type="text" value={ageInMonths} className="block w-full bg-gray-50 border border-gray-200 rounded-md p-2 text-sm text-gray-500 font-bold" />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-500 mb-1">Weight (kg)</label>
              <div className="relative">
                <Weight className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                <input type="number" name="weight" value={formData.weight} onChange={handleFormChange} placeholder="0.0" className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-green-500 focus:border-green-500 shadow-sm" />
              </div>
            </div>
          </div>
        </div>

        {/* Health & Feed */}
        <div className="space-y-4">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Activity className="w-3 h-3" /> Health & Feed
          </h3>
          <div>
            <label className="block text-xs font-bold text-gray-500 mb-1">Health Status</label>
            <select name="healthStatus" value={formData.healthStatus} onChange={handleFormChange} className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm bg-white font-bold text-green-700">
              <option value="Healthy">Healthy</option>
              <option value="Sick">Sick</option>
              <option value="Under Treatment">Under Treatment</option>
              <option value="Quarantined">Quarantined</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 mb-1">Primary Feed Type</label>
            <input type="text" name="feedType" value={formData.feedType} onChange={handleFormChange} placeholder="e.g., Grain Mix" className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm" />
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-end lg:pb-0">
          <button disabled={saving} type="submit" className="w-full inline-flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-md text-sm font-bold hover:bg-green-700 shadow-md transition-all disabled:bg-green-400 h-[42px] mt-auto">
            {saving ? 'Saving...' : <><Save className="w-4 h-4 mr-2" /> Save Livestock</>}
          </button>
        </div>
      </div>
    </form>
  );
};

export default AnimalEntryForm;
