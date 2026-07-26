import React, { useEffect, useState } from 'react';
import { collection, query, where, onSnapshot, addDoc, doc, deleteDoc, updateDoc, serverTimestamp } from 'firebase/firestore';
import { db } from '../../firebase/config';
import { useAuth } from '../../context/AuthContext';
import { Users, Plus, ShieldCheck, Wheat, Trash2, Pencil } from 'lucide-react';
import BatchEntryForm, { type BatchFormSubmission } from './BatchEntryForm';
import type { Batch } from '../../types';
import { getDisplaySpecies, getSpeciesFilterValue } from '../../utils/livestockStatus';
import {
  reconcileOwnedBatches,
  upsertOwnedBatch,
} from '../../features/batchRecords';

interface BatchManagementProps {
  searchTerm: string;
  filterSpecies: string;
  onSuccess: (msg: string) => void;
  onBatchCreated: () => void;
}

const getBatchHealthStyle = (status: string) => {
  if (status === 'Healthy') return 'border-[#606c38]/30 bg-[#606c38]/10 text-[#283618]';
  if (status === 'Sick') return 'border-[#bc6c25]/40 bg-[#bc6c25]/10 text-[#7c3f12]';
  return 'border-[#dda15e]/60 bg-[#fefae0] text-[#7c3f12]';
};

const getBatchVaccinationStyle = (status: string) => {
  if (status === 'Up to date') return 'border-[#606c38]/30 bg-[#606c38]/10 text-[#283618]';
  if (status === 'Overdue') return 'border-[#bc6c25]/40 bg-[#bc6c25]/10 text-[#7c3f12]';
  return 'border-[#dda15e]/60 bg-[#fefae0] text-[#7c3f12]';
};

