import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';

// Layouts
import MainLayout from './layouts/MainLayout';

// Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ForgotPassword from './pages/auth/ForgotPassword';
import Dashboard from './pages/Dashboard';

import LivestockList from './pages/Livestock/LivestockList';
import LivestockDetail from './pages/Livestock/LivestockDetail';
import EditLivestock from './pages/Livestock/EditLivestock';
import VaccinationManagement from './pages/Vaccinations';
import FeedInventoryPage from './pages/FeedInventory';
import HealthTracking from './pages/HealthTracking';
import FeedRecommendation from './pages/FeedRecommendation';
import Notifications from './pages/Notifications';
import Profile from './pages/Profile';

const Settings = () => <div className="p-4">Settings (Coming Soon)</div>;

const RouteFallback: React.FC<{ title: string }> = ({ title }) => (
  <div className="rounded-xl border border-red-200 bg-red-50 p-8 text-center">
    <h2 className="text-lg font-bold text-red-900">{title} is temporarily unavailable</h2>
    <p className="mt-2 text-sm text-red-700">
      This page hit an unexpected error. Please refresh and try again.
    </p>
  </div>
);

const withRouteBoundary = (title: string, element: React.ReactElement) => (
  <ErrorBoundary fallback={<RouteFallback title={title} />}>{element}</ErrorBoundary>
);

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={withRouteBoundary('Login', <Login />)} />
          <Route path="/register" element={withRouteBoundary('Register', <Register />)} />
          <Route path="/forgot-password" element={withRouteBoundary('Forgot Password', <ForgotPassword />)} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/" element={withRouteBoundary('Dashboard', <Dashboard />)} />
              <Route path="/livestock" element={withRouteBoundary('Livestock', <LivestockList />)} />
              <Route path="/livestock/:id" element={withRouteBoundary('Livestock Detail', <LivestockDetail />)} />
              <Route path="/livestock/edit/:id" element={withRouteBoundary('Edit Livestock', <EditLivestock />)} />
              <Route path="/vaccinations" element={withRouteBoundary('Vaccinations', <VaccinationManagement />)} />
              <Route path="/feed" element={withRouteBoundary('Feed Inventory', <FeedInventoryPage />)} />
              <Route path="/ai-feed" element={withRouteBoundary('AI Feed Recommendations', <FeedRecommendation />)} />
              <Route path="/health" element={withRouteBoundary('Health Tracking', <HealthTracking />)} />
              <Route path="/health-tracking" element={withRouteBoundary('Health Tracking', <HealthTracking />)} />
              <Route path="/notifications" element={withRouteBoundary('Notifications', <Notifications />)} />
              <Route path="/settings" element={withRouteBoundary('Settings', <Settings />)} />
              <Route path="/profile" element={withRouteBoundary('Profile', <Profile />)} />
            </Route>
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
