import React, { useState } from 'react';
import { Save, Tag, Info, Activity } from 'lucide-react';
import {
  BATCH_LIVESTOCK_TYPES,
  includeStoredLivestockType,
} from '../../features/livestockTypes';

type BatchHealthStatus = 'Healthy' | 'Sick' | 'Under Treatment' | 'Quarantined';
type BatchVaccinationStatus = 'Up to date' | 'Pending' | 'Overdue';

interface BatchFormValues {
  batchName: string;
  species: string;
  headCount: string;
  feedType: string;
  vaccinationStatus: BatchVaccinationStatus;
  healthStatus: BatchHealthStatus;
}

export interface BatchFormSubmission extends Omit<BatchFormValues, 'headCount'> {
  headCount: number;
}

interface BatchEntryFormProps {
  onSave: (data: BatchFormSubmission) => Promise<void>;
  saving: boolean;
  initialData?: Partial<BatchFormSubmission>;
  onCancel?: () => void;
}

const createInitialBatchForm = (initialData?: Partial<BatchFormSubmission>): BatchFormValues => ({
  batchName: initialData?.batchName ?? '',
  species: initialData?.species ?? BATCH_LIVESTOCK_TYPES[0],
  headCount: String(initialData?.headCount ?? 1),
  feedType: initialData?.feedType ?? '',
  vaccinationStatus: initialData?.vaccinationStatus ?? 'Up to date',
  healthStatus: initialData?.healthStatus ?? 'Healthy'
});

const BatchEntryForm: React.FC<BatchEntryFormProps> = ({ onSave, saving, initialData, onCancel }) => {
  const [batchForm, setBatchForm] = useState<BatchFormValues>(() => createInitialBatchForm(initialData));
  const livestockTypeOptions = includeStoredLivestockType(
    BATCH_LIVESTOCK_TYPES,
    batchForm.species
  );

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setBatchForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave({
      ...batchForm,
      headCount: Number(batchForm.headCount)
    });

    if (!initialData) {
      setBatchForm(createInitialBatchForm());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-5 sm:p-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Batch Info */}
        <div className="space-y-4">
          <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#606c38]">
            <Tag className="w-3 h-3" /> Batch Info
          </h3>
          <div>
            <label className="mb-1 block text-xs font-bold text-[#283618]">Batch Name *</label>
            <input required type="text" name="batchName" value={batchForm.batchName} onChange={handleFormChange} placeholder="e.g., Summer Calves" className="block w-full rounded-md border border-[#dda15e]/70 bg-white p-2 text-sm shadow-sm focus:border-[#606c38] focus:ring-[#606c38]" />
          </div>
          <div>
            <label htmlFor="batch-livestock-type" className="mb-1 block text-xs font-bold text-[#283618]">Livestock Type</label>
            <select id="batch-livestock-type" name="species" value={batchForm.species} onChange={handleFormChange} className="block w-full rounded-md border border-[#dda15e]/70 bg-white p-2 text-sm shadow-sm focus:border-[#606c38] focus:ring-[#606c38]">
              {livestockTypeOptions.map((livestockType) => (
                <option key={livestockType} value={livestockType}>
                  {livestockType}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Group Attributes */}
        <div className="space-y-4">
          <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#606c38]">
            <Info className="w-3 h-3" /> Group Attributes
          </h3>
          <div>
            <label className="mb-1 block text-xs font-bold text-[#283618]">Head Count</label>
            <input required type="number" min="1" name="headCount" value={batchForm.headCount} onChange={handleFormChange} className="block w-full rounded-md border border-[#dda15e]/70 bg-white p-2 text-sm shadow-sm focus:border-[#606c38] focus:ring-[#606c38]" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-[#283618]">Primary Feed Type</label>
            <input type="text" name="feedType" value={batchForm.feedType} onChange={handleFormChange} placeholder="e.g., Starter Mix" className="block w-full rounded-md border border-[#dda15e]/70 bg-white p-2 text-sm shadow-sm focus:border-[#606c38] focus:ring-[#606c38]" />
          </div>
        </div>

        {/* Status */}
        <div className="space-y-4">
          <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#606c38]">
            <Activity className="w-3 h-3" /> Status
          </h3>
          <div>
            <label className="mb-1 block text-xs font-bold text-[#283618]">Health Status</label>
            <select name="healthStatus" value={batchForm.healthStatus} onChange={handleFormChange} className="block w-full rounded-md border border-[#dda15e]/70 bg-white p-2 text-sm font-semibold text-[#283618] shadow-sm focus:border-[#606c38] focus:ring-[#606c38]">
              <option value="Healthy">Healthy</option>
              <option value="Sick">Sick</option>
              <option value="Under Treatment">Under Treatment</option>
              <option value="Quarantined">Quarantined</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-[#283618]">Vaccinations</label>
            <select name="vaccinationStatus" value={batchForm.vaccinationStatus} onChange={handleFormChange} className="block w-full rounded-md border border-[#dda15e]/70 bg-white p-2 text-sm font-semibold text-[#283618] shadow-sm focus:border-[#606c38] focus:ring-[#606c38]">
              <option>Up to date</option>
              <option>Pending</option>
              <option>Overdue</option>
            </select>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex gap-3 items-end lg:pb-0">
          {initialData && onCancel && (
            <button
              onClick={onCancel}
              type="button"
              className="mt-auto inline-flex h-[42px] w-full items-center justify-center rounded-lg border border-[#dda15e] bg-white px-4 py-2 text-sm font-medium text-[#bc6c25] shadow-sm transition-all hover:bg-[#fefae0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
            >
              Cancel
            </button>
          )}
          <button disabled={saving} type="submit" className="mt-auto inline-flex h-[42px] w-full items-center justify-center rounded-lg bg-[#606c38] px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-[#4f5a2f] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#283618] disabled:bg-[#606c38]/60">
            {saving ? (initialData ? 'Updating...' : 'Saving...') : <><Save className="w-4 h-4 mr-2" /> {initialData ? 'Update Batch' : 'Save Batch'}</>}
          </button>
        </div>
      </div>
    </form>
  );
};

export default BatchEntryForm;
