import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  doc,
  getDoc,
  collection,
  query,
  where,
  getDocs,
  updateDoc,
  writeBatch,
} from 'firebase/firestore';
import { db } from '../../firebase/config';
import { useAuth } from '../../context/AuthContext';
import type { Livestock, HealthRecord, Vaccination } from '../../types';
import {
  ArrowLeft,
  Trash2,
  Activity,
  Syringe,
  FileText,
  Pencil,
  Save,
} from 'lucide-react';
import {
  calculateAgeInMonths,
  getDerivedHealthStatus,
  getHealthBadgeStyle,
  parseDateValue,
  getVaccinationStatus,
  getVaccinationStatusStyle,
  getDisplaySpecies,
  normalizeHealthStatus,
} from '../../utils/livestockStatus';
import {
  buildInlineLivestockUpdate,
  createInlineLivestockForm,
  EMPTY_INLINE_LIVESTOCK_FORM,
  getInlineLivestockTypeOptions,
  type InlineLivestockEditFormData,
} from '../../features/inlineLivestockEdit';

const LivestockDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [animal, setAnimal] = useState<Livestock | null>(null);
  const [healthRecords, setHealthRecords] = useState<HealthRecord[]>([]);
  const [vaccinations, setVaccinations] = useState<Vaccination[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(
    () => searchParams.get('edit') === 'true'
  );
  const [editForm, setEditForm] = useState<InlineLivestockEditFormData>({
    ...EMPTY_INLINE_LIVESTOCK_FORM,
  });
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

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
          const loadedAnimal = {
            id: docSnap.id,
            ...docSnap.data(),
          } as Livestock;
          setAnimal(loadedAnimal);
          setEditForm(createInlineLivestockForm(loadedAnimal));
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

  const handleStartEditing = () => {
    if (!animal || !id) return;
    setEditForm(createInlineLivestockForm(animal));
    setEditError('');
    setSuccessMessage('');
    setIsEditing(true);
    navigate(`/livestock/${id}?edit=true`, { replace: true });
  };

  const handleCancelEditing = () => {
    if (!animal || !id) return;
    setEditForm(createInlineLivestockForm(animal));
    setEditError('');
    setIsEditing(false);
    navigate(`/livestock/${id}`, { replace: true });
  };

  const handleEditChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = event.target;
    setEditError('');
    setEditForm((previous) => {
      if (name !== 'birthDate') {
        return { ...previous, [name]: value };
      }

      const derivedAge = calculateAgeInMonths(value);
      return {
        ...previous,
        birthDate: value,
        age: value && derivedAge !== null ? String(derivedAge) : previous.age,
      };
    });
  };

  const handleSaveChanges = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!animal || !id || !currentUser || animal.userId !== currentUser.uid) {
      setEditError('This livestock record is not available for editing.');
      return;
    }

    const update = buildInlineLivestockUpdate(editForm);
    if (!update.value) {
      setEditError(update.error);
      return;
    }

    setSaving(true);
    setEditError('');
    try {
      const updatedAt = new Date();
      await updateDoc(doc(db, 'livestock', id), {
        ...update.value,
        updatedAt,
      });

      const updatedAnimal: Livestock = {
        ...animal,
        ...update.value,
        updatedAt,
      };
      setAnimal(updatedAnimal);
      setEditForm(createInlineLivestockForm(updatedAnimal));
      setIsEditing(false);
      setSuccessMessage('Livestock details updated successfully.');
      navigate(`/livestock/${id}`, { replace: true });
    } catch (saveError) {
      console.error('Failed to update livestock:', saveError);
      setEditError('Could not save livestock changes. Please try again.');
    } finally {
      setSaving(false);
    }
  };

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
  const displaySpecies = getDisplaySpecies(animal.species);
  const latestHealthRecord = sortedHealthRecords[0] ?? null;
  const dateAdded = parseDateValue(animal.createdAt)?.toLocaleDateString() ?? 'Unavailable';
  const batchAssignment = animal.batchName || animal.batchId || 'Not assigned';
  const livestockTypeOptions = getInlineLivestockTypeOptions(editForm.species);
  const hasLegacyLivestockType = livestockTypeOptions.some(
    (option) => option.legacy && option.value === editForm.species
  );

  return (
    <div className="min-w-0 space-y-6 overflow-x-hidden">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div className="flex items-center gap-4">
          <Link
            to="/livestock"
            aria-label="Back to Livestock"
            className="rounded-md border border-[#dda15e]/70 bg-white p-2 text-[#283618] hover:bg-[#fefae0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-[#283618]">{animal.animalName}</h1>
            <p className="text-sm text-gray-500">ID: {animal.animalId} &bull; {displaySpecies}</p>
          </div>
        </div>
        <div className="flex w-full items-center gap-2 sm:w-auto">
          <button
            type="button"
            onClick={handleDelete}
            className="inline-flex flex-1 items-center justify-center rounded-lg bg-[#bc6c25] px-3 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-[#9f571d] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#283618] sm:flex-none"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </button>
        </div>
      </div>

      <section
        aria-labelledby="animal-profile-title"
        className="rounded-xl border border-[#dda15e]/60 bg-white p-5 shadow-sm sm:p-6"
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h2 id="animal-profile-title" className="flex items-center text-xl font-bold text-[#283618]">
            <FileText className="mr-2 h-5 w-5 text-[#606c38]" />
            Animal Profile
          </h2>
          {!isEditing ? (
            <button
              type="button"
              onClick={handleStartEditing}
              className="inline-flex w-full items-center justify-center rounded-lg bg-[#dda15e] px-4 py-2 text-sm font-semibold text-[#283618] shadow-sm transition-colors hover:bg-[#cf8f4b] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38] sm:w-auto"
            >
              <Pencil aria-hidden="true" className="mr-2 h-4 w-4" />
              Edit Livestock
            </button>
          ) : null}
        </div>

        {successMessage ? (
          <p
            role="status"
            className="mt-5 rounded-lg border border-[#606c38]/40 bg-[#fefae0] px-4 py-3 text-sm font-medium text-[#283618]"
          >
            {successMessage}
          </p>
        ) : null}

        {isEditing ? (
          <form
            aria-label="Edit livestock details"
            aria-busy={saving}
            onSubmit={handleSaveChanges}
            className="mt-5 min-w-0 space-y-5 overflow-hidden"
          >
            {editError ? (
              <p
                id="inline-livestock-edit-error"
                role="alert"
                className="rounded-lg border border-[#bc6c25]/50 bg-[#fefae0] px-4 py-3 text-sm font-medium text-[#8b4518]"
              >
                {editError}
              </p>
            ) : null}

            <div className="grid min-w-0 grid-cols-1 gap-4 md:grid-cols-2">
              <div className="min-w-0">
                <label htmlFor="inline-animal-id" className="block text-sm font-semibold text-[#283618]">
                  Animal ID / Tag
                </label>
                <input
                  id="inline-animal-id"
                  required
                  type="text"
                  name="animalId"
                  value={editForm.animalId}
                  onChange={handleEditChange}
                  aria-describedby={editError ? 'inline-livestock-edit-error' : undefined}
                  className="mt-1 block w-full min-w-0 rounded-lg border border-[#dda15e] bg-white px-3 py-2 text-[#283618] shadow-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
                />
              </div>

              <div className="min-w-0">
                <label htmlFor="inline-animal-name" className="block text-sm font-semibold text-[#283618]">
                  Animal Name
                </label>
                <input
                  id="inline-animal-name"
                  required
                  type="text"
                  name="animalName"
                  value={editForm.animalName}
                  onChange={handleEditChange}
                  className="mt-1 block w-full min-w-0 rounded-lg border border-[#dda15e] bg-white px-3 py-2 text-[#283618] shadow-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
                />
              </div>

              <div className="min-w-0">
                <label htmlFor="inline-livestock-type" className="block text-sm font-semibold text-[#283618]">
                  Livestock
                </label>
                <select
                  id="inline-livestock-type"
                  name="species"
                  value={editForm.species}
                  onChange={handleEditChange}
                  className="mt-1 block w-full min-w-0 rounded-lg border border-[#dda15e] bg-white px-3 py-2 text-[#283618] shadow-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
                >
                  {livestockTypeOptions.map((option) => (
                    <option
                      key={`${option.legacy ? 'legacy' : 'approved'}-${option.value}`}
                      value={option.value}
                      disabled={option.legacy}
                    >
                      {option.label}
                    </option>
                  ))}
                </select>
                {hasLegacyLivestockType ? (
                  <p className="mt-1 text-xs text-[#bc6c25]">
                    This stored legacy value is retained unless you choose an approved livestock type.
                  </p>
                ) : null}
              </div>

              <div className="min-w-0">
                <label htmlFor="inline-breed" className="block text-sm font-semibold text-[#283618]">
                  Breed
                </label>
                <input
                  id="inline-breed"
                  required
                  type="text"
                  name="breed"
                  value={editForm.breed}
                  onChange={handleEditChange}
                  className="mt-1 block w-full min-w-0 rounded-lg border border-[#dda15e] bg-white px-3 py-2 text-[#283618] shadow-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
                />
              </div>

              <div className="min-w-0">
                <label htmlFor="inline-birth-date" className="block text-sm font-semibold text-[#283618]">
                  Birth Date
                </label>
                <input
                  id="inline-birth-date"
                  type="date"
                  name="birthDate"
                  value={editForm.birthDate}
                  onChange={handleEditChange}
                  className="mt-1 block w-full min-w-0 rounded-lg border border-[#dda15e] bg-white px-3 py-2 text-[#283618] shadow-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
                />
              </div>

              <div className="min-w-0">
                <label htmlFor="inline-age" className="block text-sm font-semibold text-[#283618]">
                  Age (Months)
                </label>
                <input
                  id="inline-age"
                  type="number"
                  min="0"
                  name="age"
                  value={editForm.age}
                  onChange={handleEditChange}
                  readOnly={Boolean(editForm.birthDate)}
                  className={`mt-1 block w-full min-w-0 rounded-lg border px-3 py-2 text-[#283618] shadow-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38] ${
                    editForm.birthDate
                      ? 'cursor-not-allowed border-[#dda15e]/40 bg-[#fefae0]'
                      : 'border-[#dda15e] bg-white'
                  }`}
                />
              </div>

              <div className="min-w-0">
                <label htmlFor="inline-weight" className="block text-sm font-semibold text-[#283618]">
                  Weight (kg)
                </label>
                <input
                  id="inline-weight"
                  required
                  type="number"
                  min="0.1"
                  step="0.1"
                  name="weight"
                  value={editForm.weight}
                  onChange={handleEditChange}
                  className="mt-1 block w-full min-w-0 rounded-lg border border-[#dda15e] bg-white px-3 py-2 text-[#283618] shadow-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
                />
              </div>
            </div>

            <div className="flex flex-col-reverse gap-3 border-t border-[#dda15e]/50 pt-5 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={handleCancelEditing}
                disabled={saving}
                className="inline-flex w-full items-center justify-center rounded-lg border border-[#606c38] bg-white px-4 py-2 text-sm font-semibold text-[#606c38] hover:bg-[#fefae0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38] disabled:opacity-60 sm:w-auto"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="inline-flex w-full items-center justify-center rounded-lg bg-[#606c38] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#4f5a2f] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#283618] disabled:opacity-60 sm:w-auto"
              >
                <Save aria-hidden="true" className="mr-2 h-4 w-4" />
                {saving ? 'Saving Changes...' : 'Save Changes'}
              </button>
            </div>
          </form>
        ) : (
          <>
            <dl className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <ProfileValue label="Animal Name" value={animal.animalName} />
              <ProfileValue label="Animal ID / Tag" value={animal.animalId} />
              <ProfileValue label="Livestock Type" value={displaySpecies} />
              <ProfileValue label="Breed" value={animal.breed || 'Unavailable'} />
              <ProfileValue label="Age" value={`${animal.age} months`} />
              <ProfileValue label="Weight" value={`${animal.weight} kg`} />
              <ProfileValue label="Birth Date" value={animal.birthDate || 'Unavailable'} />
              <ProfileValue label="Date Added" value={dateAdded} />
              <ProfileValue label="Batch Assignment" value={batchAssignment} />
            </dl>

            {animal.notes ? (
              <div className="mt-5 rounded-lg border border-[#dda15e]/60 bg-[#fefae0] p-4">
                <h3 className="text-sm font-semibold text-[#283618]">Management Notes</h3>
                <p className="mt-1 whitespace-pre-wrap text-sm text-gray-700">{animal.notes}</p>
              </div>
            ) : null}
          </>
        )}
      </section>

      <section
        aria-labelledby="health-status-title"
        className="rounded-xl border border-[#dda15e]/60 bg-white p-5 shadow-sm sm:p-6"
      >
        <h2 id="health-status-title" className="flex items-center text-xl font-bold text-[#283618]">
          <Activity className="mr-2 h-5 w-5 text-[#606c38]" />
          Health Status
        </h2>
        <div className={`mt-5 rounded-lg border p-4 ${getHealthBadgeStyle(derivedHealthStatus, 'card')}`}>
          <p className="text-lg font-bold">{derivedHealthStatus}</p>
          <p className="mt-1 text-sm text-gray-700">
            Based on the latest health tracking record when available.
          </p>
        </div>

        {latestHealthRecord ? (
          <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <h3 className="font-semibold text-[#283618]">Latest Recorded Health Information</h3>
            <dl className="mt-3 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-medium text-gray-500">Condition</dt>
                <dd className="mt-1 text-gray-900">{latestHealthRecord.diseaseType || 'Unavailable'}</dd>
              </div>
              <div>
                <dt className="font-medium text-gray-500">Recorded</dt>
                <dd className="mt-1 text-gray-900">
                  {parseDateValue(latestHealthRecord.updatedAt)?.toLocaleDateString() ||
                    parseDateValue(latestHealthRecord.createdAt)?.toLocaleDateString() ||
                    'Unavailable'}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="font-medium text-gray-500">Current Notes</dt>
                <dd className="mt-1 whitespace-pre-wrap text-gray-900">
                  {latestHealthRecord.vetNotes ||
                    latestHealthRecord.treatment ||
                    latestHealthRecord.symptoms ||
                    'No current health notes were recorded.'}
                </dd>
              </div>
            </dl>
          </div>
        ) : (
          <p className="mt-4 text-sm text-gray-600">No health records are available for this animal.</p>
        )}
      </section>

      <section
        aria-labelledby="medical-vaccinations-title"
        className="rounded-xl border border-[#dda15e]/60 bg-white p-5 shadow-sm sm:p-6"
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h2 id="medical-vaccinations-title" className="flex items-center text-xl font-bold text-[#283618]">
            <Syringe className="mr-2 h-5 w-5 text-[#606c38]" />
            Medical and Vaccinations
          </h2>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Link
              to="/health"
              className="inline-flex items-center justify-center rounded-lg border border-[#606c38] px-3 py-2 text-sm font-medium text-[#606c38] hover:bg-[#fefae0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
            >
              Add Health Record
            </Link>
            <Link
              to="/vaccinations"
              className="inline-flex items-center justify-center rounded-lg bg-[#606c38] px-3 py-2 text-sm font-medium text-white hover:bg-[#4f5a2f] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#283618]"
            >
              Record Vaccination
            </Link>
          </div>
        </div>

        <div className={`mt-5 rounded-lg border p-4 ${getVaccinationStatusStyle(derivedVaccinationStatus, 'card')}`}>
          <p className="text-sm font-medium">Vaccination Status</p>
          <p className="mt-1 text-lg font-bold">{derivedVaccinationStatus}</p>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-8 xl:grid-cols-2">
          <div className="min-w-0">
            <h3 className="font-bold text-[#283618]">Vaccination History</h3>
            {sortedVaccinations.length > 0 ? (
              <ul className="mt-4 space-y-3">
                {sortedVaccinations.map((vaccination) => {
                  const status = getVaccinationStatus([vaccination]);
                  return (
                    <li key={vaccination.id} className="rounded-lg border border-gray-200 p-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <p className="font-semibold text-[#283618]">{vaccination.vaccineName}</p>
                        <span className={`w-fit rounded-full px-2.5 py-1 text-xs font-semibold ${getVaccinationStatusStyle(status, 'badge')}`}>
                          {status}
                        </span>
                      </div>
                      <dl className="mt-3 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
                        <div>
                          <dt className="text-gray-500">Date administered</dt>
                          <dd className="font-medium text-gray-900">{vaccination.vaccinationDate || 'Unavailable'}</dd>
                        </div>
                        <div>
                          <dt className="text-gray-500">Next due date</dt>
                          <dd className="font-medium text-gray-900">{vaccination.nextDueDate || 'Unavailable'}</dd>
                        </div>
                      </dl>
                      {vaccination.notes ? (
                        <p className="mt-3 whitespace-pre-wrap text-sm text-gray-700">{vaccination.notes}</p>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            ) : (
              <div className="mt-4 rounded-lg border border-dashed border-[#dda15e] bg-[#fefae0] p-5 text-sm text-gray-700">
                No vaccination records found for this animal.
              </div>
            )}
          </div>

          <div className="min-w-0">
            <h3 className="font-bold text-[#283618]">Medical History</h3>
            {sortedHealthRecords.length > 0 ? (
              <div className="mt-4 space-y-3">
                {sortedHealthRecords.map((record) => (
                  <article key={record.id} className="rounded-lg border border-gray-200 p-4">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <p className="font-semibold text-[#283618]">{record.diseaseType || 'Health record'}</p>
                      <span className={`w-fit rounded-full px-2.5 py-1 text-xs font-semibold ${getHealthBadgeStyle(normalizeHealthStatus(record.recoveryStatus), 'badge')}`}>
                        {record.recoveryStatus}
                      </span>
                    </div>
                    <div className="mt-3 space-y-2 text-sm text-gray-700">
                      <p><strong>Symptoms:</strong> {record.symptoms || 'Not recorded'}</p>
                      <p><strong>Treatment:</strong> {record.treatment || 'Not recorded'}</p>
                      {record.medicine ? <p><strong>Medicine:</strong> {record.medicine}</p> : null}
                      {record.vetNotes ? <p><strong>Notes:</strong> {record.vetNotes}</p> : null}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="mt-4 rounded-lg border border-dashed border-[#dda15e] bg-[#fefae0] p-5 text-sm text-gray-700">
                No medical history found for this animal.
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

const ProfileValue: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="rounded-lg border border-[#dda15e]/30 bg-[#fefae0]/70 p-4">
    <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</dt>
    <dd className="mt-1 break-words text-base font-medium text-[#283618]">{value}</dd>
  </div>
);

export default LivestockDetail;
