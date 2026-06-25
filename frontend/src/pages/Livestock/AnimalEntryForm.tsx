import React, { useState } from 'react';
import { Save, Calendar, Weight, Tag, Info } from 'lucide-react';
import { calculateAgeInMonths } from '../../utils/livestockStatus';

interface AnimalFormValues {
  animalId: string;
  animalName: string;
  species: string;
  breed: string;
  birthDate: string;
  age: string;
  weight: string;
}

export interface AnimalFormSubmission
  extends Omit<AnimalFormValues, 'age' | 'weight'> {
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
  age: '',
  weight: '',
});

const AnimalEntryForm: React.FC<AnimalEntryFormProps> = ({ onSave, saving }) => {
  const [formData, setFormData] = useState<AnimalFormValues>(createInitialAnimalForm);
  const ageInMonths = formData.birthDate
    ? calculateAgeInMonths(formData.birthDate) ?? 0
    : null;

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;

    if (name === 'birthDate') {
      const nextAge = value ? calculateAgeInMonths(value) ?? 0 : formData.age;
      setFormData((prev) => ({
        ...prev,
        birthDate: value,
        age: value ? String(nextAge) : prev.age,
      }));
      return;
    }

    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const resolvedAge = formData.birthDate
      ? calculateAgeInMonths(formData.birthDate) ?? 0
      : Number(formData.age) || 0;

    await onSave({
      ...formData,
      age: resolvedAge,
      weight: Number(formData.weight)
    });
    setFormData(createInitialAnimalForm());
  };

  return (
    <form onSubmit={handleSubmit} className="p-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_220px]">
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
              <input
                type="number"
                min="0"
                name="age"
                value={formData.birthDate ? String(ageInMonths ?? 0) : formData.age}
                onChange={handleFormChange}
                readOnly={Boolean(formData.birthDate)}
                placeholder={formData.birthDate ? 'Auto-calculated' : 'Enter age in months'}
                className={`block w-full rounded-md p-2 text-sm font-bold ${
                  formData.birthDate
                    ? 'bg-gray-50 border border-gray-200 text-gray-500'
                    : 'border-gray-300 border focus:ring-green-500 focus:border-green-500 shadow-sm'
                }`}
              />
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

        {/* Save Button */}
        <div className="flex items-end lg:justify-end">
          <button disabled={saving} type="submit" className="w-full inline-flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-md text-sm font-bold hover:bg-green-700 shadow-md transition-all disabled:bg-green-400 h-[42px] lg:min-w-[220px]">
            {saving ? 'Saving...' : <><Save className="w-4 h-4 mr-2" /> Save Livestock</>}
          </button>
        </div>
      </div>
    </form>
  );
};

export default AnimalEntryForm;
