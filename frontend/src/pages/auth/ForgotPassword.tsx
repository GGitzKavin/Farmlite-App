import React, { useState } from 'react';
import { sendPasswordResetEmail } from 'firebase/auth';
import { Link } from 'react-router-dom';
import { auth } from '../../firebase/config';
import logo from '../../assets/logo.svg';

interface FormErrors {
  email: string;
  form: string;
}

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState<FormErrors>({ email: '', form: '' });
  const [loading, setLoading] = useState(false);
  const [successEmail, setSuccessEmail] = useState('');

  const validateEmail = () => {
    const trimmedEmail = email.trim();

    if (!trimmedEmail) {
      setErrors((current) => ({
        ...current,
        email: 'Email address is required.',
      }));
      return false;
    }

    if (!emailPattern.test(trimmedEmail)) {
      setErrors((current) => ({
        ...current,
        email: 'Please enter a valid email address.',
      }));
      return false;
    }

    setErrors((current) => ({ ...current, email: '' }));
    return true;
  };

  const handleSendReset = async (e?: React.FormEvent) => {
    e?.preventDefault();

    setErrors({ email: '', form: '' });

    if (!validateEmail()) {
      return;
    }

    const trimmedEmail = email.trim();
    setLoading(true);

    try {
      await sendPasswordResetEmail(auth, trimmedEmail);
      setSuccessEmail(trimmedEmail);
    } catch (error) {
      setErrors({
        email: '',
        form: getResetErrorMessage(error),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);

    if (errors.email || errors.form) {
      setErrors({ email: '', form: '' });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-md">
        <div className="flex flex-col items-center">
          <div className="mb-4">
            <img src={logo} alt="FarmLite Logo" className="h-12 w-12 object-contain" />
          </div>
          <h2 className="text-center text-3xl font-extrabold text-gray-900">
            Forgot Password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter the email address associated with your account.
          </p>
          <p className="text-center text-sm text-gray-600">
            We&apos;ll send you a password reset link.
          </p>
        </div>

        {successEmail ? (
          <div className="mt-8 space-y-6">
            <div className="bg-green-50 border-l-4 border-green-400 p-4 rounded-r-lg">
              <p className="text-sm font-semibold text-green-800">
                <span aria-hidden="true">&#10003;</span>{' '}
                Password Reset Email Sent
              </p>
              <p className="mt-2 text-sm text-green-700">
                A password reset link has been sent to:
              </p>
              <p className="mt-1 text-sm font-medium text-green-800 break-all">
                {successEmail}
              </p>
              <p className="mt-3 text-sm text-green-700">
                Please check your inbox and follow the instructions in the email.
              </p>
            </div>

            {errors.form && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4">
                <p className="text-sm text-red-700">{errors.form}</p>
              </div>
            )}

            <div className="space-y-3">
              <Link
                to="/login"
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                Back to Login
              </Link>
              <button
                type="button"
                onClick={() => void handleSendReset()}
                disabled={loading}
                className="group relative w-full flex justify-center py-3 px-4 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-gray-100 disabled:text-gray-400"
              >
                {loading ? 'Sending...' : 'Send Again'}
              </button>
            </div>
          </div>
        ) : (
          <form className="mt-8 space-y-6" onSubmit={handleSendReset}>
            {errors.form && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4">
                <p className="text-sm text-red-700">{errors.form}</p>
              </div>
            )}

            <div className="rounded-md shadow-sm space-y-2">
              <div>
                <label
                  htmlFor="email-address"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Email Address
                </label>
                <input
                  id="email-address"
                  name="email"
                  type="email"
                  className={`appearance-none rounded-lg relative block w-full px-3 py-3 border placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm ${
                    errors.email ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Email address"
                  value={email}
                  onChange={handleEmailChange}
                  onBlur={validateEmail}
                />
                {errors.email && (
                  <p className="mt-2 text-sm text-red-600">{errors.email}</p>
                )}
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </div>

            <div className="text-center">
              <Link to="/login" className="text-sm font-medium text-green-600 hover:text-green-500">
                <span aria-hidden="true">&larr;</span> Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;
