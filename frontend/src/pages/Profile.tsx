import React, { useEffect, useMemo, useState } from 'react';
import { sendPasswordResetEmail } from 'firebase/auth';
import { doc, getDoc, serverTimestamp, setDoc } from 'firebase/firestore';
import { Building2, Lock, Save, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import { auth, db } from '../firebase/config';
import { useAuth } from '../context/AuthContext';
import {
  FARM_TYPE_MAX_LENGTH,
  loadFarmType,
  normalizeFarmType,
  validateFarmType,
} from '../features/profileForm';

interface OwnerFormState {
  fullName: string;
  email: string;
  phone: string;
}

interface FarmFormState {
  farmName: string;
  farmLocation: string;
  farmType: string;
  farmContactNumber: string;
}

interface FeedbackState {
  type: 'success' | 'error';
  message: string;
}

const getResetErrorMessage = (error: unknown) => {
  const errorCode =
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    typeof error.code === 'string'
      ? error.code
      : '';

  switch (errorCode) {
    case 'auth/invalid-email':
      return 'Please enter a valid email address.';
    case 'auth/user-not-found':
      return 'No account exists with this email.';
    case 'auth/too-many-requests':
      return 'Too many attempts. Please try again later.';
    default:
      return 'Unable to send reset email. Please try again.';
  }
};

const Profile: React.FC = () => {
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [savingSection, setSavingSection] = useState<'owner' | 'farm' | 'security' | null>(null);
  const [loadError, setLoadError] = useState('');
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);
  const [farmTypeError, setFarmTypeError] = useState('');
  const [ownerForm, setOwnerForm] = useState<OwnerFormState>({
    fullName: '',
    email: '',
    phone: '',
  });
  const [farmForm, setFarmForm] = useState<FarmFormState>({
    farmName: '',
    farmLocation: '',
    farmType: '',
    farmContactNumber: '',
  });

  const currentUserId = currentUser?.uid;
  const userDocRef = useMemo(() => {
    if (!currentUserId) return null;
    return doc(db, 'users', currentUserId);
  }, [currentUserId]);

  useEffect(() => {
    const loadProfile = async () => {
      if (!currentUser || !userDocRef) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setLoadError('');
      setFeedback(null);

      try {
        const snapshot = await getDoc(userDocRef);
        const data = snapshot.exists() ? snapshot.data() : {};

        setOwnerForm({
          fullName:
            (typeof data.fullName === 'string' && data.fullName) ||
            (typeof data.name === 'string' && data.name) ||
            currentUser.displayName ||
            '',
          email: currentUser.email || '',
          phone: typeof data.phone === 'string' ? data.phone : '',
        });

        setFarmForm({
          farmName: typeof data.farmName === 'string' ? data.farmName : '',
          farmLocation:
            (typeof data.farmLocation === 'string' && data.farmLocation) ||
            (typeof data.farmAddress === 'string' && data.farmAddress) ||
            '',
          farmType: loadFarmType(data.farmType),
          farmContactNumber:
            typeof data.farmContactNumber === 'string' ? data.farmContactNumber : '',
        });
      } catch (error) {
        console.error('Failed to load profile:', error);
        setLoadError('Unable to load your profile right now. Please try again.');
        setOwnerForm({
          fullName: currentUser.displayName || '',
          email: currentUser.email || '',
          phone: '',
        });
        setFarmForm({
          farmName: '',
          farmLocation: '',
          farmType: '',
          farmContactNumber: '',
        });
      } finally {
        setLoading(false);
      }
    };

    void loadProfile();
  }, [currentUser, userDocRef]);

  const handleOwnerChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = e.target;
    setOwnerForm((current) => ({ ...current, [name]: value }));
    if (feedback) setFeedback(null);
  };

  const handleFarmChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = e.target;
    setFarmForm((current) => ({ ...current, [name]: value }));
    if (name === 'farmType' && farmTypeError) setFarmTypeError('');
    if (feedback) setFeedback(null);
  };

  const handleSaveOwnerDetails = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser || !userDocRef) return;

    if (!ownerForm.fullName.trim()) {
      setFeedback({
        type: 'error',
        message: 'Full name is required.',
      });
      return;
    }

    setSavingSection('owner');
    setFeedback(null);

    try {
      await setDoc(
        userDocRef,
        {
          uid: currentUser.uid,
          fullName: ownerForm.fullName.trim(),
          email: currentUser.email || '',
          phone: ownerForm.phone.trim(),
          updatedAt: serverTimestamp(),
        },
        { merge: true }
      );

      setFeedback({
        type: 'success',
        message: 'Owner details saved successfully.',
      });
    } catch (error) {
      console.error('Failed to save owner details:', error);
      setFeedback({
        type: 'error',
        message: 'Unable to save owner details right now. Please try again.',
      });
    } finally {
      setSavingSection(null);
    }
  };

  const handleSaveFarmDetails = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser || !userDocRef) return;

    if (!farmForm.farmName.trim()) {
      setFeedback({
        type: 'error',
        message: 'Farm name is required.',
      });
      return;
    }

    const nextFarmTypeError = validateFarmType(farmForm.farmType);
    if (nextFarmTypeError) {
      setFarmTypeError(nextFarmTypeError);
      setFeedback({
        type: 'error',
        message: nextFarmTypeError,
      });
      return;
    }

    setSavingSection('farm');
    setFarmTypeError('');
    setFeedback(null);

    try {
      await setDoc(
        userDocRef,
        {
          uid: currentUser.uid,
          email: currentUser.email || '',
          farmName: farmForm.farmName.trim(),
          farmLocation: farmForm.farmLocation.trim(),
          farmType: normalizeFarmType(farmForm.farmType),
          farmContactNumber: farmForm.farmContactNumber.trim(),
          updatedAt: serverTimestamp(),
        },
        { merge: true }
      );

      setFeedback({
        type: 'success',
        message: 'Farm details saved successfully.',
      });
    } catch (error) {
      console.error('Failed to save farm details:', error);
      setFeedback({
        type: 'error',
        message: 'Unable to save farm details right now. Please try again.',
      });
    } finally {
      setSavingSection(null);
    }
  };

  const handleSendPasswordReset = async () => {
    if (!currentUser?.email) {
      setFeedback({
        type: 'error',
        message: 'No email address is available for this account.',
      });
      return;
    }

    setSavingSection('security');
    setFeedback(null);

    try {
      await sendPasswordResetEmail(auth, currentUser.email);
      setFeedback({
        type: 'success',
        message: 'Password reset email sent. Please check your inbox.',
      });
    } catch (error) {
      setFeedback({
        type: 'error',
        message: getResetErrorMessage(error),
      });
    } finally {
      setSavingSection(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="flex items-center gap-3 text-2xl font-bold text-gray-900">
        <User className="h-7 w-7 text-[#606c38]" />
        Profile
      </h1>

      {loadError ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4">
          <p className="text-sm text-red-700">{loadError}</p>
        </div>
      ) : null}

      {feedback ? (
        <div
          role={feedback.type === 'error' ? 'alert' : 'status'}
          className={`rounded-xl border px-5 py-4 ${
            feedback.type === 'success'
              ? 'border-green-200 bg-green-50'
              : 'border-red-200 bg-red-50'
          }`}
        >
          <p
            className={`text-sm ${
              feedback.type === 'success' ? 'text-green-700' : 'text-red-700'
            }`}
          >
            {feedback.message}
          </p>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <form
          onSubmit={handleSaveOwnerDetails}
          className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-gray-900">Owner Information</h2>
          <div className="mt-5 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Full Name</label>
              <input
                required
                type="text"
                name="fullName"
                value={ownerForm.fullName}
                onChange={handleOwnerChange}
                className="mt-1 block w-full rounded-md border border-gray-300 p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Email Address</label>
              <input
                readOnly
                type="email"
                value={ownerForm.email}
                className="mt-1 block w-full rounded-md border border-gray-200 bg-gray-50 p-2 text-gray-500 shadow-sm sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Phone Number</label>
              <input
                type="text"
                name="phone"
                value={ownerForm.phone}
                onChange={handleOwnerChange}
                className="mt-1 block w-full rounded-md border border-gray-300 p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              type="submit"
              disabled={savingSection === 'owner'}
              className="inline-flex items-center rounded-lg bg-[#606c38] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#4f5a2f] disabled:bg-[#606c38]/60"
            >
              <Save className="mr-2 h-4 w-4" />
              {savingSection === 'owner' ? 'Saving...' : 'Save Owner Details'}
            </button>
          </div>
        </form>

        <form
          onSubmit={handleSaveFarmDetails}
          className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
        >
          <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
            <Building2 className="h-5 w-5 text-green-600" />
            Farm Information
          </h2>
          <div className="mt-5 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Farm Name</label>
              <input
                required
                type="text"
                name="farmName"
                value={farmForm.farmName}
                onChange={handleFarmChange}
                className="mt-1 block w-full rounded-md border border-gray-300 p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Farm Address / Location
              </label>
              <input
                type="text"
                name="farmLocation"
                value={farmForm.farmLocation}
                onChange={handleFarmChange}
                className="mt-1 block w-full rounded-md border border-gray-300 p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
              />
            </div>

            <div>
              <label htmlFor="farm-type" className="block text-sm font-medium text-gray-700">
                Farm Type
              </label>
              <input
                id="farm-type"
                type="text"
                name="farmType"
                value={farmForm.farmType}
                onChange={handleFarmChange}
                placeholder="Enter farm type"
                maxLength={FARM_TYPE_MAX_LENGTH}
                aria-invalid={Boolean(farmTypeError)}
                aria-describedby={
                  farmTypeError ? 'farm-type-help farm-type-error' : 'farm-type-help'
                }
                className="mt-1 block w-full rounded-md border border-gray-300 p-2 shadow-sm focus:border-[#606c38] focus:ring-[#606c38] sm:text-sm"
              />
              <p id="farm-type-help" className="mt-1 text-xs text-gray-500">
                Enter the description your farm uses.
              </p>
              {farmTypeError ? (
                <p id="farm-type-error" role="alert" className="mt-1 text-sm text-[#bc6c25]">
                  {farmTypeError}
                </p>
              ) : null}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Farm Contact Number
              </label>
              <input
                type="text"
                name="farmContactNumber"
                value={farmForm.farmContactNumber}
                onChange={handleFarmChange}
                className="mt-1 block w-full rounded-md border border-gray-300 p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm"
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              type="submit"
              disabled={savingSection === 'farm'}
              className="inline-flex items-center rounded-lg bg-[#606c38] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#4f5a2f] disabled:bg-[#606c38]/60"
            >
              <Save className="mr-2 h-4 w-4" />
              {savingSection === 'farm' ? 'Saving...' : 'Save Farm Details'}
            </button>
          </div>
        </form>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(280px,0.8fr)]">
        <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">Account Security</h2>
          <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-50 p-3">
                <Lock className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">Password</p>
                <p className="text-base font-semibold text-gray-900">************</p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => void handleSendPasswordReset()}
              disabled={savingSection === 'security'}
              className="inline-flex items-center justify-center rounded-lg bg-[#606c38] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#4f5a2f] disabled:bg-[#606c38]/60"
            >
              {savingSection === 'security'
                ? 'Sending...'
                : 'Send Password Reset Email'}
            </button>
          </div>
        </section>

        <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">About FarmLite</h2>
          <Link
            to="/"
            className="mt-4 inline-flex w-full cursor-pointer items-center justify-center rounded-lg bg-[#606c38] px-4 py-2.5 text-sm font-medium text-white no-underline shadow-sm transition-all hover:-translate-y-px hover:bg-[#283618] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#dda15e] sm:w-fit"
          >
            Visit FarmLite Landing Page
          </Link>
          <div className="mt-4 space-y-3 text-sm text-gray-600">
            <p>
              <span className="font-medium text-gray-900">FarmLite Version:</span> v1.0
            </p>
            <p>AI-assisted livestock management and decision-support system.</p>
            <p className="pt-2 text-xs text-gray-500">© 2026 FarmLite</p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Profile;
