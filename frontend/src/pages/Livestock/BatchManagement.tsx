import React, { useEffect, useState } from 'react';
import { collection, query, where, onSnapshot, orderBy, addDoc, doc, deleteDoc, updateDoc, serverTimestamp } from 'firebase/firestore';
import { db } from '../../firebase/config';
import { useAuth } from '../../context/AuthContext';
import { Users, Plus, ShieldCheck, Wheat, Trash2 } from 'lucide-react';
import BatchEntryForm from './BatchEntryForm';
import type { Batch } from '../../types';

interface BatchManagementProps {
  searchTerm: string;
  filterSpecies: string;
  onSuccess: (msg: string) => void;
}

const BatchCard: React.FC<{
  batch: Batch;
  onDelete: (id: string) => void;
  onSuccess: (msg: string) => void;
}> = ({ batch, onDelete, onSuccess }) => {
  const [isEditingInline, setIsEditingInline] = useState(false);
  const [editName, setEditName] = useState(batch.batchName);
  const [editCount, setEditCount] = useState(batch.headCount);
  const [editFeed, setEditFeed] = useState(batch.feedType);
  const [editHealth, setEditHealth] = useState(batch.healthStatus);
  const [savingInline, setSavingInline] = useState(false);

  useEffect(() => {
    setEditName(batch.batchName);
    setEditCount(batch.headCount);
    setEditFeed(batch.feedType);
    setEditHealth(batch.healthStatus);
  }, [batch]);

  const handleSaveInline = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingInline(true);
    try {
      const docRef = doc(db, 'batches', batch.id);
      await updateDoc(docRef, {
        batchName: editName,
        headCount: Number(editCount),
        feedType: editFeed,
        healthStatus: editHealth
      });
      setIsEditingInline(false);
      onSuccess('Batch updated successfully!');
    } catch (err) {
      console.error("Error updating batch inline:", err);
      alert("Failed to update batch.");
    } finally {
      setSavingInline(false);
    }
  };

  if (isEditingInline) {
    return (
      <form onSubmit={handleSaveInline} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden border-l-4 border-l-green-500 p-5 space-y-4 flex flex-col justify-between h-full">
        <div className="space-y-3">
          <div>
            <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Batch Name *</label>
            <input
              required
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Head Count *</label>
              <input
                required
                type="number"
                min="1"
                value={editCount}
                onChange={(e) => setEditCount(Number(e.target.value))}
                className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Health Status</label>
              <select
                value={editHealth}
                onChange={(e) => setEditHealth(e.target.value)}
                className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm bg-white font-bold text-green-700"
              >
                <option value="Healthy">Healthy</option>
                <option value="Sick">Sick</option>
                <option value="Under Treatment">Under Treatment</option>
                <option value="Quarantined">Quarantined</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Primary Feed</label>
            <input
              type="text"
              value={editFeed}
              onChange={(e) => setEditFeed(e.target.value)}
              placeholder="e.g., Grain Mix"
              className="block w-full rounded-md border-gray-300 border p-2 text-sm focus:ring-green-500 focus:border-green-500 shadow-sm"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-gray-100 mt-2">
          <button
            type="button"
            onClick={() => setIsEditingInline(false)}
            className="px-3 py-1.5 border border-gray-300 rounded-md text-xs font-bold text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={savingInline}
            className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-md text-xs font-bold shadow-sm transition-all disabled:bg-green-400"
          >
            {savingInline ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all overflow-hidden border-l-4 border-l-green-500 group flex flex-col justify-between h-full">
      <div className="p-5">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-bold text-gray-900 text-lg group-hover:text-green-700 transition-colors">{batch?.batchName}</h3>
            <p className="text-xs text-gray-500 font-medium">{batch?.species}</p>
          </div>
          <div className="bg-green-50 text-green-700 px-3 py-1 rounded-lg border border-green-100 text-center">
             <span className="block text-lg font-bold leading-none">{batch?.headCount}</span>
             <span className="text-[10px] uppercase font-bold tracking-tighter">Animals</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
            <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">Health Status</p>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                batch?.healthStatus === 'Healthy' ? 'bg-green-500' :
                batch?.healthStatus === 'Sick' ? 'bg-red-500' :
                batch?.healthStatus === 'Under Treatment' ? 'bg-yellow-500' : 'bg-orange-500'
              }`}></div>
              <span className="text-xs font-bold text-gray-700">{batch?.healthStatus || 'Healthy'}</span>
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
            <p className="text-[10px] font-bold text-gray-400 uppercase mb-1">Vaccinations</p>
            <div className="flex items-center gap-2 text-blue-600">
              <ShieldCheck className="w-3 h-3" />
              <span className="text-xs font-bold">{batch?.vaccinationStatus}</span>
            </div>
          </div>
        </div>

        <div className="bg-amber-50 p-3 rounded-lg border border-amber-100 flex items-center gap-3">
          <Wheat className="w-5 h-5 text-amber-600" />
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-bold text-amber-600 uppercase">Primary Feed</p>
            <p className="text-xs font-bold text-amber-900 truncate">{batch?.feedType || 'General Forage'}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-gray-50 px-5 py-3 border-t border-gray-100 flex justify-between items-center mt-auto">
        <span className="text-[10px] text-gray-400">Created: {(batch?.createdAt as any)?.seconds ? new Date((batch.createdAt as any).seconds * 1000).toLocaleDateString() : 'Just now'}</span>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsEditingInline(true)}
            className="text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
            title="Edit Batch"
          >
            Edit
          </button>
          <button
            onClick={() => onDelete(batch.id)}
            className="text-slate-400 hover:text-red-600 transition-colors p-1"
            title="Delete Batch"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

const BatchManagement: React.FC<BatchManagementProps> = ({ searchTerm, filterSpecies, onSuccess }) => {
  const { currentUser } = useAuth();
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!currentUser?.uid) return;

    const q = query(
      collection(db, 'batches'),
      where('userId', '==', currentUser.uid),
      orderBy('createdAt', 'desc')
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const batchData: Batch[] = [];
      snapshot.forEach((doc) => {
        batchData.push({ id: doc.id, ...doc.data() } as Batch);
      });
      setBatches(batchData);
      setLoading(false);
    }, (error) => {
      console.error("Error listening to batches:", error);
      setLoading(false);
    });

    return () => unsubscribe();
  }, [currentUser?.uid]);

  const handleSave = async (data: any) => {
    if (!currentUser?.uid) return;
    setSaving(true);
    try {
      await addDoc(collection(db, 'batches'), {
        ...data,
        userId: currentUser.uid,
        createdAt: serverTimestamp()
      });
      onSuccess('Batch created successfully!');
    } catch (err) {
      console.error("Error creating batch:", err);
      alert("Failed to create batch.");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteBatch = async (batchId: string) => {
    if (!window.confirm("Are you sure you want to delete this batch? This will permanently remove it from your inventory.")) return;
    try {
      await deleteDoc(doc(db, 'batches', batchId));
      onSuccess('Batch deleted successfully!');
    } catch (err) {
      console.error("Error deleting batch:", err);
      alert("Failed to delete batch.");
    }
  };

  const filteredBatches = batches.filter(batch => {
    const name = batch?.batchName?.toLowerCase() || '';
    const species = batch?.species || '';
    
    const matchesSearch = 
      name.includes(searchTerm.toLowerCase());
    const matchesFilter = filterSpecies ? species === filterSpecies : true;
    
    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        <p className="text-gray-500 font-medium animate-pulse">Loading batch dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Persistent Inline Batch Entry Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 bg-gray-50">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Plus className="w-5 h-5 text-green-600" /> Create New Batch
          </h2>
        </div>
        <BatchEntryForm onSave={handleSave} saving={saving} />
      </div>

      {/* Dashboard Section */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-green-600" /> Active Batches
          </h2>
          <span className="text-sm font-medium text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
            {filteredBatches.length} Total
          </span>
        </div>
        
        {filteredBatches.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center border-dashed">
            <Users className="mx-auto h-12 w-12 text-gray-400 mb-3" />
            <h3 className="text-gray-900 font-bold text-lg">No batches found</h3>
            <p className="mt-1 text-gray-500 max-w-xs mx-auto">
              {searchTerm || filterSpecies 
                ? "No batches match your current search filters." 
                : "Start managing your groups by creating your first batch using the form above."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredBatches.map((batch) => (
              <BatchCard
                key={batch?.id}
                batch={batch}
                onDelete={handleDeleteBatch}
                onSuccess={onSuccess}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default BatchManagement;