const BatchCard: React.FC<{
  batch: Batch;
  onDelete: (id: string) => void;
  onSuccess: (msg: string) => void;
}> = ({ batch, onDelete, onSuccess }) => {
  const [isEditingInline, setIsEditingInline] = useState(false);
  const [editName, setEditName] = useState(batch.batchName);
  const [editCount, setEditCount] = useState(batch.headCount);
  const [editFeed, setEditFeed] = useState(batch.feedType ?? '');
  const [editHealth, setEditHealth] = useState(batch.healthStatus ?? 'Healthy');
  const [savingInline, setSavingInline] = useState(false);

  const formatCreatedAt = (createdAt: Batch['createdAt'] | null | undefined) => {
    if (!createdAt) return 'Just now';
    if (createdAt instanceof Date) return createdAt.toLocaleDateString();
    return createdAt.toDate().toLocaleDateString();
  };

  const beginInlineEdit = () => {
    setEditName(batch.batchName);
    setEditCount(batch.headCount);
    setEditFeed(batch.feedType ?? '');
    setEditHealth(batch.healthStatus ?? 'Healthy');
    setIsEditingInline(true);
  };

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
      <form onSubmit={handleSaveInline} className="flex h-full flex-col justify-between space-y-4 overflow-hidden rounded-xl border border-[#dda15e]/70 border-l-4 border-l-[#606c38] bg-white p-5 shadow-sm">
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#283618]">Batch Name *</label>
            <input
              required
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="block w-full rounded-md border border-[#dda15e]/70 p-2 text-sm shadow-sm focus:border-[#606c38] focus:ring-[#606c38]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#283618]">Head Count *</label>
              <input
                required
                type="number"
                min="1"
                value={editCount}
                onChange={(e) => setEditCount(Number(e.target.value))}
                className="block w-full rounded-md border border-[#dda15e]/70 p-2 text-sm shadow-sm focus:border-[#606c38] focus:ring-[#606c38]"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#283618]">Health Status</label>
              <select
                value={editHealth}
                onChange={(e) => setEditHealth(e.target.value)}
                className="block w-full rounded-md border border-[#dda15e]/70 bg-white p-2 text-sm font-semibold text-[#283618] shadow-sm focus:border-[#606c38] focus:ring-[#606c38]"
              >
                <option value="Healthy">Healthy</option>
                <option value="Sick">Sick</option>
                <option value="Under Treatment">Under Treatment</option>
                <option value="Quarantined">Quarantined</option>
              </select>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#283618]">Primary Feed</label>
            <input
              type="text"
              value={editFeed}
              onChange={(e) => setEditFeed(e.target.value)}
              placeholder="e.g., Grain Mix"
              className="block w-full rounded-md border border-[#dda15e]/70 p-2 text-sm shadow-sm focus:border-[#606c38] focus:ring-[#606c38]"
            />
          </div>
        </div>

        <div className="mt-2 flex justify-end gap-2 border-t border-[#dda15e]/30 pt-3">
          <button
            type="button"
            onClick={() => setIsEditingInline(false)}
            className="rounded-md border border-[#dda15e] bg-white px-3 py-1.5 text-xs font-bold text-[#bc6c25] transition-colors hover:bg-[#fefae0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={savingInline}
            className="rounded-lg bg-[#606c38] px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-[#4f5a2f] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#283618] disabled:bg-[#606c38]/60"
          >
            {savingInline ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    );
  }

  return (
    <article className="group flex h-full flex-col justify-between overflow-hidden rounded-xl border border-[#dda15e]/70 border-l-4 border-l-[#606c38] bg-white shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
      <div className="p-5">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-bold text-[#283618] transition-colors group-hover:text-[#606c38]">{batch?.batchName}</h3>
            <p className="text-xs text-gray-500 font-medium">{getDisplaySpecies(batch?.species)}</p>
          </div>
          <div className="rounded-lg border border-[#606c38]/30 bg-[#fefae0] px-3 py-1 text-center text-[#283618]">
             <span className="block text-lg font-bold leading-none">{batch?.headCount}</span>
             <span className="text-[10px] uppercase font-bold tracking-tighter">Livestock</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className={`rounded-lg border p-3 ${getBatchHealthStyle(batch?.healthStatus || 'Healthy')}`}>
            <p className="mb-1 text-[10px] font-bold uppercase">Health Status</p>
            <p className="text-xs font-bold">{batch?.healthStatus || 'Healthy'}</p>
          </div>
          <div className={`rounded-lg border p-3 ${getBatchVaccinationStyle(batch?.vaccinationStatus || 'No records')}`}>
            <p className="mb-1 text-[10px] font-bold uppercase">Vaccinations</p>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-3 h-3" />
              <span className="text-xs font-bold">{batch?.vaccinationStatus || 'No records'}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 rounded-lg border border-[#dda15e]/60 bg-[#fefae0] p-3">
          <Wheat className="w-5 h-5 text-[#bc6c25]" />
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-bold uppercase text-[#bc6c25]">Primary Feed</p>
            <p className="truncate text-xs font-bold text-[#283618]">{batch?.feedType || 'General Forage'}</p>
          </div>
        </div>
      </div>

      <div className="mt-auto flex flex-col gap-3 border-t border-[#dda15e]/30 bg-[#fefae0]/60 px-5 py-3 sm:flex-row sm:items-center sm:justify-between">
        <span className="text-[10px] text-gray-400">Created: {formatCreatedAt(batch.createdAt)}</span>

        <div className="flex items-center gap-3">
          <button
            onClick={beginInlineEdit}
            className="inline-flex items-center rounded-lg bg-[#dda15e] px-3 py-2 text-sm font-medium text-[#283618] shadow-sm transition-colors hover:bg-[#cf8f4b] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
            title="Edit Batch"
          >
            <Pencil className="mr-1.5 h-4 w-4" />
            Edit
          </button>
          <button
            onClick={() => onDelete(batch.id)}
            className="inline-flex items-center rounded-lg bg-[#bc6c25] px-3 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-[#9f571d] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#283618]"
            title="Delete Batch"
          >
            <Trash2 className="mr-1.5 h-4 w-4" />
            Delete
          </button>
        </div>
      </div>
    </article>
  );
};

const BatchManagement: React.FC<BatchManagementProps> = ({
  searchTerm,
  filterSpecies,
  onSuccess,
  onBatchCreated,
}) => {
  const { currentUser } = useAuth();
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [listError, setListError] = useState('');

  useEffect(() => {
    if (!currentUser?.uid) return;
    const currentUserId = currentUser.uid;

    // Keep the ownership predicate in Firestore, but sort locally so this
    // listener does not depend on a userId + createdAt composite index.
    const q = query(
      collection(db, 'batches'),
      where('userId', '==', currentUserId)
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const batchData: Batch[] = [];
      snapshot.forEach((doc) => {
        batchData.push({ id: doc.id, ...doc.data() } as Batch);
      });
      setBatches(reconcileOwnedBatches(batchData, currentUserId));
      setListError('');
      setLoading(false);
    }, (error) => {
      console.error("Error listening to batches:", error);
      setListError('Batch Management could not load the latest batches. Please try again.');
      setLoading(false);
    });

    return () => unsubscribe();
  }, [currentUser?.uid]);

  const handleSave = async (data: BatchFormSubmission) => {
    if (!currentUser?.uid) return;
    const currentUserId = currentUser.uid;
    setSaving(true);
    try {
      const savedDocument = await addDoc(collection(db, 'batches'), {
        ...data,
        userId: currentUserId,
        createdAt: serverTimestamp()
      });

      setBatches((currentBatches) =>
        upsertOwnedBatch(
          currentBatches,
          {
            id: savedDocument.id,
            ...data,
            userId: currentUserId,
            createdAt: new Date(),
          },
          currentUserId
        )
      );
      setListError('');
      onBatchCreated();
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
    if (batch.userId !== currentUser?.uid) return false;
    const name = batch?.batchName?.toLowerCase() || '';
    const species = batch?.species || '';

    const matchesSearch =
      name.includes(searchTerm.toLowerCase());
    const matchesFilter = filterSpecies
      ? getSpeciesFilterValue(species) === filterSpecies
      : true;

    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-[#606c38]"></div>
        <p className="animate-pulse font-medium text-[#283618]">Loading Batch Management...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 rounded-xl bg-[#fefae0]/50 p-1 sm:p-3">
      {/* Persistent Inline Batch Entry Card */}
      <section className="overflow-hidden rounded-xl border border-[#dda15e]/70 bg-white shadow-sm">
        <div className="border-b border-[#dda15e]/40 bg-[#fefae0] p-4">
          <h2 className="flex items-center gap-2 text-lg font-bold text-[#283618]">
            <Plus className="w-5 h-5 text-[#606c38]" /> Create New Batch
          </h2>
        </div>
        <BatchEntryForm onSave={handleSave} saving={saving} />
      </section>

      {/* Dashboard Section */}
      <section aria-labelledby="active-batches-title">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 id="active-batches-title" className="flex items-center gap-2 text-xl font-bold text-[#283618]">
            <Users className="w-6 h-6 text-[#606c38]" /> Active Batches
          </h2>
          <span className="w-fit rounded-full border border-[#dda15e]/60 bg-[#dda15e]/20 px-3 py-1 text-sm font-semibold text-[#283618]">
            {filteredBatches.length} Total
          </span>
        </div>

        {listError ? (
          <div
            role="alert"
            className="mb-5 rounded-lg border border-[#bc6c25]/50 bg-[#fefae0] p-4 text-sm font-medium text-[#7c3f12]"
          >
            {listError}
          </div>
        ) : null}

        {filteredBatches.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[#dda15e] bg-[#fefae0] p-8 text-center sm:p-12">
            <Users className="mx-auto mb-3 h-12 w-12 text-[#606c38]" />
            <h3 className="text-lg font-bold text-[#283618]">No batches found</h3>
            <p className="mx-auto mt-1 max-w-xs text-gray-600">
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
      </section>
    </div>
  );
};

export default BatchManagement;
