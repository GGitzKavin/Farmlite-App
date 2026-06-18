import React, { useState, useEffect } from 'react';
import { Save, Tag, Info, Activity } from 'lucide-react';

interface BatchEntryFormProps {
  onSave: (data: any) => Promise<void>;
  saving: boolean;
  initialData?: any;
  onCancel?: () => void;
}

const BatchEntryForm: React.FC<BatchEntryFormProps> = ({ onSave, saving, initialData, onCancel }) => {
  const [batchForm, setBatchForm] = useState({
    batchName: '',
    species: 'Cattle (Beef)',
    headCount: 1,
    feedType: '',
    vaccinationStatus: 'Up to date',
    healthStatus: 'Healthy'
  });

  useEffect(() => {
    if (initialData) {
      setBatchForm({
        batchName: initialData.batchName || '',
        species: initialData.species || 'Cattle (Beef)',
        headCount: initialData.headCount || 1,
        feedType: initialData.feedType || '',
        vaccinationStatus: initialData.vaccinationStatus || 'Up to date',
        healthStatus: initialData.healthStatus || 'Healthy'
      });
    } else {
      setBatchForm({
        batchName: '',
        species: 'Cattle (Beef)',
        headCount: 1,
        feedType: '',
        vaccinationStatus: 'Up to date',
        healthStatus: 'Healthy'
      });
    }
  }, [initialData]);

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
    setBatchForm({
      batchName: '',
      species: 'Cattle (Beef)',
      headCount: 1,
      feedType: '',
      vaccinationStatus: 'Up to date',
      healthStatus: 'Healthy'
    });
  };

  return (
    <form onSubmit={handleSubmit} className="p-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Batch Info */}
        <div className="space-y-4">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Tag className="w-3 h-3" /> Batch Info
          </h3>
          <div>
            <label className="block text-xs font-bold text-gray-500 mb-1">Batch Name *</label>
            <input required type="text" name="batchName" value={batchForm.batchName} onChange={handleFormChange} placeholder="e.g., Summer Calves" className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm" />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 mb-1">Species</label>
            <select name="species" value={batchForm.species} onChange={handleFormChange} className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm bg-white">
              <option>Cattle (Beef)</option>
              <option>Cattle (Dairy)</option>
              <option>Poultry</option>
              <option>Chicken</option>
              <option>Duck</option>
              <option>Swine</option>
              <option>Sheep/Goats</option>
            </select>
          </div>
        </div>

        {/* Group Attributes */}
        <div className="space-y-4">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Info className="w-3 h-3" /> Group Attributes
          </h3>
          <div>
            <label className="block text-xs font-bold text-gray-500 mb-1">Head Count</label>
            <input required type="number" min="1" name="headCount" value={batchForm.headCount} onChange={handleFormChange} className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm" />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 mb-1">Primary Feed Type</label>
            <input type="text" name="feedType" value={batchForm.feedType} onChange={handleFormChange} placeholder="e.g., Starter Mix" className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm" />
          </div>
        </div>

        {/* Status */}
        <div className="space-y-4">
          <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Activity className="w-3 h-3" /> Status
          </h3>
          <div>
            <label className="block text-xs font-bold text-gray-500 mb-1">Health Status</label>
            <select name="healthStatus" value={batchForm.healthStatus} onChange={handleFormChange} className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm bg-white font-bold text-green-700">
              <option value="Healthy">Healthy</option>
              <option value="Sick">Sick</option>
              <option value="Under Treatment">Under Treatment</option>
              <option value="Quarantined">Quarantined</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 mb-1">Vaccinations</label>
            <select name="vaccinationStatus" value={batchForm.vaccinationStatus} onChange={handleFormChange} className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm bg-white font-bold text-blue-700">
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
              className="w-full inline-flex items-center justify-center px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-md text-sm font-bold hover:bg-gray-50 shadow-sm transition-all h-[42px] mt-auto font-medium"
            >
              Cancel
            </button>
          )}
          <button disabled={saving} type="submit" className="w-full inline-flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-md text-sm font-bold hover:bg-green-700 shadow-md transition-all disabled:bg-green-400 h-[42px] mt-auto">
            {saving ? (initialData ? 'Updating...' : 'Saving...') : <><Save className="w-4 h-4 mr-2" /> {initialData ? 'Update Batch' : 'Save Batch'}</>}
          </button>
        </div>
      </div>
    </form>
  );
};

export default BatchEntryForm;
