import React, { useState } from 'react';
import { Save, Calendar, Weight, Tag, Info } from 'lucide-react';
import { calculateAgeInMonths } from '../../utils/livestockStatus';
import { INDIVIDUAL_LIVESTOCK_TYPES } from '../../features/livestockTypes';

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
  species: 'Dairy Cattle',
  breed: '',
  birthDate: '',
  age: '',
  weight: '',
});

const labelClassName = 'block text-sm font-medium text-gray-700 mb-1.5';
const inputClassName =
  'block w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm focus:border-green-500 focus:ring-2 focus:ring-green-500 shadow-sm';
const iconInputClassName =
  'block w-full rounded-lg border border-gray-300 bg-white py-2.5 pl-10 pr-3 text-sm focus:border-green-500 focus:ring-2 focus:ring-green-500 shadow-sm';

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
    <form onSubmit={handleSubmit} className="p-4 sm:p-5">
      <div className="space-y-5">
        <section className="rounded-xl border border-gray-200 bg-gray-50/40 p-4">
          <h3 className="flex items-center gap-2 text-base font-semibold text-gray-900">
            <Tag className="h-4 w-4 text-green-600" /> Basic Info
          </h3>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <div>
              <label className={labelClassName}>Tag ID *</label>
              <input required type="text" name="animalId" value={formData.animalId} onChange={handleFormChange} placeholder="eg- 001" className={inputClassName} />
            </div>
            <div>
              <label className={labelClassName}>Name</label>
              <input type="text" name="animalName" value={formData.animalName} onChange={handleFormChange} placeholder="e.g., Bessie" className={inputClassName} />
            </div>
            <div>
              <label htmlFor="individual-livestock-type" className={labelClassName}>
                Livestock
              </label>
              <select
                id="individual-livestock-type"
                name="species"
                value={formData.species}
                onChange={handleFormChange}
                aria-describedby="individual-livestock-type-help"
                className={inputClassName}
              >
                {INDIVIDUAL_LIVESTOCK_TYPES.map((livestockType) => (
                  <option key={livestockType} value={livestockType}>
                    {livestockType}
                  </option>
                ))}
              </select>
              <p id="individual-livestock-type-help" className="mt-1.5 text-xs text-gray-500">
                Choose livestock tracked as an individual record.
              </p>
            </div>
            <div>
              <label className={labelClassName}>Breed</label>
              <input type="text" name="breed" value={formData.breed} onChange={handleFormChange} placeholder="e.g., Friesian" className={inputClassName} />
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="flex items-center gap-2 text-base font-semibold text-gray-900">
            <Info className="h-4 w-4 text-green-600" /> Physical Details
          </h3>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className={labelClassName}>Birth Date</label>
            <div className="relative group">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-green-500 transition-colors pointer-events-none" />
              <input
                type="date"
                name="birthDate"
                value={formData.birthDate}
                onChange={handleFormChange}
                className={`${iconInputClassName} cursor-pointer`}
                onClick={(e: React.MouseEvent<HTMLInputElement>) => e.currentTarget.showPicker?.()}
              />
            </div>
          </div>
            <div>
              <label className={labelClassName}>Age (Months)</label>
              <input
                type="number"
                min="0"
                name="age"
                value={formData.birthDate ? String(ageInMonths ?? 0) : formData.age}
                onChange={handleFormChange}
                readOnly={Boolean(formData.birthDate)}
                placeholder={formData.birthDate ? 'Auto-calculated' : 'Enter age in months'}
                className={`block w-full rounded-lg px-3 py-2.5 text-sm font-medium shadow-sm ${
                  formData.birthDate
                    ? 'bg-gray-50 border border-gray-200 text-gray-500'
                    : 'border border-gray-300 bg-white focus:border-green-500 focus:ring-2 focus:ring-green-500'
                }`}
              />
            </div>
            <div>
              <label className={labelClassName}>Weight (kg)</label>
              <div className="relative">
                <Weight className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                <input type="number" name="weight" value={formData.weight} onChange={handleFormChange} placeholder="0.0" className={iconInputClassName} />
              </div>
            </div>
          </div>
        </section>

        <div className="flex justify-end border-t border-gray-100 pt-4">
          <button disabled={saving} type="submit" className="inline-flex w-full items-center justify-center rounded-lg bg-[#606c38] px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-[#4f5a2f] disabled:bg-[#606c38]/60 sm:w-auto sm:min-w-[180px]">
            {saving ? 'Saving...' : <><Save className="w-4 h-4 mr-2" /> Save Livestock</>}
          </button>
        </div>
      </div>
    </form>
  );
};

export default AnimalEntryForm;
