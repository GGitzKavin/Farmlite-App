import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Layouts
import MainLayout from './layouts/MainLayout';

// Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import Dashboard from './pages/Dashboard';

import LivestockList from './pages/Livestock/LivestockList';
import LivestockDetail from './pages/Livestock/LivestockDetail';
import EditLivestock from './pages/Livestock/EditLivestock';
import VaccinationManagement from './pages/Vaccinations';
import FeedInventoryPage from './pages/FeedInventory';
import HealthTracking from './pages/HealthTracking';
import FeedRecommendation from './pages/FeedRecommendation';

// Placeholder Pages (To be implemented)
const Notifications = () => <div className="p-4">Notifications (Coming Soon)</div>;
const Settings = () => <div className="p-4">Settings (Coming Soon)</div>;
const Profile = () => <div className="p-4">Profile (Coming Soon)</div>;

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/livestock" element={<LivestockList />} />
              <Route path="/livestock/:id" element={<LivestockDetail />} />
              <Route path="/livestock/edit/:id" element={<EditLivestock />} />
              <Route path="/vaccinations" element={<VaccinationManagement />} />
              <Route path="/feed" element={<FeedInventoryPage />} />
              <Route path="/ai-feed" element={<FeedRecommendation />} />
              <Route path="/health" element={<HealthTracking />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/profile" element={<Profile />} />
            </Route>
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
