import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Tractor, 
  Syringe, 
  Wheat, 
  Activity, 
  Bell, 
  User, 
  LogOut,
  Menu,
  X,
  Bot
} from 'lucide-react';
import { signOut } from 'firebase/auth';
import { auth } from '../firebase/config';
import logo from '../assets/logo.svg';

const MainLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await signOut(auth);
      navigate('/login');
    } catch (error) {
      console.error("Logout failed", error);
    }
  };

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Livestock', path: '/livestock', icon: Tractor },
    { name: 'Vaccinations', path: '/vaccinations', icon: Syringe },
    { name: 'Feed Inventory', path: '/feed', icon: Wheat },
    { name: 'AI Feed Recs', path: '/ai-feed', icon: Bot },
    { name: 'Health Tracking', path: '/health', icon: Activity },
    { name: 'Notifications', path: '/notifications', icon: Bell },
  ];

  const bottomNavItems = [
    { name: 'Profile', path: '/profile', icon: User },
  ];

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-20 bg-gray-600 bg-opacity-75 transition-opacity lg:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 lg:translate-x-0 lg:static lg:inset-auto flex flex-col ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex flex-col items-center justify-center pt-10 pb-8 px-4 mb-8 border-b border-gray-200 relative text-center">
          <img 
            src={logo} 
            alt="FarmLite Logo" 
            className="w-32 h-auto object-contain mx-auto mb-4"
            loading="eager"
          />
          <span className="text-4xl font-extrabold tracking-tight leading-tight text-green-900">
            FarmLite
          </span>
          <button 
            className="absolute top-4 right-4 lg:hidden text-gray-500 hover:text-gray-700"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-8 w-8" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <nav className="px-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`group flex items-center px-4 py-4 text-xl font-semibold rounded-md ${
                    isActive 
                      ? 'bg-green-50 text-green-700' 
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className={`mr-4 flex-shrink-0 h-7 w-7 ${isActive ? 'text-green-600' : 'text-gray-400 group-hover:text-gray-500'}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="space-y-1">
            {bottomNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`group flex items-center px-4 py-4 text-xl font-semibold rounded-md ${
                    isActive 
                      ? 'bg-green-50 text-green-700' 
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className={`mr-4 flex-shrink-0 h-7 w-7 ${isActive ? 'text-green-600' : 'text-gray-400 group-hover:text-gray-500'}`} />
                  {item.name}
                </Link>
              );
            })}
            <button
              onClick={handleLogout}
              className="w-full group flex items-center px-4 py-4 text-xl font-semibold rounded-md text-red-600 hover:bg-red-50"
            >
              <LogOut className="mr-4 flex-shrink-0 h-7 w-7 text-red-500 group-hover:text-red-600" />
              Sign Out
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar for mobile */}
        <div className="lg:hidden flex items-center justify-between bg-white border-b border-gray-200 p-4">
          <div className="flex items-center">
            <img 
              src={logo} 
              alt="FarmLite Logo" 
              className="h-14 w-14 object-contain mr-3" 
            />
            <span className="text-2xl font-bold text-gray-800">FarmLite</span>
          </div>
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            <Menu className="h-6 w-6" />
          </button>
        </div>

        <main className="flex-1 overflow-y-auto focus:outline-none p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
