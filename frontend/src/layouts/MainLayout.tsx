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
    <div className="flex h-dvh min-h-0 w-full overflow-hidden bg-[#fefae0]">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-20 bg-gray-600/75 transition-opacity lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        id="main-navigation"
        className={`farm-sidebar fixed inset-y-0 left-0 z-30 flex h-dvh w-64 shrink-0 flex-col border-r border-[#a85f20] bg-[#bc6c25] transform transition-transform duration-300 lg:static lg:h-screen lg:w-56 lg:translate-x-0 2xl:w-64 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="farm-sidebar__brand relative flex shrink-0 flex-col items-center justify-center border-b border-[#d79552]/60 px-4 py-5 text-center 2xl:py-7">
          <img
            src={logo}
            alt="FarmLite Logo"
            className="farm-sidebar__logo mb-2 h-auto w-24 object-contain 2xl:w-28"
            loading="eager"
          />
          <span className="farm-sidebar__title text-3xl font-extrabold leading-tight tracking-tight text-white 2xl:text-4xl">
            FarmLite
          </span>
          <button
            type="button"
            aria-label="Close navigation"
            className="absolute right-3 top-3 rounded-md p-2 text-[#fefae0] hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="sidebar-scrollbar min-h-0 flex-1 overflow-y-auto overscroll-contain py-3">
          <nav className="px-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`group flex items-center rounded-md px-4 py-2.5 text-base font-semibold ${
                    isActive
                      ? 'bg-[#fefae0] text-[#3f250d]'
                      : 'text-[#fff8dc] hover:bg-[#d79552] hover:text-white'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className={`mr-3 size-[1.375rem] shrink-0 ${isActive ? 'text-[#606c38]' : 'text-[#fff8dc] group-hover:text-white'}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="shrink-0 border-t border-[#d79552]/60 p-3">
          <div className="space-y-1">
            {bottomNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`group flex items-center rounded-md px-4 py-2.5 text-base font-semibold ${
                    isActive
                      ? 'bg-[#fefae0] text-[#3f250d]'
                      : 'text-[#fff8dc] hover:bg-[#d79552] hover:text-white'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className={`mr-3 size-[1.375rem] shrink-0 ${isActive ? 'text-[#606c38]' : 'text-[#fff8dc] group-hover:text-white'}`} />
                  {item.name}
                </Link>
              );
            })}
            <button
              type="button"
              onClick={handleLogout}
              className="group flex w-full items-center rounded-md px-4 py-2.5 text-base font-semibold text-white hover:bg-[#c1121f]"
            >
              <LogOut className="mr-3 size-[1.375rem] shrink-0 text-red-100 group-hover:text-white" />
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Topbar for mobile */}
        <div className="flex shrink-0 items-center justify-between border-b border-[#eadfa9] bg-[#fefae0] p-3 sm:p-4 lg:hidden">
          <div className="flex items-center">
            <img
              src={logo}
              alt="FarmLite Logo"
              className="mr-2 h-10 w-10 object-contain sm:mr-3 sm:h-12 sm:w-12"
            />
            <span className="text-xl font-bold text-gray-800 sm:text-2xl">FarmLite</span>
          </div>
          <button
            type="button"
            aria-label="Open navigation"
            aria-controls="main-navigation"
            aria-expanded={sidebarOpen}
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-2 text-gray-500 hover:text-gray-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#606c38]"
          >
            <Menu className="h-6 w-6" />
          </button>
        </div>

        <main className="farm-main min-w-0 flex-1 overflow-x-hidden overflow-y-auto bg-[#fefae0] p-4 focus:outline-none lg:p-5 xl:p-6 2xl:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
